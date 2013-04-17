#!/usr/bin/env python
#
# Milovision: A camera pose estimation programme
# 
# Copyright (C) 2013 Joris Stork
# See LICENSE.txt
#
# simulator.py
"""
:synopsis:  Implements the simulation of camera operation in an environment with
            fiducial markers. OpenGL based.

.. moduleauthor:: Joris Stork <joris@wintermute.eu>

"""
# todo: multiprocessing-aware exception handling
# todo: replace glut. with pygame?

# third party packages
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import Image
import StringIO
import numpy as np
import sys
import time
import copy

# milovision modules
from pipeline_modules import PipelineModule
from marker import GL_Marker
from camera_values import GL_Camera_Vals
from pose_generator import Linear_Pose_Generator, Random_Pose_Generator


class GL_Simulator(PipelineModule):
    """ note that the simulator is a pipeline module """


    def __init__(self, queues = None, options = None):
        """ 
        Sets OpenGL machine state; message queues to and from the pipeline;
        camera; pose generator; initial model-view matrix; and optionally starts
        up the main function.
        See images directory for all possible markers 
        Variables:
            iph: image height in pixels (similarly ipw)
            iuh: image height in simulation units (similarly iuw)
        
        """

        PipelineModule.__init__(self, options = options)
        glHint(GL_PERSPECTIVE_CORRECTION_HINT, GL_NICEST)
        glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)
        glHint(GL_POINT_SMOOTH_HINT, GL_NICEST)
        glHint(GL_POLYGON_SMOOTH_HINT, GL_NICEST)
        glHint(GL_FOG_HINT, GL_NICEST)
        glEnable(GL_DEPTH_TEST)             # necessary?
        glEnable(GL_BLEND)
        glBlendFunc(GL_ONE, GL_SRC_COLOR)
        glShadeModel(GL_SMOOTH)
        glClearColor(0, 0, 0, 0.)

        self.q2sim, self.q2pipe = queues
        self.output = self.q2sim.get()
        self.output.cam = GL_Camera_Vals()
        cam = self.output.cam
        self.pose_generator = None

        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        ratio = cam.get_ratio()
        gluPerspective(cam.fovy, ratio, cam.znear, cam.zfar)

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        if queues:
            self.main()

    
    def resize_window(self, w, h):
        """ 
        Adjust parameters to reflect a resized simulation window; nb: this
        is included to allow for smooth operation, but is not recommended for
        experimental simulations.
        
        """

        cam = self.output.cam
        cam.ipw = w
        if h == 0:
            cam.iph = 1
        else:
            cam.iph = h

        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        ratio = cam.get_ratio()
        gluPerspective(cam.fovy, ratio, cam.znear, cam.zfar)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        self.output.cam = cam
        self.logger.info('window resized to %dx%d'%(w,h))


    def dispatch_to_pipe(self):
        """ 
        Sends image from current buffer and corresponding marker pose(s) to
        pipeline over message queue.
        
        """

        cam = self.output.cam
        data = glReadPixels(0, 0, cam.ipw, cam.iph, GL_RGBA, GL_UNSIGNED_BYTE)
        image_dims = (cam.ipw, cam.iph)
        frame = Image.frombuffer("RGBA", image_dims, data, "raw", "RGBA",0,0).convert("L")
        np_img = np.array(frame)
        self.q2pipe.put_nowait(('simulglob', np_img, self.output))


    def refresh_output(self):
        """ 
        Replaces output with a copy that is reset to avoid overlap with the
        object in q2pipe.
        
        """

        self.output = copy.deepcopy(self.output)
        self.output.reset_markers_and_time()


    def draw(self):
        """ 
        Called from within OpenGL. Refreshes data and settings as necessary;
        obtains new marker poses from generator; exits the simulator and
        pipeline if the generators are done; calls all the markers' draw
        functions; and calls the function to send image and pose data to the
        pipeline. The buffers are then swapped for the next image to be drawn.

        """

        self.refresh_output()
        self.markers = []
        if not self.q2sim.empty():
            incoming = self.q2sim.get()
            if 'stop' in incoming:
                time.sleep(0.5)
                self.stop()
            elif 'newoutput' in incoming:
                self.output = incoming[1]
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glClearColor(0.5, 0.5, 0.5, 0.5)

        if self.options.simulate < 0:
            markers = self.pose_generator.generate()
            if not markers:
                self.logger.info('generator complete')
                self.stop()
                return
            elif not isinstance(markers, list):
                self.output.markers = [markers]
            else:
                self.output.markers = markers

        for marker in self.output.markers:
            marker.draw(self.textures)

        self.dispatch_to_pipe()
        glutSwapBuffers()


    def key_press(self, *args):
        """ enables the option to quit within the simulator window with 'q' """

        if args[0] == 'q':
            self.logger.info('q pressed')
            self.stop()


    def stop(self):
        """ tries to exit simulator and pipeline cleanly """

        self.q2pipe.put_nowait('stop')
        self.logger.info('poisoning pipeline for good measure')
        time.sleep(0.05)
        glutDestroyWindow(window)
        glutLeaveMainLoop()
        self.logger.info('exiting')


    def main(self):
        """
        This function refers to the command line options, and: performs more
        initialisation for the OpenGL machine; displays a simulation window;
        initialises the required pose generator; initialises the markers and
        sets the corresponding textures; and calls OpenGL's main loop.
        
        """

        global window
        glutInit()
        glutInitDisplayMode(GLUT_RGBA | GLUT_DOUBLE | GLUT_ALPHA | GLUT_DEPTH)
        glutInitWindowSize(self.output.cam.ipw, self.output.cam.iph)
        glutInitWindowPosition(50,50)
        window = glutCreateWindow('simulator')
        glutIdleFunc(self.draw)
        glutReshapeFunc(self.resize_window)
        glutKeyboardFunc(self.key_press)
        print 'press \'q\' to exit simulator'
        glutDisplayFunc(self.draw)

        markers = []
        self.textures = {}
        if self.options.simulate == -1:
            self.pose_generator = Random_Pose_Generator(self.output)
        elif self.options.simulate == -2:
            self.pose_generator = Linear_Pose_Generator(self.output)
        else:
            if (self.options.simulate == -1) or (self.options.simulate == -2):
                self.logger.error('incompatible simulation options')
                self.stop()
            index = self.options.simulate
            marker = GL_Marker(config_id = index, cam = self.output.cam)
            markers.append(marker)
            texture, texture_id = markers[-1].load_texture()
            self.textures[texture_id] = texture
        if self.options.simulate == -1 or self.options.simulate == -2:
            texture, texture_id = self.pose_generator.init_marker.load_texture()
            self.textures[texture_id] = texture
        self.output.markers = markers

        glutMainLoop()


if __name__ == '__main__':
    simulator = GL_Simulator()
    simulator.main()
