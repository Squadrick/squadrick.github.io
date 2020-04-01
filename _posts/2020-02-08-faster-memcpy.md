---
layout: post
title: "Going faster than memcpy"
author: "Dheeraj R. Reddy"
categories: journal
tags: [shadesmar, cpp, simd]
---
To make Shadesmar[github.com/squadrick/shadesmar], I used [`perf`](https://perf.wiki.kernel.org/index.php/Main_Page) to 
analyze the time taken by each function. This was the result:
```
  Children      Self  Command        Shared Object        Symbol
+   99.86%     0.00%  raw_benchmark  libc-2.27.so         [.] __libc_start_main
+   99.86%     0.00%  raw_benchmark  [unknown]            [k] 0x4426258d4c544155
+   99.84%     0.02%  raw_benchmark  raw_benchmark        [.] main
+   98.13%    97.12%  raw_benchmark  libc-2.27.so         [.] __memmove_avx_unaligned_erms
+   51.99%     0.00%  raw_benchmark  raw_benchmark        [.] shm::PublisherBin<16u>::publish
+   51.98%     0.01%  raw_benchmark  raw_benchmark        [.] shm::Topic<16u>::write
+   47.73%     0.01%  raw_benchmark  raw_benchmark        [.] shm::SubscriberBase<16u>::spinOnce
+   47.70%     0.00%  raw_benchmark  raw_benchmark        [.] shm::SubscriberBin<16u>::_subscribe
+   47.64%     0.01%  raw_benchmark  raw_benchmark        [.] shm::Topic<16u>::read
```

`__memmove_avx_unaligned_erms` is an implementation of `memcpy` for unaligned memory blocks that uses AVX 
to copy over 32 bytes at a time. Using `memcpy` for the pub-sub (10MB message size) results in a 
throughput of 5.20GB/s and latency of 17.1 ms.

Since 97% of the execution time was spent on `memcpy`, I figured I'd try to find faster a faster alternative 
for the special case of transferring large messages. This way, I can fallback to the default `memcpy` for 
small messages and use a faster alternative for larger messages.

UPDATE: After spending a weekend on writing faster algorithms for memory copying, I would recommended
others to not do the same. To that end, you can use whatever I've implementation [here](dragons.h) with 
a fair warning: Here be Dragons.

---

`REP MOVSB`

`rep` repeats the following string operation a given number of times. `movsb` moves a single byte from 
one pointer to another, and increments the pointers. The logic may seem very basic, since it's 
only a 2-byte instruction compared to the much more complex alternatives. Intel does spend a lot of time 
optimizing the operation resulting in "Enhanced REP MOVSB and STOSB operation (ERMSB)". I found an 
[excellent answer](https://stackoverflow.com/a/43574756/2240521) on Stackoverflow that goes into great 
depth about ERMSB and other memory copying algorithms.

The implementation uses inline assembly, since we can't guarantee that a compiler will generate a `REP MOVSB`:

```c++
static inline void *_rep_movsb(void *d, const void *s, size_t n) {
  asm volatile("rep movsb"
               : "=D"(d), "=S"(s), "=c"(n)
               : "0"(d), "1"(s), "2"(n)
               : "memory");
  return d;
}
```

It performs decently well, but the default `memcpy` implementation is slightly better, almost ~25% faster
when used for pub-sub with 10MB messages. 

---


