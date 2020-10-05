---
layout: page
title: Feed
---

A running list in the intersection of things I want to remember and
things I don't mind the internet knowing about me.

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
