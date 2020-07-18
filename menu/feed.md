---
layout: page
title: Feed
---

A running list in the intersection of things I want to remember and
things I don't mind the internet knowing about me.

---

### 15th July 2020, 10:15 AM

I'm done with my degree! Just wrapped up my final presentation for my 8th
semester internship. I start working full-time from ~~16th~~ 17th July at
ThoughtSpot.

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
