---
layout: post
title: "(Better) Interprocess Locks"
author: "Dheeraj R. Reddy"
categories: journal
tags: [cpp, ipc, shadesmar]
---

This is a follow-up to my previous post on 
[Interprocess Locks](https://squadrick.github.io/journal/ipc-locks.html), 
where an alternate approach was to use a `ptread_mutex` with attributes 
`PTHREAD_PROCESS_SHARED` and `PTHREAD_MUTEX_ROBUST`. After working on other
parts of [Shadesmar](https://github.com/Squadrick/shadesmar) over the last
few weeks, I decided to implement the alternative lock.

Before going into the implementation details, I'd like to point out the 
problems with the previous implementation:

1. As pointed by [wahern on HN](https://news.ycombinator.com/item?id=21402988)
   - PIDs are recycled. Although the problem would arise very rarely, it 
   is still possible that process which died while holding the lock could
   have its PID recycled, preventing our recovery mechanism from working
   as expected.

2. The recovery mechanism is quite expensive, and makes the lock an order of
   magnitude slower compared to a non-robust lock.

3. The need of a lockless set brings in quite a bit of complexity.

It worked well enough in our tests, but I'd like something better. 

---

#### Implementation

The requirement is a reader-writer lock (`rwlock`) since it'll be used 
to protect a multi-reader, multi-writer queue. The algorithm for building 
a `rwlock` using a simple mutex is quite easy and can be found on 
[Wikipedia](https://en.wikipedia.org/wiki/Readers%E2%80%93writer_lock). 
It requires two simple mutexes and a counter. We define a function 
`consistency_handler()` to recover in the case of a dead process. 

```c++
class IPC_Lock {
public:
  IPC_Lock();
  ~IPC_Lock();

  void lock();
  void unlock();
  void lock_sharable();
  void unlock_sharable();

private:
  void consistency_handler(pthread_mutex_t *mutex, int result);
  pthread_mutex_t r, g;
  pthread_mutexattr_t attr;
  std::atomic<uint32_t> counter;
};
```

For ensuring that `IPC_Lock` can be used between different processes by
being placed in shared memory, we use `pthread_mutexattr_setpshared` 
with `PTHREAD_PROCESS_SHARED`.

To ensure robustness, we use `pthread_mutexattr_setrobust` with 
`PTHREAD_MUTEX_ROBUST`. If a process dies while doing this mutex, the 
process that acquires the mutex succeeds, and it returns `EOWNERDEAD`. 
The new owner must call `pthread_mutex_consistent()` to ensure correct
working hence forth. 

```c++
IPC_Lock::IPC_Lock() {
  pthread_mutexattr_init(&attr);
  pthread_mutexattr_setpshared(&attr, PTHREAD_PROCESS_SHARED);
  pthread_mutexattr_setrobust(&attr, PTHREAD_MUTEX_ROBUST);

  pthread_mutex_init(&r, &attr);
  pthread_mutex_init(&g, &attr);
}

IPC_Lock::~IPC_Lock() {
  pthread_mutexattr_destroy(&attr);
  pthread_mutex_destroy(&r);
  pthread_mutex_destroy(&g);
}

void IPC_Lock::lock() {
  int res = pthread_mutex_lock(&g);
  consistency_handler(&g, res);
}

void IPC_Lock::unlock() { pthread_mutex_unlock(&g); }

void IPC_Lock::lock_sharable() {
  int res_r = pthread_mutex_lock(&r);
  consistency_handler(&r, res_r);
  counter.fetch_add(1);
  if (counter == 1) {
    int res_g = pthread_mutex_lock(&g);
    consistency_handler(&g, res_g);
  }
  pthread_mutex_unlock(&r);
}

void IPC_Lock::unlock_sharable() {
  int res_r = pthread_mutex_lock(&r);
  consistency_handler(&r, res_r);
  counter.fetch_sub(1);
  if (counter == 0) {
    pthread_mutex_unlock(&g);
  }
  pthread_mutex_unlock(&r);
}

void IPC_Lock::consistency_handler(pthread_mutex_t *mutex, int result) {
  if (result == EOWNERDEAD) {
    pthread_mutex_consistent(mutex);
  } else if (result == ENOTRECOVERABLE) {
    pthread_mutex_destroy(mutex);
    pthread_mutex_init(mutex, &attr);
  }
}
```

I'm not dwelling into the code as much as the previous post since the 
code is faily simple and straight forward.

#### Performance 

The speed of `IPC_Lock` with and without the shared and robust mechanism: 
`PTHREAD_PROCESS_SHARED`, `PTHREAD_MUTEX_ROBUST` and `consistency_handler`
is very similar. Doing simple tests of repeated lock/unlock doesn't really 
show much of a different. I'll update this section after a more thorough
benchmark.

#### Problems

I'm hoping to add more OS support for Shadesmar. The implementation of 
`pthread` in OSX doesn't support `pthread_mutexattr_setrobust`, 
`pthread_mutexattr_setrobust` and `pthread_mutex_consistent`. So, I'm 
currently using the old IPC lock on OSX until I can find a better alternative. 

---

The pull request for the new lock can be found 
[here](https://github.com/Squadrick/shadesmar/pull/7).
