#!/usr/bin/env python
#
# Milovision: A camera pose estimation programme
# 
# Copyright (C) 2013 Joris Stork
# See LICENSE.txt
#
# pose_generator.py
""" 
:synopsis:  Contains the Pose Generator (sub)classes, which generates marker
            poses within the visibility contraints of the given camera. These
            poses are used to position the marker in successive simulated
            images.

.. moduleauthor:: Joris Stork <joris@wintermute.eu>

"""

# standard library and third party packages
import logging
import copy
import cv2
import numpy as np
import time
import math
import sys

# milovision modules
from marker import GL_Marker


class Pose_Generator(object):

    def __init__(self, output = None):
        """ 
        Sets parameters that define visibility contraints, amongst other
        attributes. Initialises the marker.
        
        """
        
        self.output = output
        fovx = self.output.cam.get_ratio() * self.output.cam.fovy
        # todo: check why fovx value apparently too big (aspect wrong?)
        self.tanx = math.tan(math.radians(fovx) / 2.05) 
        self.tany = math.tan(math.radians(self.output.cam.fovy) / 2.)
        self.init_marker = GL_Marker(config_id = 0, cam = self.output.cam)
        self.init_marker.set_min_dist()
        self.maxangle = np.pi / 2. # 90 degrees
        

class Linear_Pose_Generator(Pose_Generator):
    """ generates linear patterns of marker poses """

    def __init__(self, output = None):
        """ sets counter, number of lines, and bounds for marker locations """

        Pose_Generator.__init__(self, output = output)
        self.n = 0
        self.nmax = 30 # for linear generator; use a multiple of 5
        self.zmax = 50. # (50 ~= 18m @ mindist=360) factor of mindist
        self.linstage = self.nmax / 5


    def generate(self):
        """ 
        Cuts the total number of required poses into 'linstage' series, each a
        straight line within the chosen bounds and visibility contraints

        """

        xsign = 1.
        ysign = 1.
        if self.n < self.linstage:
            pass
        elif self.n < 2 * self.linstage:
            ysign = -1
        elif self.n < 3 * self.linstage:
            xsign = -1
            ysign = -1
        elif self.n < 4 * self.linstage:
            xsign = -1
        elif self.n < 5 * self.linstage:
            xsign = 0.
            ysign = 0.
        else:
            return None

        mfh = self.init_marker.config.simul_frame_height
        init_z = self.init_marker.config.C[2]
        n = self.n % (self.nmax / 5)
        zstep = self.zmax / (self.nmax / 5)
        z = (n * zstep * init_z) + init_z
        x = xsign * -(z - init_z) * self.tanx
        y = ysign * -(z - init_z) * self.tany
        marker = copy.deepcopy(self.init_marker)
        marker.config.C = np.array([x, y, z])

        self.n += 1
        return marker


class Random_Pose_Generator(Pose_Generator):
    """
    Generates random poses, including random orientation, within the given
    visibility contraints.
    
    """

    def __init__(self, output = None):
        """ sets range of depths allowed """

        Pose_Generator.__init__(self, output = output)
        self.tzrange = -10000 / self.output.cam.unitsize
        self.tzrange -= self.init_marker.config.C[2]


    def get_angle(self, a, b):
        """ returns the angle between vectors a and b """

        return np.arccos(np.dot(a/np.linalg.norm(a),b/np.linalg.norm(b)))


    def get_rotation(self, angle, axis):
        """ 
        Returns a rotation matrix corresponding to the given angle and axis 
        
        """

        if axis == 'x':
            return np.array([
                [1.0, 0.0, 0.0],
                [0.0, np.cos(angle), -np.sin(angle)],
                [0.0, np.sin(angle), np.cos(angle)]
                ])
        elif axis == 'y':
            return np.array([
                [np.cos(angle), 0.0, np.sin(angle)],
                [0.0, 1.0, 0.0],
                [-np.sin(angle), 0.0, np.cos(angle)]
                ])
        elif axis == 'z':
            return np.array([
                [np.cos(angle), -np.sin(angle), 0.0],
                [np.sin(angle), np.cos(angle), 0.0],
                [0.0, 0.0, 1.0]
                ])
        else:
            self.logger.error('invalid axis for rotation')
            sys.exit(1)
            

    def rotate(self, a, r):
        """ 
        Applies a succession of rotations, each around one axis and stored in
        order in the array r, to a point. The result is a 3D rotation of the
        point.

        """

        result = np.copy(a)
        for rotation in r:
            result = np.dot(rotation, result)
        return result


    def generate(self):
        """ 
        Applies an arbitrary 3D rotation and translation to the points in
        corners_3d, within a visibility constraint.

        Visibility constraint: first, translation must be within camera field of
        view (fov); second, rotation must not map to a marker that is too
        edge-on or that is facing away.

        Variables:
            tzlim/txlim/tylim: marker translation limits to remain in camera fov
            tx/ty/tz: marker translation
            z: z-axis unit vector
            mn: marker normal
            mc: marker centre
            vis_threshold: maximum angle(mn, z) where marker visible (72deg)
            r: array of three rotation matrices (x, y, z)
        
        """

        tz = self.init_marker.config.C[2] + np.random.uniform() * self.tzrange 

        txrange = -(tz - self.init_marker.config.C[2]) * self.tanx
        tx = 2. * np.random.uniform() * txrange - txrange

        tyrange = -(tz - self.init_marker.config.C[2]) * self.tany
        ty = 2. * np.random.uniform() * tyrange - tyrange

        t = np.array([tx, ty, tz])
        marker = copy.deepcopy(self.init_marker)
        marker.config.C = copy.deepcopy(t)

        a = self.get_angle(marker.config.C, -marker.config.N)

        r = None
        while (not r) or (a > (self.maxangle)):
            r = []
            for axis in ['x', 'y', 'z']:
                angle = np.random.uniform() * 2.0 * np.pi
                r.append(self.get_rotation(angle, axis))
                N = copy.deepcopy(self.init_marker.config.N)
            marker.config.N = self.rotate(N, r)
            a = self.get_angle(marker.config.C, -marker.config.N)

        for i, vertex in enumerate(marker.vertices):
            marker.vertices[i] = self.rotate(vertex, r)
        return marker
