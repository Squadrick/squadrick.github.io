---
layout: post
title: "When to stop working on side-projects"
author: "Dheeraj R Reddy"
categories: journal
tags: [banter]
---

I'm a professional coder, and so like all good coders™, I spend a non-trivial
number of hours working each week on side-projects. The projects' range is
pretty wide, from low-level RPC stuff to machine learning and rendering
engines. Right now, I'm working on several projects that might never see the
light-of-day. The most significant among them (and the only one that has been
open-sourced) is [Shadesmar](https://github.com/squadrick/shadesmar).

It was also the first project I started hoping that it wouldn't be another repo
collecting dust on my GitHub that only I use, and I put down on my résumé.
No, this would be useful to the broader community.

When I first started working on it, close to a year back, I had an clear idea
of when I should stop working on Shadesmar, or when I would consider Shadesmar
to be a completed project. The v1.0 release. Since then, I've maintained a list
(spread across GitHub issues and mental lists) of the functionality I should
build next:
- Shared memory only
- Handle deadlocks due to dead processes
- Multi-threaded pubsub
- RPCs
- Custom allocators
- ...

The point is that there isn't a real end to this list. Every time I got closer
to the v1.0 release, it slipped further away. Sometimes I realized what I
previously built won't be useful to the users, or there's a "better"[^nit] way
to do it. I've set-up CI to ensure there are no errors and benchmarks to
prevent any performance regressions. I've even set-up a pipeline to convert all
the code into a single header file[^single-header] to make it easier for users
to integrate into existing projects.

But the truth is that there are no users. At the time of writing this article,
it has 85 stars and 7 forks on GitHub, and a good chunk of those are from my
friends who follow me and star every repo I have. There are a few external
starrers, but I'm sure no one actually tried using the project because the
project had been in a non-functioning state for nearly 3 months. I got a grand
total of 0 issues complaining about this. This is what prompted me to set-up
CI.

Now I'm not salty or disheartened that people aren't using my library built for
a very small use-case. I started this as an alternate to ROS's XMLRPC based
communication protocol, which was a cause for a lot of headaches. But when ROS2
was released a couple months later and using DDS as the communication layer,
the need for Shadesmar was basically dead. But I figured, "Hey, people may
still want to do pubsub/RPC across processes, and some of these people want to
do it without using the network stack, and an even smaller subset *really* care
about performance, and need it in C++1x, and don't wanna use tried and tested
UNIX pipes, and they appreciate a reference to Brandon Sanderson's novels." I
realized the set of people needing Shadesmar is relatively minuscule. Hell,
I'm part of that set, and even I haven't used Shadesmar in any other project, I
resort to using UNIX pipes instead. But I continued building it anyway.

The reality was that I really enjoyed working on it. It taught me a great deal
about low-level systems engineering and operating systems. I faced challenges
that required me to come up with non-trivial solutions. I fixed really
complicated bugs. It led me to find other fields of CS that I now have an
active interest in[^game-dev]. I found [other people](https://github.com/alephzero/alephzero)
interested in solving the same problems, and frankly did a better job than me.

A skill that my friends, [Ajeet](https://github.com/ajeetdsouza) and 
[Sarthak](https://github.com/naiveHobo) have and that I admire, is to work on
[side](https://github.com/naiveHobo/InvoiceNet)-[projects](https://github.com/ajeetdsouza/zoxide)
that are both challenging and useful to other people. Definitely a skill I
should learn.

The point of this blog is more catharsis than generic advice. The evergrowing
features list has stopped. I have made issues for all pending work, and beyond
that, I'll stop working on Shadesmar. That will be its v1.0 release.
I think it'll take a few months of working on the weekends to finish it.
Hopefully, by that point, I can figure out someplace I can actually use it.

---

TL;DR Here's when I'm going to stop working on any side-project:
1. I don't have a use for it
2. I don't find it enjoyable

---

[^nit]: Higher throughput, lower latency, or better APIs, etc.

[^single-header]: I know that single-headers are not the best way to distribute libraries. But Shadesmar is small enough (~1500 LoCs) that compile speeds shouldn't be an issue.

[^game-dev]: I had to build a custom memory allocator. Most of the solutions for custom local memory allocators were predominantly in game engine development.
