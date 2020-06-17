---
layout: post
title: "Going faster than memcpy"
author: "Dheeraj R Reddy"
categories: journal
tags: [cpp]
---

While profiling [Shadesmar](https://github.com/squadrick/shadesmar) a couple of
weeks ago, I noticed that for large binary unserialized messages (>512kB) most
of the execution time is spent doing copying the message (using `memcpy`)
between process memory to shared memory and back.

I had a few hours to kill last weekend, and I tried to implement a faster way
to do memory copies.

---

### Autopsy of memcpy

Here's the dumb of [`perf`](https://perf.wiki.kernel.org/index.php/Main_Page)
when running pub-sub for messages of sizes between 512kB and 2MB.

```
 Children      Self  Shared Object      Symbol
+  99.86%     0.00%  libc-2.27.so       [.] __libc_start_main
+  99.86%     0.00%  [unknown]          [k] 0x4426258d4c544155
+  99.84%     0.02%  raw_benchmark      [.] main
+  98.13%    97.12%  libc-2.27.so       [.] __memmove_avx_unaligned_erms
+  51.99%     0.00%  raw_benchmark      [.] shm::PublisherBin<16u>::publish
+  51.98%     0.01%  raw_benchmark      [.] shm::Topic<16u>::write
+  47.64%     0.01%  raw_benchmark      [.] shm::Topic<16u>::read
```

`__memmove_avx_unaligned_erms` is an implementation of `memcpy` for unaligned
memory blocks that uses AVX to copy over 32 bytes at a time. Digging into the
`glibc` source code, I found this:

```c
#if IS_IN (libc)
# define VEC_SIZE                32
# define VEC(i)                  ymm##i
# define VMOVNT                  vmovntdq
# define VMOVU                   vmovdqu
# define VMOVA                   vmovdqa
# define SECTION(p)              p##.avx
# define MEMMOVE_SYMBOL(p,s)     p##_avx_##s

# include "memmove-vec-unaligned-erms.S"
#endif
```

Breaking down this function:

`memmove`: `glibc` implements `memcpy` as a `memmove` instead, here's the
relevant source code:

```c
# define SYMBOL_NAME memcpy
# include "ifunc-memmove.h"

libc_ifunc_redirected (__redirect_memcpy, __new_memcpy,
		       IFUNC_SELECTOR ());
```

Here's the difference between the two: With `memcpy`, the destination cannot
overlap the source at all. With `memmove` it can. Initially, I wasn't sure why
it was implemented as `memmove`. The reason for this will become clearer as
the post proceeds.

`erms`: *E*nhanced *R*ep *M*ov*s* is a hardware optimization for a loop that
does a simple copy. In simple pseudo-code, this is what the loop implementation
looks like for copying a single byte at a time (`REP MOVSB`).

```c++
void rep_movsb(void *dest, const void *src, size_t len) {
  const uint8_t* s = (uint8_t*)src;
  uint8_t* d = (uint8_t*)dest;

  while (len--)
    *d++ = *s++;

  return dest;
}
```

Since the loop copies data pointer by pointer, it can handle the case of
overlapping data.

`vec`: For the above loop rather than copying around single bytes, it uses x86
vectorized instructions to copy multiple bytes in a single loop iteration
(technically single instruction). `vmov*` are assembly instructions for AVX
which is the latest instruction set that the CPU on my laptop supports. With
`VEC_SIZE = 32`, it copies 32 bytes at a time.

`unaigned`: This is a generic version of `memmove` that can copy between any
pointer locations irrespective of their alignment. Unaligned pointers increase
complexity for copy loop when using vectorized instructions. The unaligned
starting and ending pointers must be copied separately before hitting the
optimized loop.

`memmove-vec-unaligned-erms.S` holds the actual implementation in assembly. A
few things that the implementation does:

1. It uses `REP MOVS` only if the data is greater than 4kB. For values smaller
than that is uses SSE2 optimization.

2. For handling `unaligned` pointers, it uses the following blocks:
   - 16 to 31: `vmovdqu`
   - 15 to 8: `movq`
   - 7 to 4: `movl`
   - 3 to 2: `movzwl` and `movw`

3. `VMOVNT` defined above is for doing non-temporal(NT) moves. NT instructions
are used when there is an overlap between destination and source since
destination may be in cache when source is loaded. Uses `prefetcht0` to load
data into cache (all levels: t0). In the current iteration, we prefetch the
data for 2 iterations later. The data is copied (via cache) into registers. The
data (via NT) is copied from registers into destination.

```nasm
L(loop_large_forward):
	; Copy 4 * VEC a time forward with non-temporal stores.
	PREFETCH_ONE_SET (1, (%rsi), PREFETCHED_LOAD_SIZE * 2)
	PREFETCH_ONE_SET (1, (%rsi), PREFETCHED_LOAD_SIZE * 3)
  ; PREFETCH 256b from rsi+256 to rsi+511

	VMOVU	(%rsi), %VEC(0)
	VMOVU	VEC_SIZE(%rsi), %VEC(1)
	VMOVU	(VEC_SIZE * 2)(%rsi), %VEC(2)
	VMOVU	(VEC_SIZE * 3)(%rsi), %VEC(3)
  ; mov 128b from rsi to rsi+127 -> 4 ymm registers (cahce)
  ; 2 loops later, we hit the prefetched values

	addq	$PREFETCHED_LOAD_SIZE, %rsi  ; advance to rsi+128 in next loop
	subq	$PREFETCHED_LOAD_SIZE, %rdx

	VMOVNT	%VEC(0), (%rdi)
	VMOVNT	%VEC(1), VEC_SIZE(%rdi)
	VMOVNT	%VEC(2), (VEC_SIZE * 2)(%rdi)
	VMOVNT	%VEC(3), (VEC_SIZE * 3)(%rdi)
  ; mov 128b from 4 ymm register -> rdi to rdi+127 (no cache)

	addq	$PREFETCHED_LOAD_SIZE, %rdi  ; advance to rdi+128 in next loop
	cmpq	$PREFETCHED_LOAD_SIZE, %rdx
	ja	L(loop_large_forward)
```

---

### Method 1: Basic REP MOVSB

Before getting into more exotic implementation, I wanted to first implement a
super simple version of ERSB to see how well it would perform. I used inline
assembly to write out the loop.

```c++
void _rep_movsb(void *d, const void *s, size_t n) {
  asm volatile("rep movsb"
               : "=D"(d), "=S"(s), "=c"(n)
               : "0"(d), "1"(s), "2"(n)
               : "memory");
}
```

This does the same as the pseudo-code attached above, but I wrote it in
assembly to prevent any compiler optimization, and rely only on the hardware
ERMS optimization.

### Alternate 2: Aligned AVX

One of the complexities in `glibc`'s  implementation is getting it to work for
unaligned pointers. Since I control the memory allocation, I figured I could
recreate the implementation focused solely on aligned pointer and sizes. I'm
using AVX intrinsics for 32-byte vectors (AVX):

```c++
void _avx_cpy(void *d, const void *s, size_t n) {
  // d, s -> 32 byte aligned
  // n -> multiple of 32
  auto *dVec = reinterpret_cast<__m256i *>(d);
  const auto *sVec = reinterpret_cast<const __m256i *>(s);
  size_t nVec = n / sizeof(__m256i);
  for (; nVec > 0; nVec--, sVec++, dVec++) {
    const __m256i temp = _mm256_load_si256(sVec);
    _mm256_store_si256(dVec, temp);
  }
}
```

The logic is identical to the previous `REP MOVSB` loop instead operating on 32
bytes at a time.

### Method 3: Stream aligned AVX

`_mm256_load_si256` and `_mm256_store_si256` go through the cache, which incurs
additional overhead. AVX instruction set has `_stream_` load and store
instructions that skip the cache. The performance of this copy is dependant
on:
1. Quantity of data to copy
2. Cache size

Non-temporal moves may bog down the performance for smaller copies (that can
fit into L2 cache) compared to regular moves.

```c++
void _avx_async_cpy(void *d, const void *s, size_t n) {
  // d, s -> 32 byte aligned
  // n -> multiple of 32
  auto *dVec = reinterpret_cast<__m256i *>(d);
  const auto *sVec = reinterpret_cast<const __m256i *>(s);
  size_t nVec = n / sizeof(__m256i);
  for (; nVec > 0; nVec--, sVec++, dVec++) {
    const __m256i temp = _mm256_stream_load_si256(sVec);
    _mm256_stream_si256(dVec, temp);
  }
  _mm_sfence();
}
```

Exact code as before but using non-temporal moves instead. There's an extra
`_mm_sfence` which guarantees that all stores in the preceding loop are 
visible globally.

### Method 4: Stream aligned AVX with prefetch

In the previous method, we skipped the cache entirely. We can squeeze a bit
more performance by prefetching the source data into the cache for the next
iteration in the current iteration. Since all prefetches work on cache-lines
(64-bytes), each loop iteration copies 64-bytes from source to data.


```c++
void _avx_async_pf_cpy(void *d, const void *s, size_t n) {
  // d, s -> 64 byte aligned
  // n -> multiple of 64

  auto *dVec = reinterpret_cast<__m256i *>(d);
  const auto *sVec = reinterpret_cast<const __m256i *>(s);
  size_t nVec = n / sizeof(__m256i);
  for (; nVec > 2; nVec -= 2, sVec += 2, dVec += 2) {
    // prefetch the next iteration's data
    // by default _mm_prefetch moves the entire cache-lint (64b)
    _mm_prefetch(sVec + 2, _MM_HINT_T0);

    _mm256_stream_si256(dVec, _mm256_load_si256(sVec));
    _mm256_stream_si256(dVec + 1, _mm256_load_si256(sVec + 1));
  }
  _mm256_stream_si256(dVec, _mm256_load_si256(sVec));
  _mm256_stream_si256(dVec + 1, _mm256_load_si256(sVec + 1));
  _mm_sfence();
}
```

The load from source pointer to register should **not** skip the cache since
that data is explicitly prefetched into the cache, non-stream
`_mm256_load_si256` must be used instead.

This also unrolls the loop for 2 copies at a time instead of a single copy.
This is to guarantee that each loop iteration's prefetch coincides the copy.
Prefetch the next 64-bytes and copy the current 64-bytes.

---

## Alternate avenues

### Unrolling

In the previous section, most of the changes were in the actual underlying
load, store instructions used. Another avenue of exploration is to unroll the
loop for a certain number of iterations. This reduces the number of branch
statements by the factor of unrolling.

In the `glibc` implementation the unrolling factor is 4 which is what I'll use
as well. A very simple way to implement this is to increase the alignment 
required by 4x and treat each loop as 4 instructions that copy 4x data.

A more complicated version would be trying to implement an unrolled loop
without increasing alignment size. We'll need to copy using a regular fully
rolled loop till we hit a pointer location that is aligned to the size expected
by our unrolled loop.

Unrolling the aligned AVX copy:

```c++
void _avx_cpy_unroll(void *d, const void *s, size_t n) {
  // d, s -> 128 byte aligned
  // n -> multiple of 128

  auto *dVec = reinterpret_cast<__m256i *>(d);
  const auto *sVec = reinterpret_cast<const __m256i *>(s);
  size_t nVec = n / sizeof(__m256i);
  for (; nVec > 0; nVec -= 4, sVec += 4, dVec += 4) {
    _mm256_store_si256(dVec, _mm256_load_si256(sVec));
    _mm256_store_si256(dVec + 1, _mm256_load_si256(sVec + 1));
    _mm256_store_si256(dVec + 2, _mm256_load_si256(sVec + 2));
    _mm256_store_si256(dVec + 3, _mm256_load_si256(sVec + 3));
  }
}
```

### Multithreading

The operation of copying data is super easy to parallelize across multiple
threads. The total data to be transferred can be segmented into (almost)
equal chunks, and then copied over using one of the above methods. This will
make the copy super-fast especially if the CPU has a large core count.

---

## Shadesmar API

To make it easy to integrate custom memory copying logic into the library,
I introduced the concept of `Copier` in [this commit](https://github.com/Squadrick/shadesmar/commit/22dc762ca658d1396f3c00366e80e4f695189df9).
For a new copying algorithm, an abstract class `Copier` must be implemented.

Here's the definition of `Copier`:

```c++
class Copier {
 public:
  virtual void *alloc(size_t) = 0;
  virtual void dealloc(void *) = 0;
  virtual void shm_to_user(void *, void *, size_t) = 0;
  virtual void user_to_shm(void *, void *, size_t) = 0;
};
```

The original reason for introducing this construct was to allow cross-device
usage, where a custom copier would be implemented to tranfer between CPU and
GPU. E.g.: using `cudaMemcpy` for Nvidia GPUs.

For a single device use case the implementation of `shm_to_user` and 
`user_to_shm` are identical. The implementation of a copier that uses
`std::memcpy`:

```c++
class DefaultCopier : public Copier {
 public:
  void *alloc(size_t size) override { return malloc(size); }

  void dealloc(void *ptr) override { free(ptr); }

  void shm_to_user(void *dst, void *src, size_t size) override {
    std::memcpy(dst, src, size);
  }

  void user_to_shm(void *dst, void *src, size_t size) override {
    std::memcpy(dst, src, size);
  }
};
```

I also created an adapter `MTCopier` that adds multithreading support to other
copiers:

```c++
template <class BaseCopierT> 
class MTCopier : public Copier {
public:
  explicit MTCopier(uint32_t threads = std::thread::hardware_concurrency())
      : base_copier(base_copier), nthreads(threads) {}

  void *alloc(size_t size) override { return base_copier.alloc(size); }

  void dealloc(void *ptr) override { base_copier.dealloc(ptr); }

  void _copy(void *d, void *s, size_t n, bool shm_to_user) {
    std::vector<std::thread> threads;
    threads.reserve(nthreads);

    ldiv_t per_worker = div((int64_t)n, nthreads);

    size_t next_start = 0;
    for (uint32_t thread_idx = 0; thread_idx < nthreads; ++thread_idx) {
      const size_t curr_start = next_start;
      next_start += per_worker.quot;
      if (thread_idx < per_worker.rem) {
        ++next_start;
      }
      uint8_t *d_thread = reinterpret_cast<uint8_t *>(d) + curr_start;
      uint8_t *s_thread = reinterpret_cast<uint8_t *>(s) + curr_start;

      if (shm_to_user) {
        threads.emplace_back(&Copier::shm_to_user, &base_copier, d_thread,
                             s_thread, next_start - curr_start);
      } else {
        threads.emplace_back(&Copier::user_to_shm, &base_copier, d_thread,
                             s_thread, next_start - curr_start);
      }
    }
    for (auto &thread : threads) {
      thread.join();
    }
    threads.clear();
  }

  void shm_to_user(void *dst, void *src, size_t size) override {
    _copy(dst, src, size, true);
  }

  void user_to_shm(void *dst, void *src, size_t size) override {
    _copy(dst, src, size, false);
  }

private:
  BaseCopierT base_copier;
  uint32_t nthreads;
};
```

Currently this only works for `memcpy` and `_rep_movsb` since the
implementation expects the memory copy to work for unaligned memory.

---

## Benchmark

I used Google's [Benchmark](https://github.com/google/benchmark) for timing
the performance of copying data ranging from size of 32kB to 64MB. All the
benchmarks were run on my PC with the following specifications:
1. AMD Ryzen 7 3700X
2. 2x8GB DDR4 RAM @ 3600Mhz

{% include graphs/memcpy.html %}

### Conclusion

Stick to `std::memcpy`. It delivers great performance while also adapting to
the hardware architecture, and makes no assumptions about the memory alignment.

If performance truly matters, then you might want to consider using a more
specific non-genetic implementation with alignment requirements. The streaming
prefetching copy works the best for larger copies (>1MB), but the performance
for small sizes is abyssal, but `memcpy` matches its performance. For small to
medium sizes Unrolled AVX absolutely dominates, but as for larger messages, it
is slower than the streaming alternatives. The regular `RepMovsb` is by far the
worst overall performer as excepted.

Unrolling definitely improves performance in most cases by about 5-10%. The
only case where the unrolled version is slower than rolled version is for
`AvxCopier` with data size of 32B, which the unrolled version is 25% slower.
The rolled version will do a single AVX-256 load/store and a conditional check.
The unrolled version will do 4 AVX-256 load/stores and a conditional check.

### Code

Code for all the methods is included in the library conforming to the above
mentioned API. To actively warn about the danger of using these custom copiers
I have named this file [`dragons.h`](https://github.com/Squadrick/shadesmar/blob/master/include/shadesmar/memory/dragons.h),
with an apt message: *Here be dragons*.
