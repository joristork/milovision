#
# Milovision: A camera pose estimation programme
# 
# Copyright (C) 2013 Joris Stork
# See LICENSE.txt
#
# contour.py
""" 
:synopsis:  Contains the ContourFinder subclass of the PipelineModule class.

.. moduleauthor:: Joris Stork <joris@wintermute.eu>

"""

import logging
import copy
import cv
import cv2
from pipeline_module import PipelineModule
import numpy as np
import Image

class ContourFinder(PipelineModule):
    """
    Applies a series of image processing techniques to extract contours from the
    pipeline's ``original'' image, and draws the contours in the pipeline's
    ``canvas'' image.
    
    """

    def __init__(self, pipeline = None):
        """ The pipeline logs the number of ellipses.  """
        
        PipelineModule.__init__(self, pipeline = pipeline)
        self.nr_conts = 0.0


    def run(self):
        """ 
        Applies the following steps to the pipeline's original image:
            1. contrast stretching
            2. blur
            3. edge detection (Canny)
            4. find contours
            
        The result is saved to the pipeline's canvas image.

        """

        self.pipe.canv = cv2.equalizeHist(self.pipe.orig)
        self.pipe.canv = cv2.GaussianBlur(self.pipe.canv, (7,7), sigma1 = 1.4, sigma2 = 1.4)
        self.pipe.canv = cv2.Canny(self.pipe.canv, 50, 150)
        self.conts, hierarchy = cv2.findContours(self.pipe.canv, cv2.RETR_LIST, cv2.CHAIN_APPROX_TC89_L1)
        self.nr_conts += len(self.conts) * 1.0
        cv2.drawContours(self.pipe.canv, self.conts, -1, (128, 128, 128))
