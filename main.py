#!/usr/bin/env python
#
# Milovision: A camera pose estimation programme
# 
# Copyright (C) 2013 Joris Stork
# See LICENSE.txt
#
# main.py

""" :synopsis:  Contains the main initialising function but not the main
                application loop, which is in pipeline.py. "milovision" is the
                code name for this project.

.. moduleauthor:: joris stork <joris@wintermute.eu>

"""

# standard and third party libraries
import sys
import os
import logging
import cv2
import signal
from pydc1394 import DC1394Library, camera
from pydc1394.cmdline import add_common_options, handle_common_options
import matplotlib.pyplot as plt
import numpy as np
import multiprocessing

# milovision libraries
from pipeline import Pipeline
from admin_modules import loginit
from admin_modules import argparse
from output import Printer

pipeline = None

def signal_handler(signal, frame):
    """ enables clean shutdown with ctrl-c """

    process_id = multiprocessing.current_process().name
    if process_id == 'child':
        return
    logger = logging.getlogger('signal_handler')
    logger.info('ctrl-c received.')
    logger.info('telling pipeline to shutdown')
    global pipeline
    pipeline.shutdown()


def main():
    """ 
    Parses arguments; initialises logger; initialises camera driver if
    necessary; loads single image from disk if necessary; and runs desired parts
    of pipeline, or loads output from previous execution for printout.
    
    """

    options, args = argparse.run()
    loginit.run(options.verbosity)
    logger = logging.getLogger('main')

    logger.info(' '.join(sys.argv[1:]))

    if options.simulate == 0:
        options.simulate = None
        l = DC1394Library()
    elif options.simulate > 0:
        options.simulate -= 1
    elif options.simtime is None:
        options.simtime = 36000

    global pipeline
    pipeline = Pipeline(options)

    if options.disk:
        logger.info('using poses from disk')
        pipe = Pipeline()
        pipe.options = options
        printer = Printer(pipe=pipe)
        printer.final()
        logger.info('done. exiting')
        sys.exit(0)

    if args:
        try:
            image = cv2.imread('images/'+args[0], cv2.CV_LOAD_IMAGE_GRAYSCALE)
            pipeline.set_image(image)
            logger.info('opening image file %s from disk' % args[0])
        except IOError:
            logger.error('image file not found: %s' % args[0])
            exit(1)
    elif options.simulate is not None:
        logger.info('running in simulation mode')
    else:
        try:
            fwcam = handle_common_options(options, l)
            pipeline.set_fwcam(fwcam)
            logger.info('init. pydc1394 camera object')
            logger.info('camera: %s' % fwcam.model)
            logger.info('mode: %s' % fwcam.mode)
            logger.info('framerate: %d' % fwcam.framerate.val)
        except:
            logger.error('unable to open camera capture')
            exit(1)

    pipeline.run()


if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)

    main()
