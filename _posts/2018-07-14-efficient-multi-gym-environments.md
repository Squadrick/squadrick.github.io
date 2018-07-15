---
layout: post
title: "Efficient Multiple Gym Environments"
author: "Dheeraj R. Reddy"
categories: journal
tags: [distributed computing]
---

In Reinforcement learning, most of the training time is spent in collecting experience from your environments(real life robots, simulators), and very little time is spent on the actual learning part on the GPU. So if we want fast RL training, we need to build fast environments.

Due to its ubiquitous usage in RL and easy-to-use API, I'll be sticking to using [OpenAI Gym.](https://gym.openai.com/)

Before going off and using multiprocessing to optimize the performance, let's benchmark a single Gym environment.

```python
import gym
env = gym.make('Breakout-v0')
```

There's a couple of ways to find the time taken for execution, but I'll be using Python's `timeit` package.

```python
import timeit

start = timeit.default_timer()
# CODE HERE
end = timeit.default_timer()

print("Time taken:", (end-start),"seconds")
```

First, I'll be checking how long it takes to reset an environment before the start of each new episode.

```python
env.reset()
```
I took an average of 1000 runs, and it's around 0.0092775 seconds per reset. Next I'll test to see the time taken to take a random action in the environment using `step`

```python
observation, reward, done, info = env.step(env.action_space.sample())
if done:
    env.reset()
```

I took an average of 1000 runs, and it's around 0.00056156 seconds per action. In frames per seconds, that's around 1.78 million new observations every second. That's pretty fast. Faster than any GPU you can use to train the RL algorithm.

<sub>(Note: I've reported numbers for only `Breakout-v0`, but it shouldn't be too different for other Atari games)</sub>

