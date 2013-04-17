#!/usr/bin/env python
#
# Milovision: A camera pose estimation programme
# 
# Copyright (C) 2013 Joris Stork
# See LICENSE.txt
#
# camera_modules.py
""" 
:synopsis:  contains the Camera class, which holds the camera-related
            parameters for the OpenGL based simulation.

.. moduleauthor:: Joris Stork <joris@wintermute.eu>

"""

import math
import numpy as np
import sys


# todo: define transparent attribute retrieval functions
class Camera_Vals(object):
    """ camera object (parent class for simulated camera) """

    def __init__(self, camera_id = None):
        """ 
        Sets default values for a real camera. Only supports square pixels.
        
        """

        if camera_id == 'chameleon1':
            self.ipw, self.iph = 1280, 960
            self.pixelsize = 0.00375
            self.unitsize = 1.                  # mm
            self.intrinsic = np.load('calibration/intrinsic.npy')
            self.focal = - (fx + fy) / 2.
            self.fovy = 32.5855                 # degrees
            self.fovx = 42.5828                 # degrees


    def get_focal(self):
        """ returns the camera's focal length """

        fx = self.pixelsize * self.intrinsic[0,0]
        fy = self.pixelsize * self.intrinsic[1,1]
        return - (fx + fy) / 2.


    def get_focal_mm(self):
        """ 
        Returns the camera focal length in mm. If the camera is real, the stored
        focal length is returned. Otherwise the focal length is calculated.
        
        """

        return self.get_focal() * self.unitsize


    def get_ratio(self):
        """ returns the camera aspect ratio """

        return self.ratio


    def get_fovx(self):
        """ returns the horizontal field-of-view """

        return self.fovx



class GL_Camera_Vals(Camera_Vals):
    """ the simulated camera class """

    def __init__(self):
        """ sets default pixel and sim units, image dimensions """

        self.ipw, self.iph = 1280, 960
        self.iuw, self.iuh = 1280, 960
        self.pixelsize = 1.
        self.unitsize = 0.00375             # mm
        self.fovy = 32.5855                 # degrees
        self.znear = 1. / self.unitsize     # mm -> sim units
        self.zfar = 100000. /self.unitsize  # mm -> sim units


    def get_focal(self):
        """ returns focal length in simulation units """

        return (self.iuh / 2.) / math.tan(math.radians(self.fovy)/2.)


    def get_ratio(self):
        """ calculates and returns aspect ratio """

        return float(self.ipw) / float(self.iph)


    def get_fovx(self):
        """ calculates and returns the horizontal field-of-view """

        return get_ratio() * self.fovy
