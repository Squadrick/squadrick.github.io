---
layout: page
title: Feed
---

_Things I want to remember_   $$ \cap $$   _Things I don't mind the internet knowing_

---

### 21st November 2021, 07:00 PM

Code blasphemy: If you can't fix a CI test, [disable it](https://github.com/Squadrick/shadesmar/commit/023c512a6fd9ad641e9075f7f8eaf3e09189c3fc).

---

### 23rd July 2021, 12:30 AM

I hadn't worked on [Shadesmar](https://github.com/Squadrick/shadesmar) for nearly a year. I was
looking at the code as reference for a tricky race condition at work. Not to brag, but the
code was pretty neat, so I decided revist the project and I've been working on it over the last couple of weeks.

I stumbled into a very tricky bug, and spent a good couple of hours debugging it. It was
a wonderful experience. I once read somewhere that a nice bug is like intellectual comfort
food, and this bug qualified handily. [Here's the fix](https://github.com/Squadrick/shadesmar/commit/25be585ced4c7dcd4b8a4faf8a592c9a37227ff3)
along with a very nice commit message.

---

### 30th May 2021, 06:50 PM

Milestone in SummaryDB: [It works!](https://github.com/Squadrick/summarydb/commit/932ffefb2853785048a27d4fc308353b528cfe8d)

---

### 22nd May 2021, 02:43 AM

I took an off from work today with the hope of enjoying a nice birthday
weekend. I spent the day listening to Neil Gaiman's The Sandman on Audible,
and hacking on [SummaryDB](https://github.com/squadrick/summarydb/) and I
just hit 100 commits. I thought it was worthy of
[a tweet](https://twitter.com/DheerajRajaram/status/1395849916484767744).

---

### 25th April 2021, 04:44PM

[Feynman's Nobel Ambition](https://www.asc.ohio-state.edu/kilcup.1/262/feynman.html?repostindays=413).

---

### 18th April 2021, 12:45 AM

Large software engineering systems are shockingly broken compared to systems
from other engineering disciplines. Other disciplines have a strong constraint
of having to adhere to physics, while infinite layers upon layers of
abstraction allows software to be really divorced from a strong
foundational tether. [It usually ends up being the sprawlings of diseased
minds.](https://xkcd.com/1513/)

---

### 3rd February 2021, 12:15 AM

Instead of using reference counts to keep track of liveness of a 
pointer, instead use a dynamic graph to track all reference pointing.

Referce counting wouldn't work too well when there's cycles in the
pointer:

```
A --> B --> C --> A
```

This usually requires a workaround using weak pointers that
don't increase the reference count.

Using a reference graph instead would fix this problem, by
denoting liveness as an edge to an eternal `sentinel`
node. Every time a node is deleted (pointer is deallocated),
we delete it's edge to `sentinel` and retrieve the list
of nodes no longer connected to `sentinel`.

Implementing the underlying dynamic graph to make it fast
while being thread-safe would be a challenge. Some looking
around leads to [this paper](https://arxiv.org/pdf/1809.00896.pdf)
which would be perfect.

---

### 1st January *2021*, 03:25 AM

It is end of 2020. It was a catastrophic year for the global community.
On a personal front, it was a year of massive changes; a solid 6.5/10.

Some of the positive highlights of my year:
1. Education.
2. Profession.
3. Family.

Some of the negative highlights:
1. Death.
2. Friendships.
3. Time.

I've never been one for resolutions, but I was looking forward to 2020.
To quote Pirate Wires,
> Big swings only.

With that hope ending in a fiery pile of pandemic shit, I tried to make
the best of the hand that was dealt. I like to think that all the
negative highlights from above were exogenous, but in highsight I
could've handled them better, with a bit less haze.

The zeitgeist is that the end of 2020 will also annul us from the
problems of 2020, while concurrently recognizing that 2021 will be
a bleak, unchanging continuation. This juxtaposition reflects my personal
outlook, but I side more with the former. I'm not hoping for big swings,
but some _Mediocre Swings_ would be scenic.

Covid didn't just leave it's mark on humanity, it french kissed it.
I'm a witness to its gross, sloppy pervasiveness. I have spent my New Year's
Eve quarantined in a room waiting for my RT-PCR test, with the gregarious
company of the dull hum of my PC's fan, some bright lit screens, a bottle of
red wine, and an uncomfortable sense of dreadly anticipation.

**Update:** I have tested negative. One more to the list of positive highlights.

Happy new year. Death to Covid. Long live enlightenment.

---

### 4th December 2020, 10:18 PM

The best advice I can give anyone is to never buy a snow-white keyboard.
If you do, you'll spend two hours each month cleaning each key-cap
only for it to be grimy within the week.

---

### 28th November 2020, 03:35 AM

I was coding something in C++ and required sum types, and reached for the
evergreen `std::variant` and life was great. Until I realized C++ doesn't
have type-based pattern matching (_à la_ [Go's Type Switch](https://tour.golang.org/methods/16)),
but after a little digging I discovered `std::visit`.

What should've been a simple piece of code ending up being monstrous
boilerplate, so I figured I was doing something wrong. A quick google
search for `std::visit usage` landed me in [this](https://bitbashing.io/std-visit.html)
blog aptly titled:

> std::visit is everything wrong with modern C++

I strongly agree with the author. It is ridicously complex, and the
addition of `make_visitor` as part of the standard would've been great.
To be perfectly fair, I really don't understand their implementation
that uses recursive overload. For now, I'm going with the `constexpr if`
solution.

I have half a mind to just roll my own `union` and `enum` based sum type.
But experience has taught me that rolling my own alternative to a thing
that exists in the C++ standard is good way to burn coding time.

This aversion to writing code from scratch, and reusing clunky existing
solutions is a sign that I'm on the road to become a Software Developer™.

---

### 24th October 2020, 02:50 AM

I have such a tough time wrapping my head around the whole Kubernetes, Docker,
Docker-compose jargon. It requires prerequisite knowledge that is unfamiliar to
me. It makes me wish I spent a bit more time doing backend web-dev during my
undergrad.

---

### 5th October 2020, 10:30 PM

It's a Monday, and I'm already mentally and physically drained. This week is
going to be rough.

---

### 21st September 2020, 01:05 AM

Previously, my resume was a built using Latex, and I had a PDF in the
GitHub repo. This had three problems:
- Making changes were difficult. I had to update the `tex` source, generate
the PDF and update the file in the repo.
- The git history was bloated by having to track the different versions of
the binary PDF file.
- It wasn't a native webpage, so it didn't adapt to the device.

Since this website is built using Jekyll, I can generate the resume while
the site is being deployed. The data is stored in a YAML file along with
some code to generate the appropriate HTML webpage.

You can check it out [here](https://squadrick.dev/resume). One issue is that
it uses more pages (2 vs. 1), but that's a trade off I'm willing to make.

---

### 2nd September 2020, 11:50PM

Fall Guys is fun. I think the last time I found a game this
enjoyable with friends was RuneScape in 2010.

RIP AzzuTheBoss.

---

### 28th August 2020, 6:10 PM 

I've recently started working with Java during my day job, and I was
reminded of a quote from [a blog](https://blog.pawandubey.com/dependency-injection-a-twenty-five-dollar-term/)
I read _long_ ago:

> “Dependency Injection” is a 25-dollar term for a 5-cent concept. – James Shore

I think Java programmers made up a bunch of jargon to make
their jobs feel cooler than it really is. Java
seems to favour verbosity over cleverness; perhaps, an averse
reaction to the preceeding era of C++'s cleverness (read: pain).

*Update, 1st September:* Honestly shocking that Java didn't get
an equivalent of C++'s `auto` till Java 10. This is especially
annoying when using for-each loops.

---

### 17th August 2020, 1:35 AM

I've really fucked up my sleep cycle. I'm currently alternating between
10AM - 5PM or 3PM - 10PM depending on the day. The past week has been
a random sequence of working, coding, watching YouTube, and trying to
live my life in-between. The lack of a proper schedule is a clean 3/10.
Would not recommend.

---

### 29th July 2020, 11:50 PM

Picturing slice/concat/reshape operations on high-dim arrays gives me the
same feelings as ASMR for some weird reason.

Here's one I was just thinking about:

```
[4, 5, 3] -> SLICE@0, 4 * [1, 5, 3] -> concat@2 -> [1, 5, 12]
```
is not the same as
```
[4, 5, 3] -> RESHAPE(1, 5, 12)
```

To put it into words: Slicing + concat along different dimensions can't be
replaced by a single reshape, unless the slicing + concat operate on subsequent
dimensions. So that means:

```
[4, 5, 3] -> SLICE@0, 4 * [1, 5, 3] -> concat@1 -> [1, 20, 3]
```
is the same as
```
[4, 5, 3] -> RESHAPE(1, 20, 3)
```

*Update, 17th August:* If the dimension of slicing is after the concat dimension,
the output of the fused slice will need to be tranposed along the concat/slice
dimensions and then concatenated.

---

### 24th July 2020, 01:20 AM

Although C++ is a powerful language, it's quite easy to write ugly code.
An example of the contrary is [Glow](https://github.com/pytorch/glow).
The [graph optimizer code](https://github.com/pytorch/glow/blob/master/lib/Optimizer/GraphOptimizer/GraphOptimizer.cpp)
is a joy to read. Going to use this as an example of steller C++ code.

---

### 3rd July 2020, 2:16 AM

Graphs are amazingly useful structures. Wanted something that could generate
a single C++ header file given my project's `include` and `src` folders.

Went around looking at pre-existing tools, but they either were not compatible
with my build system (good ol' `CMake`) or too complex to set up.
[`quom`](https://github.com/Viatorus/quom) looks promising as a general
purpose tool.

Wrote my own `shadesmar`-specific single header generator. It's called
[`simul`](https://github.com/Squadrick/shadesmar/tree/master/simul).
The core logic is embarrassing simple:
1. Parse all the header files to find all its includes and its source file.
2. Build a DAG of include dependencies.
3. Repeatedly paste the header file and source file in topological order.

But as usual, the string handling (which is most of the code) was annoying.
There's a little bit more code to deal with file-specific include guard
removal.

---

### 1st July 2020, 7:20 AM

I recently got a new PC. To play games I installed Windows. I hate Windows.
Read [a blog post](https://tonsky.me/blog/disenchantment/) that encapsulates why I
hate it. This is similar to another [video](https://www.youtube.com/watch?v=ZSRHeXYDLko)
by Jonathon Blow. That's not to say Windows is the only thing guilty of this, there's
plenty of inefficient, janky softwares I use of a regular basis.

After playing games like Red Dead Redemption 2 over the last couple of days, I'm
gobsmacked by people who write game engines. They are far less guilty of
the above.

I'm going to try [Proton](https://github.com/ValveSoftware/Proton) now, and try
to get started with some basic game engine work.

---

### 25th June 2020, 04:45 AM

I accidentally deleted 6 hours of uncommitted work:

```
~/W/shadesmar> rm -rf *
zsh: sure you want to delete all 21 files in /home/squadrick/Workspace/shadesmar [yn]? y
```

I thought I was in `build` deleting compiled targets. Time to retype from memory.
