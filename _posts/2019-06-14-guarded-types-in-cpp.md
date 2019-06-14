---
layout: post
title: "Guarded Types in C++"
author: "Dheeraj R. Reddy"
categories: journal
tags: [cpp]
---

I was working with C++ to build a replacement for [Costmap ROS](http://wiki.ros.org/costmap_2d) to use in a driverless car, since Costmap ROS is targeted towards smaller autonomous bots. To this end, the current plan is to make it work in real time, and include some more functionality (like bayesian updates).

In my implementation, the costmap is split into two parts: `Costmap`, which handles the inter-process communication using ROS, and wraps `MapGrid` which is the low-level grid that does most of the heavy lifting. The division of these two layers to so that we can port `Costmap` from using ROS to ROS2, once the latter is more stable.

In this post I'll be outlining a little feature I implemented to make my life easier while building `MapGrid`.

Let me outline the problem first. I'm using a structure to keep track of the bounds, where each map is a rectangle, like this:

```c++
struct Bounds {
  uint16_t x1, x2;
  uint16_t y1, y2;
};
```

Each `MapGrid` is composed of smaller `MapArea`s each having their own `bounds`, and `MapGrid` has it's own all emcompassing `bounds`. Something like this:

```c++
class MapArea {
  ...
  Bounds area_bounds;
  ...
};

class MapGrid {
  ...
  std::vector <MapArea> map_areas;
  Bounds map_bounds;
  ...
};
```

During computation, I do a bunch of operations between objects of `Bounds` and their cooridinates, and this is where the problem arises. After every operation I need to manually check to make sure there's no underflow or overflow, and this gets annoying pretty fast. Initially I was writing functions to manually check for under or overflow and handle the case accordingly, and my life was pretty great. But...

During this time, I was also reading about [Cap'n Protocol](https://capnproto.org/) which is a serialization protocol that's ~infinitely~ faster than Protobuf for encoding and decoding a message in memory. It's pretty neat, you should definitely check it out. They had a problem with integer overflows which they discuss [here](https://capnproto.org/news/2015-03-02-security-advisory-and-integer-overflow-protection.html). They solve this by defining their own `Guarded` type that does compile time checks for overflow.

After reading the blogpost, I decided to implement my own `Guarded` type for use in `Bounds`. Let's get started.

---

### The Crux

Base type definition:

```c++
template <typename T, T max, T min>
class Guarded {
  T value;
}
```
where `max` and `min` are the upper and lower bounds of my type. We can modify it to have default template parameters are the maximum and minimum of type `T` respectively by modifying the template to be:

```c++
template <typename T,
          T max = std::numeric_limits<T>::max(),
          T min = std::numeric_limits<T>::min()>
```

Thankfully both `numeric_limits<T>::max()` and `numeric_limits<T>::min()` are `constexpr`s. The most important thing is that we need to be able to check for valid data during compile time. We can either use `if constexpr`, or the easier `static_assert`:

```c++
template <typename T,
          T max = std::numeric_limits<T>::max(),
          T min = std::numeric_limits<T>::min()>
class Guarded {
  static_assert(max <= std::numeric_limits<T>::max(),
      "possible overflow detected");

  static_assert(min >= std::numeric_limits<T>::min(),
      "possible underflow detected");

  static_assert(max >= min, "incorrect bounds");

  T value;
}
```

After the `static_assert`:

```c++
Guarded<int, 10, 5> a; // no error
Guarded<char, 5, 10> b; // compilation error: incorrect bounds
```

We can then add some constructors for initializing the data:

```c++
template <typename T, T max = std::numeric_limits<T>::max(),
          T min = std::numeric_limits<T>::min()>
class Guarded {
  static_assert(max <= std::numeric_limits<T>::max(),
                "possible overflow detected");

  static_assert(min >= std::numeric_limits<T>::min(),
                "possible underflow detected");

  static_assert(max >= min, "incorrect bounds");

public:
  inline constexpr Guarded() : value((max + min) / 2) {}

  inline constexpr Guarded(T val) : value(val) { /* Unsafe */
  }

  template <typename otherT, otherT otherMax, otherT otherMin>
  inline constexpr Guarded(const Guarded<otherT, otherMax, otherMin>
      &other) : value(other.value) {
    static_assert(otherMax <= max, "possible overflow detected");
    static_assert(otherMin >= min, "possible underflow detected");
  }
  T value;
};
```

Right now, you must be noticing that the only way to assign something to `value` is through the unsafe constructor. We can make a utility function (similar to `make_shared`) to create a `Guarded` value.

```c++
template <typename T, T val> inline constexpr Guarded<T, val, val>
guard() {
  return Guarded<T, val, val>(val);
}
```

One thing to note is that the `max` and `min` values of the `Guarded` value is equal to `val`. This makes it strictly bound.

Now we have everything needed for a working example to show you the use of `Guarded`.

```c++
Guarded<int, 25> a = guard<int, 10>();
Guarded<int, 9, 1> b = a; // compilation failure: overflow detected
Guarded<int, 100, 0> c = a; // works

std::cout << a.value << std::endl; // prints 10
```

We can get compile time errors because all of the code is evaluated at run-time by the compiler since we've used `constexpr` and `static_assert`. C++ is weirdly great because of this thing called Metatemplate Programming that allows for Turing complete computations at compile time.

Being able to just do guarded assignments is pretty useless for anything more than a blog post, so let's tackle addition of two `Guarded` types using operator overloading.

```c++
template <typename otherT, otherT otherMax, otherT otherMin>
inline constexpr Guarded<decltype(T() + otherT()), std::max(max, otherMax),
                         std::min(min, otherMin)>
operator+(const Guarded<otherT, otherMax, otherMin> other) const {
  return Guarded<decltype(T() + otherT()), std::max(max, otherMax),
                 std::min(min, otherMin)>(value + other.value);
}
```

`decltype` is used to deduce the type from `T` and `otherT`. The important thing to note is how we handle the new upper and lower guard bounds. In this example use case, we've set `newMax = max(max, otherMax)` and `minMin = min(min, otherMin)`. The value of these bounds for addition can be changed to best suite ones needs; the only requirements being that it's a `constexpr` that evaluates at compile time. To show you how exactly the bounds work:

```c++
Guarded<int, 10, 1> a = guard<int, 3>();
Guarded<int, 15, 10> b = guard<int, 11>();
auto c = a + b;
// c.value = 3
// c.max = max(10, 15) = 15
// c.min = min(1, 10) = 10
```

There's one glaring problem here, consider:
```c++
Guarded<int, 2, 1> a = guard<int, 2>();
Guarded<int, 2, 1> b = guard<int, 2>();

auto c = a + b;
// c.value = 4
// c.max = 2
// c.min = 1
```

The above code won't throw any compile time warnings. This culprit here is

```c++
return Guarded<decltype(T() + otherT()), std::max(max, otherMax),
    std::min(min, otherMin)>(value + other.value);
```

I'm calling the "unsafe" constructor that doesn't check for any bounds, which causes the problem. But we had compile time checking for assignments using `guard()`. Let's use that here:

```c++
return Guarded<decltype(T() + otherT()), std::max(max, otherMax),
    std::min(min, otherMin)>(
      guard<decltype(T() + otherT()), value+other.value>());
```

This looks like it works, but it doesn't. This is because `value+other.value` can't be a `constexpr`, and therefore this can't be evaluated compile, and we get a compilation error. (If someone figures out a workaround for this, please let me know.)

Instead we're stuck using the unsafe constructor without compile time bounds checking. If the need arises, we could do a run time check or clip in the constructor. Or we could modify how we assign `newMax` and `minMin` to never worry about this situation. Or do what I do:

```c++
Guarded <int, 10, 5> a = guard<int, 6>();
Guarded <int, 15, -5> b = guard<int, 7>();

Guarded <int, 25, -25> c = a + b; // compiles
Guarded <int, 10, 0> d = a + b; // compile error: overflow detected
```

Handling other operations like subtraction, multiplication, division would be roughly similar. Finally using this with `Bounds`:

```c++
struct Bounds {
	Guarded<uint16_t, 1000, 0> x1;
	Guarded<uint16_t, 1000, 0> x2;
	Guarded<uint16_t, 1000, 0> y1;
	Guarded<uint16_t, 1000, 0> y2;
};
```

This ensures that the result of any of any computation relating to `Bounds` won't be outside the map area. This is beneficial because we might get a segfault if we try to access memory outside map area. To show a proper example:

```c++
const uint16_t MAX_MAP_DIM = 1000;

// Without guarded
uint8_t* __map = malloc(sizeof(uint8_t) * MAX_MAP_DIM * MAX_MAP_DIM);

// Consider Bounds b1, b2
uint16_t newX = b1.x1 + b2.x1;
uint16_t newY = b1.y2 + b2.y2;

// check_under_over_flow(newX, MAX_MAP_DIM, 0);
// check_under_over_flow(newY, MAX_MAP_DIM, 0);

__map[newX * MAX_MAP_DIM + newY] = 0; // might throw segfault if it overflows
```

In the code snippet `check_under_over_flow` ensures that we don't access unsafe memory, but calling it after every check makes it tedious. With the new `Guarded` type:

```c++
Guarded<uint16_t, MAX_MAP_DIM> newX = b1.x1 + b2.x1;
Guarded<uint16_t, MAX_MAP_DIM> newY = b1.x1 + b2.x1;

__map[newX.value * MAX_MAP_DIM + newY.value] = 0;
// will never throw a segfault
```

In my application, I can't really make use compile time checks all that much, I've modified `Guarded` to include a lot more runtime checks and calculations since most of the information is unknown at compile time and depends on the sensor readings during runtime.

Is this the perfect solution? No. There's a lot of things I didn't account for, and there's probably better ways to do it, I'm no C++ expert, but I found it useful for my case and maybe you might too.

---

If you have any criticisms of this blog post, please [email me](mailto:dheeraj98reddy@gmail.com) and let me know. I'm still learning and anything to help me out is something I look forward to.

Links to things I've found enjoyable over the last few weeks:
* [The Valleyfolk](https://www.youtube.com/channel/UCkEXXbo1QOTesV8h2hkN-1g), RIP Sourcefed.
* [Reply All](https://gimletmedia.com/shows/reply-all)
* [Jesus Christ or Russell Brand](https://github.com/scottleechua/jesus-russell)
* [Bearcels](https://www.reddit.com/r/bearcels)
* [TensorFlow Addons](https://github.com/tensorflow/addons)
