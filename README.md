Milovision: a camera pose estimation programme
==============================================

A full description and discussion of Milovision is available
[here](http://www.science.uva.nl/onderwijs/thesis/centraal/files/f755157801.pdf).

Collaborators are more than welcome: just contact the
[author](http://nl.linkedin.com/in/joris1).


What
----

Milovision is, first, a pose estimation pipeline. It turns images of a
known circular marker into estimates of the camera's position and rotation
relative to that marker. 

This project includes an OpenGL based simulator that generates images of markers
in the virtual camera's field of view. The simulator serves to validate the
model, and to evaluate and improve the performance of the pose estimation
pipeline.

Why
---

While many visual marker based pose estimation systems do exist, the motivation
for this project arose from the lack of freely available implementations based
on circular markers. Circular marker based methods offer some distinct
advantages for the purpose of pose estimation by comparison with those that rely
on square markers, not least due to their ability to accurately detect partially
occluded ellipses.

How to use
----------

Refer to the *Implementation* chapter of the
[report](http://www.science.uva.nl/onderwijs/thesis/centraal/files/f755157801.pdf) for a short user manual.

For the impatient: edit, make executable, and run the convenience script,
`run`, or type `python main.py -h`.
