---
layout: post
title: "Tricks of the Trade"
author: "Dheeraj R Reddy"
categories: journal
tags: [programming]
---

I've worked on a wide range of software projects: ML stuff, databases, search engines, rendering engines, web servers. Most of which involved writing code that was performant. Over that time, I've learnt a bunch of tricks from one domain that I think can be applied broadly, and this blog will capture some of them.

---

### First construct, then optimize

Construct the data-structure first in an inefficient way, but that's easy to reason about and optimize. If you're building a tree, just use pointers for the node connectivity. Once the data-structure is fully built, convert to a much more optimized structure using knowledge about:
1. The distribution of data in the structure
2. The read/access pattern
For example, if the number of nodes in a tree is known and the accesses will be primarily breath-first, balance the tree and then convert the inefficient-tree-with-pointers to a dense BFS array with index offsets for connecting edges. Then discard the inefficient tree structure. The dense structure is gonna be balanced, smaller and faster, with better memory locality. 

The down-side is that the optimized, dense representation cannot be updated. So this is only applicable for data-structures that are read-heavy and infrequently updated. To add new data:
1. Convert the dense structure back to the inefficient structure, add the data, then reconvert back to dense, OR
2. Generate the inefficient structure from scratch (considering the raw data is stored elsewhere) with the additional data, reconvert back to dense. 

*Example*: A k-d tree for approximate kNN search over vector space representing some embedded text: some version of this can be used for powering RAG in LLMs. The dataset to search over is likely to be updated every fortnight, but the reads are gonna be far more frequent: ~1k QPS[^1].

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

[This article](https://www.rfleury.com/p/untangling-lifetimes-the-arena-allocator) gives a lot deeper into the topic.

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

[^1]: Pulled this out of my ass. Just go with it. 