Now, in RL, we don't just train on data from a single instance of the simulator, even if the simulator is sufficiently fast enough.
1. 	We want the experience that the RL algorithm learns on to be as diverse as possible. So each sampled mini-batch will be from a separate simulator. This breaks the long term temporal dependency, allowing the algorithm to rely solely on the input data.
2.  Sometimes, we might vary each instance of the simulator slightly to prevent the algorithm from fitting to one specific dynamics model. So if we're training an RL algorithm to control a robotics arm with some parameters $$\theta$$ describing the dynamics of the model, maybe the length of each arm. Training the algorithm simultaneously from another set of simulators with parameters $$\theta_1, \theta_2, ..$$ allows the algorithm to be robust to the dynamics model.
3. 	In [this paper](https://arxiv.org/pdf/1804.03720.pdf) by OpenAI, they showed that simultaneously training of a varied set of environments, make the algorithm much better at transfer learning.

Let's see how to get multiple instances of the same environment up and running.

```python
class MultiEnv:
    def __init__(self, env_id, num_env):
        self.envs = []
        for _ in range(num_env):
            self.envs.append(gym.make(env_id))

    def reset(self):
        for env in self.envs:
	        env.reset()

    def step(self, actions):
        obs = []
        rewards = []
        dones = []
        infos = []

        for env, ac in zip(self.envs, actions):
            ob, rew, done, info = env.step(ac)
            obs.append(ob)
            rewards.append(rew)
            dones.append(done)
            infos.append(info)

            if done:
                env.reset()
	
        return obs, rewards, dones, infos
```

This isn't perfect either, because I haven't created `action_space` and `observation_space` fields that other Gym environments have. But the above `MultiEnv` should be good enough for timing the performance.

Let's create an instance of this class, which encapsulates 10 `Breakout-v0` Gym environments.
```python
multi_env = MultiEnv('Breakout-v0', 10)
```

Let's measure the time taken for `reset` and `step` like before. I took an average of 1000 runs like before.

It takes 0.102515 seconds per reset, and 0.0061777 seconds per step. As you can see that's around 10x the time taken by a single environment, and a little bit more time for iterating through `env` in `self.envs`, but it's negligible.

To see how this option scales with the number of environment look at the plot below.

![num-env-plot](https://i.imgur.com/CXFctLG.png "No. of envs vs. time taken")

As the number of environments increases, so does the time taken. The blue line is the expected linear growth, what we expect to hit. However, due to added time taken by iterating over all the environments, we get the orange line.

It's pretty evident why our current `MultiEnv` takes slightly more than linear time. The execution of any operation such as `step` or `reset` is sequential. 

This would be suitable where the number of environments is fairly less, or when each environment is very light, like CartPole or Pendulum. But we often deal with cases where we simultaneously train on a large number of simulators, or the simulators tend to be computationally heavy like Gazebo or AirSim.

Our task now is to build a multi-environment system that gets below the blue linear line. We'll acheive this by using a parallel concurrent system as opposed to this sequential system.

There's a few ways to acheive concurrent behaviour in Python:
1. Multithreading
2. Multiprocessing
3. MPI

We can immediately disregard one of the above options -- Multithreading. This is because of Python's GIL.

Global interpreter lock (GIL) is a mutex used by CPython, that allows a process to use only one thread at a time. This prevents us from taking advantage of multicore processors. [Here](https://opensource.com/article/17/4/grok-gil) is an excellent article about Python's GIL and how exactly it works.

### Multiprocessing

Let's build a gym environment that uses Python's Multiprocessing module.

This is a wrapper class that can be used to treat multiple Gym environments through a single object.

```python
class SubprocVecEnv():
	def __init__(self, env_fns):
		self.waiting = False
		self.closed = False
		no_of_envs = len(env_fns)
		self.remotes, self.work_remotes = \
			zip(*[Pipe() for _ in range(no_of_envs)])
		self.ps = []
		
		for wrk, rem, fn in zip(self.work_remotes, self.remotes, env_fns):
			proc = Process(target = worker, 
				args = (wrk, rem, CloudpickleWrapper(fn)))
			self.ps.append(proc)

		for p in self.ps:
			p.daemon = True
			p.start()

		for remote in self.work_remotes:
			remote.close()
```

A few things I've used above haven't been defined yet like `worker` and `CloudpickleWrapper`, let's do that now

```python
import pickle
import cloudpickle

class CloudpickleWrapper(object):
	def __init__(self, x):
		self.x = x

	def __getstate__(self):
		return cloudpickle.dumps(self.x)

	def __setstate__(self, ob):
		self.x = pickle.loads(ob)
	
	def __call__(self):
		return self.x()
```

I'm using an external library called [cloudpickle](https://github.com/cloudpipe/cloudpickle), which gives us extended pickle support particularly useful for transporting objects between processes running the same version of Python.

Now we need to define the `target` that each `Process` will use. A `worker` can be thought as the behaviour of each `Process`.

```python
def worker(remote, parent_remote, env_fn):
	parent_remote.close()
	env = env_fn()
	while True:
		cmd, data = remote.recv()
		
		if cmd == 'step':
			ob, reward, done, info = env.step(data)
			if done:
				ob = env.reset()
			remote.send((ob, reward, done, info))

		elif cmd == 'render':
			remote.send(env.render())

		elif cmd == 'close':
			remote.close()
			break

		else:
			raise NotImplentedError
```

Let's finish our implementation of `SubprocVecEnv` be defining the basic Gym environment functions.
```python
import numpy as np

class SubprocVecEnv():
	def __init__(self):
		# See above
	
	def step_async(self, actions):
		if self.waiting:
			raise AlreadySteppingError
		self.waiting = True

		for remote, action in zip(self.remotes, actions):
			remote.send(('step', action))
	
	def step_wait(self):
		if not self.waiting:
			raise NotSteppingError
		self.waiting = False

		results = [remote.recv() for remote in self.remotes]
		obs, rews, dones, infos = zip(*results)
		return np.stack(obs), np.stack(rews), np.stack(dones), info
	
	def step(self, actions):
		self.step_async(actions)
		return self.step_wait()
	
	def reset(self):
		for remote in self.remotes:
			remote.send(('reset', None))

		return np.stack([remote.recv() for remote in self.remotes])
	
	def close(self):
		if self.closed:
			return
		if self.waiting:
			for remote in self.remotes:
				remote.recv()
		for remote in self.remotes:
			remote.send(('close', None))
		for p in self.ps:
			p.join()
		self.closed = True
```

We're finally done, and we're ready to run some more experiments. Let's make a simple helper function for launching multiprocessor Gym environments:

```python
def make_mp_envs(env_id, num_env, seed, start_idx = 0):
	def make_env(rank):
		def fn():
			env = gym.make(env_id)
			env.seed(seed + rank)
			return env
		return fn
	return SubprocVecEnv([make_env(i + start_idx) for i in range(num_env)])
```

Let's plot the time taken for `step` by a single Gym environment as compared to our multiprocessor Gym wrapper.

![multi-proc](https://i.imgur.com/0flmiPD.png "Multiprocessor comparision")

(Note: The single Gym environment here appears to be slower than before since the two experiments were run on different computer, I'll make a proper definite benchmark at a later time. Sorry!)

Clearly it's faster, but it still scales sub-linearly with the number of environment, whereas one would expect no growth atleast early on, at least as far as the number of environments is equal to the number of cores. To understand the reason for the slowdown, let's take a look at `step_async` and `step_wait`.

```python
def step_async(self, actions):
	if self.waiting:
		raise AlreadySteppingError
	self.waiting = True

	for remote, action in zip(self.remotes, actions):
		remote.send(('step', action))
```

In the above method, we send a `step` command to each of our processes along with the action, but we don't wait for a response, and we set `waiting = True`

```python
def step_wait(self):
	if not self.waiting:
		raise NotSteppingError
	self.waiting = False

	results = [remote.recv() for remote in self.remotes]
	obs, rews, dones, infos = zip(*results)
	return np.stack(obs), np.stack(rews), np.stack(dones), info
```

In the `step_wait` method, we now need to synchronize every process, collect all the responses and return it. The problem is that the sync step is expensive. Since the speed of all the other processes is bogged down by the slowest process. As an extreme example, consider 10 processes where the first 9 execute a `step` on its own Gym instance in 1 second, and the 10th process takes 100 seconds to complete the same action.

In this line `results = [remote.recv() for remote in self.remote]`, we need to wait for `remote.recv()` of the 10th process for 100 seconds, even though all the previous processes were much faster.

Although in reality, the time taken by each process is comparable, we stil need to wait for the slowest process each time. This synchronization step causes the increase in time with increase in environment.

So if each individual environment's `step` is very light and fast, it's better to use the seqeuntial wrapper. But if each environment is heavy, it's better to use the concurrent wrapper.

You could also mix both of them together. We launch a number of processes, where each process executes sequentially on a number of environments. This is particularly useful for Environments that are not too heavy or too light such as Atari. But finding the right number of processes vs. number of sequential environments takes some tinkering to find what works best of your hardware.

Implementing this would be super easy in my code. Just modify `make_env` function in `make_mp_envs`. Instead of `env = gym.make(env_id)` use `env = MultiEnv(env_id, num_seq)`. Each `observation` and `action` will now be a matrix of size `[num_proc, num_seq]` which you can flatten out and treat as a vector.

### MPI

Using multiprocessing for parallel gym environments was a definite improvement, however it's useful only for a single PC with multiple cores. For large scale training using clusters of PCs, we'll need to look a little further.

Python's multiprocessing can spawn multi processes but they will still be bound with a single node.

What we will need is a framework that handles spawning of processes across multiple nodes and provides a mechanism for communication between the processors. Pretty much what MPI does.

MPI is not the only tool that can be used for this. Other popular choices are pp, jug, pyro and celery although I can't vouch for any since I have no experience with any of them. 
