---
layout: post
title: "Multiprocessed Gym Environments"
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

This isn't perfect either, because I haven't created a an `action_space` or `observation_space` field that other Gym environments have. But the above `MultiEnv` should be good enough.

Let's create an instance of this class, which encapsulated 10 `Breakout-v0` Gym environments.
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
