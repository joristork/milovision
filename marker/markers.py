#
# Milovision: A camera pose estimation programme
# 
# Copyright (C) 2013 Joris Stork
# See LICENSE.txt
#
# markers.py
"""
:synopsis:  Marker_Config, Marker, and Texture (sub)classes.  The __init__
            functions define the (gl)marker configurations 

.. moduleauthor:: Joris Stork <joris@wintermute.eu>

"""
# todo: logging

import numpy as np
from OpenGL.GL import *
import Image
import StringIO
import numpy as np
import math
import sys
import copy


class Marker_Config(object):
    """ stores key marker attributes; parent class to simulated version """

    def __init__(self, config_id = 0, C = None, N = None):
        """ sets configuration values for a real marker """

        self.outer_circle_diam = [          # mm
                188.
                ][config_id]
        self.inner_circle_diam = [          # mm
                141.
                ][config_id]
        self.C = np.array(C)
        self.N = np.array(N)


class GL_Marker_Config(Marker_Config):
    """ stores simulated marker parameters """

    def __init__(self, config_id = 0):
        """ define marker positions, sizes, and image files here """

        self.file_id = [
                'marker/marker.png'
                ][config_id]
        self.simul_frame_height = [             # mm (is converted to sim units)
                210.     # ~210mm (A4 minor length at 0.00375mm pixel size))
                ][config_id] 
        self.orig_frame_height = [              # pixels (doesn't change)
                256.
                ][config_id]
        self.inner_circle_diam = [              # pixels (is converted to mm)
                180.
                ][config_id]
        self.outer_circle_diam = [              # pixels (is converted to mm)
                240.
                ][config_id]
        self.C = [                              # mm (is converted to sim units)
                np.array([0.,0.,-6000.])#-359.2407])        
                ][config_id]
        self.N = [                              # sim units (remains sim units)
                np.array([0., 0., -1.])
                ][config_id]


class Marker(object):
    """ represents real fiducial marker; parent class for simulated markers """

    def __init__(self, config_id = 0, cam = None, C = None, N = None):
        """ sets this marker's config and camera objects """

        self.config = Marker_Config(config_id, C, N)
        self.cam = cam


    def get_C(self):
        """ obtains (value of) circle centre in camera coordinates """

        if hasattr(self.config, 'C'):
            return copy.deepcopy(self.config.C)
        else:
            return None


    def get_C_mm(self):
        """ obtains (value of) circle centre in camera coordinates in mm """

        C = self.get_C()
        if C is not None:
            for i, item in enumerate(C):
                C[i] = item * self.cam.unitsize
        return C


    def get_N(self):
        """ obtains (value of) circle centre in camera coordinates """

        if hasattr(self.config, 'N'):
            return copy.deepcopy(self.config.N)
        else:
            return None


    def get_N_mm(self):
        """ obtains (value of) circle centre in camera coordinates in mm """

        N = self.get_N()
        if N is not None:
            for i, item in enumerate(N):
                N[i] = item * self.cam.unitsize
        return N


    def get_circle_radius(self):
        """ obtains (value of) circle centre in camera coordinates """

        return self.config.outer_circle_diam / 2.


    def get_circle_radius_mm(self):
        """ obtains (value of) circle centre in camera coordinates in mm """

        return self.get_circle_radius() / self.cam.unitsize



class GL_Marker(Marker):
    """ represents a simulated fiducial marker """

    def __init__(self, config_id = 0, cam = None):
        """ 
        Sets key attributes, camera and vertex coordinates and converts all
        attribute values to simulation units 
        
        """

        self.config = GL_Marker_Config(config_id)
        self.cam = cam
        self.set_circle_sizes()
        self.convert_to_sim_units()
        self.vertices = np.array([
            [-0.5,  0.5, 0.],
            [ 0.5,  0.5, 0.],
            [ 0.5, -0.5, 0.],
            [-0.5, -0.5, 0.]
            ]) * self.config.simul_frame_height


    def set_circle_sizes(self, outer=None, inner=None):
        """ derives and records dimensions of inner and outer circles in mm """ 

        sim_orig_ratio = self.config.simul_frame_height / self.config.orig_frame_height
        self.config.outer_circle_diam *= sim_orig_ratio
        self.config.inner_circle_diam *= sim_orig_ratio


    def flip_z(self, vertex):
        """ reverses direction of z coordinates (to switch conventions) """

        rev_z_matrix = np.array([
            [1., 0., 0.],
            [0., 1., 0.],
            [0., 0.,-1.]
                ])
        return np.dot(rev_z_matrix, vertex)


    def simunits_to_mm(self, value):
        """ converts given value from simulation units to mm """

        return value * self.cam.unitsize


    def get_C_mm(self):
        """ obtains circle centre in camera coordinates in mm """

        return self.flip_z(self.simunits_to_mm(self.get_C()))


    def get_N_mm(self):
        """ obtains marker normal in camera coordinates in mm """

        return self.flip_z(self.simunits_to_mm(self.get_N()))


    def load_texture(self):
        """ loads config-specific texture from file, binds it to this marker """

        texture = GL_Marker_Texture(self.config.file_id)
        self.texture_id = glGenTextures(1)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexImage2D(GL_TEXTURE_2D, 0, 4, texture.xsize, texture.ysize, 0, GL_RGBA, GL_UNSIGNED_BYTE, texture.raw)
        glEnable(GL_TEXTURE_2D)
        return texture, self.texture_id


    def draw(self, textures):
        """ 
        Draws this marker for the current OpenGL model-view matrix.
        Note that glbintexture would be needed for multiple markers. 
        
        """

        C = self.config.C
        texture = textures[self.texture_id]

        glPushMatrix()
        glTranslatef(C[0], C[1], C[2])

        glColor(list(texture.colour))
        glBegin(GL_QUADS)
        for vertex, tcoord in zip (self.vertices, texture.coords):
            glTexCoord2f(tcoord[0],tcoord[1])
            glVertex(vertex)
        glEnd()

        glPopMatrix()


    def convert_to_sim_units(self):
        """ converts marker vertices and sizes to simulation units """

        unitsize = self.cam.unitsize
        self.config.C = self.config.C / unitsize
        self.config.simul_frame_height = self.config.simul_frame_height / unitsize
        self.config.outer_circle_diam = self.config.outer_circle_diam / unitsize
        self.config.inner_circle_diam = self.config.inner_circle_diam / unitsize


    def set_min_dist(self):
        """ sets the marker at a distance that vertically fills the image """
         
        angle = math.radians(self.cam.fovy) * 0.5
        min_dist = 0.5 * self.config.simul_frame_height / math.tan(angle)
        self.config.C[2] = -1. * min_dist


class GL_Marker_Texture(object):
    """ wrapper for the marker texture """

    def __init__(self, filename, colour=(1.,1.,1.)):
        """ sets attributes including image size, vertices, and raw image """

        self.colour = colour
        self.img = Image.open(filename)
        self.xsize = self.img.size[0]
        self.ysize = self.img.size[1]
        self.raw = self.img.convert('RGBA').tostring('raw', 'RGBA')
        self.coords = np.array([
            [0, 1],
            [1, 1],
            [1, 0],
            [0, 0]
            ])
