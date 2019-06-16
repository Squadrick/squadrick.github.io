---
layout: post
title: "Day-to-day log of building a driverless car"
author: "Dheeraj R. Reddy"
categories: journal
tags: [robotics]
---

This will be a day to day log of me trying to build a driverless car. I'll make the code fully open source once it's completed, and I'm doing this for my university's [robotics team](projectmanas.in). 
The purpose of this is to serve as documentation for myself, and my colleagues. I'll try to explain concepts as breifly as possible, but you're probably better of looking for other sources if you're objective is to learn how to do it yourself.

The car we'll be using is the [Mahindra e20](https://www.mahindraelectric.com/vehicles/e2oPlus/).

---

#### 17th June 2019

Start the blog.

The first thing to work on would be the simulation environment. I'm torn between using [Gazebo](http://gazebosim.org/), [AirSim](https://github.com/microsoft/AirSim) or [Carla](http://carla.org/). 
I'll need to do some research and weigh the pros and cons before taking the plunge. We've already some a little work on Gazebo. We've made the urdf for the car and made the simulation environment, 
so if I opt for something else, I'll need to write a tool to convert from urdf to whatever config AirSim or Carla uses.

