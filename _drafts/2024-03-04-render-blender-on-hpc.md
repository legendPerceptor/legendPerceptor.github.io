---
title: How to render Blender project on HPC systems with GPUs
author: yuanjian
date: 2024-03-04 22:57:00 -0500
categories: [Tutorial]
tags: [Blender, HPC, GPU, 3D rendering]
pin: true
---

Install the newest Blender from the [Blender website](https://www.blender.org/download/).

> The old version on the HPC system usually generates an error for your newer project file.
{: .prompt-danger }

```bash
wget https://mirror.clarkson.edu/blender/release/Blender4.0/blender-4.0.2-linux-x64.tar.xz
```

Extract the `.tar.xz` file via the following command.

```bash
tar -xf ./blender-4.0.2-linux-x64.tar.xz
```
