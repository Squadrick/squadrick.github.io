---
layout: post
title: "Tricks of the Trade"
author: "Dheeraj R Reddy"
categories: journal
tags: [programming]
---

I've worked on a wide range of software projects: ML stuff, databases, search engines, rendering engines, web servers. Most of which involved writing code that was performant. I've learnt a bunch of tricks from each domain that I think can be applied broadly, and this blog explains some of them.

---

### First construct, then optimize

Construct the data-structure first in an inefficient way, but that's easy to reason about and optimize.  Once the data-structure is fully built, convert to a much more optimized structure using knowledge about:
1. The distribution of data in the structure.
2. The read/access pattern.

The usual down-side is that the optimized representation cannot be updated easily. So this is only applicable for data-structures that are read-heavy and infrequently updated. To add new data:
1. Convert the dense structure back to the inefficient structure, add the data, then reconvert back to dense, OR
2. Generate the inefficient structure from scratch (considering the raw data is stored elsewhere) with the additional data, reconvert back to dense. 

*Example*: A k-d tree for approximate kNN search in high-dim vector space: some version of this can be used for similarily text search. The dataset to search over is likely to be updated every fortnight, but the reads are gonna be far more frequent: ~1k QPS. The unoptimized k-d tree data-structure uses pointers for node-connectivity, with simple straight forward construction. Once constructured, balance the tree (spilling is a common optimization) and convert it to a dense DFS array with index offsets for connecting nodes. Then discard the unoptimized data-structure. The dense k-d tree is gonna be more balanced, smaller and faster, with better memory locality.

Check out the [compact BVH implementation from PBRT](https://pbr-book.org/3ed-2018/Primitives_and_Intersection_Acceleration/Bounding_Volume_Hierarchies#CompactBVHForTraversal) for a more in-depth explanation.

---
### Local memory allocators

This goes hand-in-hand with the above trick. `malloc` and `free` are not cheap, and calling them frequently can tank performance. The exact impact varies by the memory allocator being used, but it is non-trivial overhead.

Avoid this overhead by allocating a buffer of memory at the start, let the application code deal with the management, and at the end the entire buffer can be deallocated. 

This has more benefits:
1. Better performance due to fewer calls to `malloc`/`free`, and the local memory allocator can be designed specifically for the use case.
2. Better memory utilization due to lower fragmentation.
3. Easier to detect and catch memory leaks.

This is typically used when there's a clear start/end point for processing like a frame in a video game or a request lifetime. A local allocator is created at the start, with bump allocation (increment a pointer for allocation) throughout and then finally reset the buffer at the end (reset pointer).

[This article](https://www.rfleury.com/p/untangling-lifetimes-the-arena-allocator) dives a lot deeper into the topic.

---
### Use the calling thread

A common pattern when needing to do some parallel work is:
 ```c++
thread_pool pool(N_THREADS);

void computeHeavyFunc(const Arg&);

void parallelFunc(const vector<Arg>& inputs) {
	for (const auto& input: inputs) {
		pool.add([&]{ computeHeavyFunc(input); });
	}
	pool.wait();
}
```
This works fine, but what if `inputs` has only a single element? There's quite a bit of redundant work being done with the lambda being scheduled onto the thread pool and the calling thread having to wait for the result. A better way would've been for the calling thread itself to just call `func` directly. Here's the generic way to do that:
```c++
void parallelFunc(const vector<Arg>& inputs) {
	for (int i = 0; i < inputs.size() - 1; ++i) {
		// First N-1 inputs are scheduled on the thread-pool
		pool.add([&]{ computeHeavyFunc(inputs[i]); });
	}
	// Call the last element in inputs directly.
	computeHeavyFunc(inputs.back());
	// Wait after the call.
	pool.wait(); 
}
```
Here, if `inputs.size() == 1`, the loop is completely skipped and `func` is called directly and `pool.wait()` is a no-op. When `inputs.size() > 1`, all the work is distributed across `inputs.size() - 1` threads (one less than in the previous case), and the calling thread is actually doing some work rather than just waiting for the thread pool.

I've not really found this technique being called anything but I refer to it as "thread inlining". If you've seen this before, send me an email about it.

---
### Read-copy-update 

To explain RCU, let me introduce an example problem of flag management. A service has a global configuration of flags, which is periodically updated. Every read path must be protected, since an update could change the underlying data:

```c++
std::shared_mutex mu;
Flags* gFlags;

void algo() {
  mu.lock_shared();
  AlgorithmConfig algoConfig = gFlags->algoConfig;
  mu.unlock_shared();
  execute(algoConfig);
}

void updateFlags() {
  // Read + copy
  Flags* oldFlags;
  Flags* newFlags = getFlagsFromRemoteServer();
  mu.lock();
  // Update
  oldFlags = gFlags;
  gFlags = newFlags;
  mu.unlock();
  delete oldFlags;
}
```

Doing this in a safe, fast manner is crucial. The above example of a shared mutex is slow and doesn't scale with the readers. The readers have to `lock_shared` and `lock_unshared` every iteration, even if the overwheling majority of time there is no update. An alternative would be to wrap `gFlags` in `std::shared_ptr`, but that has almost the same overhead as using a lock to protect it due to ref-counting.

Removing the locks entirely:

```c++
std::atomic<Flags*> gFlags;

void algo() {
  Flags* flags = gFlags.load();
  AlgorithmConfig algoConfig = flags->algoConfig;
  execute(algoConfig);
}

void updateFlags() {
  Flags* newFlags = getFlagsFromRemoteServer();
  gFlags.store(newFlags);
  // Can't delete the older flag state, since we don't know
  // when the readers will be done with using it. The solution
  // is to leak it.
}
```
This is a faster implementation, but one that is not safe as it leaks the older data.

RCU is a synchronization primitive that allows this:
```c++
std::atomic<Flags*> gFlags;

void algo() {
  {
    // The critical section.
    rcu_read_lock();
    Flags* flags = gFlags.load();
    AlgorithmConfig algoConfig = flags->algoConfig;
    rcu_read_unlock();
  }
  execute(algoConfig);
}

void updateFlags() {
  Flags* oldFlags = gFlags.load();
  Flags* newFlags = getFlagsFromRemoteServer();
  gFlags.store(newFlags);
  rcu_synchronize();
  delete oldFlags;
}
```

`read_read_{lock,unlock}` is super fast (sometimes a no-op depending on the implementation), so it is perfect for our use case. This allows for minimal overhead in the much more often read path, while still ensuring the safety when calling the solemn write path.

[Folly's implementation of RCU](https://github.com/facebook/folly/blob/main/folly/synchronization/Rcu.h) is a great read to understand both the usage and the implementation of RCU. 
