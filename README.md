Milovision: a camera pose estimation programme
==============================================

A full description and discussion of Milovision is available
[here](http://wintermute.eu/report.pdf).

What
----

Milovision is, first, a pose estimation pipeline. It turns images of a
known circular marker into estimates of the camera's position and rotation
relative to that marker. 

The project also includes an OpenGL based simulator. The simulator serves to
facilitate the validation and performance evaluation of the the pose
estimation pipeline.

Why
---

While many pose estimation systems do exist, most are either not freely
available under an MIT-style (permissive) license, or lack some of the
advantages of circular marker based systems - such as their resilience to
occlusion.

How to use
----------

Refer to the *Implementation* chapter of the
[report](http://wintermute.eu/report.pdf) for a short user manual.

For the impatient: edit, make executable, and run the convenience script,
`run`, or type `python main.py -h`.
