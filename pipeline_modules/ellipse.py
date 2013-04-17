#
# Milovision: A camera pose estimation programme
# 
# Copyright (C) 2013 Joris Stork
# See LICENSE.txt
#
# ellipse.py
""" 
:synopsis:  Contains the EllipseFitter class, a PipelineModule used to fit
            ellipses to the pipeline's sequences of contours.

.. moduleauthor:: Joris Stork <joris@wintermute.eu>

"""

import logging
import copy
import cv2
from pipeline_module import PipelineModule
import sys
import numpy as np
import math


class EllipseFitter(PipelineModule):


    def __init__(self, pipeline = None):
        """ 
        Sets ellipse filtering parameters and initialises accounting variables.
        
        """

        PipelineModule.__init__(self, pipeline = pipeline)
        self.nr_ellipses = 0.0
        self.nr_candidates = 0

        self.min_contour_length = 10
        self.max_aspect_ratio = 10.
        self.max_relative_inclination = 30.
        self.max_ctrs_distance = 4.
        # ratio ellipse sizes (outer/inner), (negative, positve) errors
        self.max_sizes_ratio_error = [0.25,0.50] 


    def convert_representation(self, ellipses = None):
        """ 
        Converts ellipse attributes to the pipeline's conventions regarding
        units of measurement and the camera's coordinate basis. 
        
        """

        e = copy.deepcopy(ellipses)
        for i, ellipse in enumerate(e):
            ((x_0, y_0), (b, a), alpha) = ellipse
            x_0 -= self.pipe.outputs[-1].cam.ipw / 2.
            x_0 *= self.pipe.outputs[-1].cam.pixelsize
            y_0 = self.pipe.outputs[-1].cam.iph - y_0
            y_0 -= self.pipe.outputs[-1].cam.iph / 2.
            y_0 *= self.pipe.outputs[-1].cam.pixelsize
            a *= self.pipe.outputs[-1].cam.pixelsize
            b *= self.pipe.outputs[-1].cam.pixelsize
            alpha = math.radians(alpha)
            e[i] = ((x_0, y_0), (b, a), alpha)
        return e


    def ellipse_to_dict(self, ellipse):
        """ converts the OpenCV ellipse representation to a dict """

        temp = copy.deepcopy(ellipse)
        ed = {}
        ed['minor'], ed['major'] = temp[1][0], temp[1][1]
        ed['ctr'] = np.asarray(temp[0])
        ed['alpha'] = temp[2]
        ed['object'] = ellipse
        return ed


    def larger_smaller(self, a, b):
        """ returns a and b in the order: largest, smallest """

        if b['major'] > a['major']:
            return b, a
        else:
            return a, b


    def aspect_ratio(self, e):
        """ returns the aspect ratio of the given ellipse """

        return abs(e['major'] / e['minor'])


    def aspect_ratio_ok(self, e):
        """ 
        Tests whether aspect ratio of the given ellipse is within a
        pre-determined limit
        
        """

        aspect_ratio = self.aspect_ratio(e)
        return aspect_ratio <= self.max_aspect_ratio


    def distance_ok(self, a, b):
        """ 
        Tests whether the distance between the centres of the given ellipses is
        within a pre-determined limit. nb: np.linalg.norm returns an absolute
        value.
        
        """

        return np.linalg.norm(a['ctr'] - b['ctr']) <= self.max_ctrs_distance


    def relative_inclination_ok(self, a, b):
        """ 
        Tests whether the difference between the inclinations of the two given
        ellipses is within a pre-determined limit.
        This is not used for near-circular ellipses.
        
        """

        return abs(a['alpha'] - b['alpha']) < self.max_relative_inclination


    def sizes_ratio_ok(self, larger = None, smaller = None):
        """ 
        Tests whether ratio of sizes of given ellipses is within a
        pre-determined range.
        
        """

        outer = self.pipe.outputs[-1].markers[-1].config.outer_circle_diam * 1.
        inner = self.pipe.outputs[-1].markers[-1].config.inner_circle_diam * 1.
        correct_ratio = outer / inner 
        ratio = abs(larger['major'] / smaller['major'])
        not_too_small = ratio > (correct_ratio - self.max_sizes_ratio_error[0])
        not_too_big = ratio < (correct_ratio + self.max_sizes_ratio_error[1])
        return not_too_small and not_too_big


    def both_circular(self, a, b):
        """ 
        Tests whether given ellipses have an aspect ratio smaller than a pre-determined limit.
        
        """

        return (self.aspect_ratio(a) < 1.2) and (self.aspect_ratio(b) < 1.2)


    def marker_filter(self, ellipses = None):
        """ 
        Compares every ellipse (a) with every other (b), and returns those that
        pass various tests relating to aspect ratio, sizes, location and
        inclination. 
    
        """

        candidates = []

        for i in xrange(len(ellipses)):
            conditions = []

            a = self.ellipse_to_dict(ellipses[i])
            if not self.aspect_ratio_ok(a):
                continue

            for j in xrange(len(ellipses) - (i+1)):
                conditions = []

                b = self.ellipse_to_dict(ellipses[j+i+1])
                larger, smaller = self.larger_smaller(a, b)

                if not self.aspect_ratio_ok(b):
                    continue
                if not self.distance_ok(a,b):
                    continue
                if not self.both_circular(a,b):
                    if not self.relative_inclination_ok(a, b):
                        continue
                if not self.sizes_ratio_ok(larger, smaller):
                    continue

                if larger['object'] not in candidates:
                    candidates.append(larger['object'])

        return candidates


    def run(self):
        """ 
        The main function. Rejects contours below a pre-determined length;
        filters the remainder; converts the remaining ellipses to the pipeline's
        representational convention; and draws these ellipses over the current
        camera image in an OpenCV window before saving them to the pipeline.
        
        """

        ellipses = []
        if self.pipe.modules[0].__class__.__name__ == 'ContourFinder':
            for cont in self.pipe.modules[0].conts:
                if len(cont) < self.min_contour_length:
                    continue
                ellipses.append(cv2.fitEllipse(cont))
            self.nr_ellipses +=  len(ellipses)
        else:
            self.logger.error('no ContourFinder in pipeline')
            self.pipe.shutdown()

        candidates = self.marker_filter(ellipses)
        self.nr_candidates += len(candidates)
        converted_candidates = self.convert_representation(ellipses=candidates)

        self.pipe.ellipses = []
        for conv_candidate, candidate in zip(converted_candidates, candidates):
            cv2.ellipse(
                    img = self.pipe.canv,
                    box = candidate,
                    color = (255,255,255),
                    thickness = 2,
                    lineType = cv2.CV_AA # antialiased
                    )
            self.pipe.ellipses.append(conv_candidate)
