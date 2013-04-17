#
# Milovision: A camera pose estimation programme
# 
# Copyright (C) 2013 Joris Stork
# See LICENSE.txt
#
# pipeline_module.py
""" 
:synopsis:  Contains the PipelineModule class, the base class for pipeline
            modules. 

.. moduleauthor:: Joris Stork <joris@wintermute.eu>

"""

import logging
import copy
import cv


class PipelineModule(object):

    def __init__(self, pipeline = None, options = None):
        """ Set logger, verbosity, relevant command line options """

        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info('initialised')
        self.pipe = pipeline
        self.options = options


    def run(self):

        pass
