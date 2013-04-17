#!/usr/bin/env python
#
# Milovision: A camera pose estimation programme
# 
# Copyright (C) 2013 Joris Stork
# See LICENSE.txt
#
# timebox.py

import timeit

import sys
import signal
import logging

import loginit
import argparse

from pydc1394 import DC1394Library, Camera
from pydc1394.cmdline import add_common_options, handle_common_options

import cv as cv2
import matplotlib.pyplot as plt
import numpy as np

setup = """
import sys
import signal
import logging

import loginit
import argparse

from pydc1394 import DC1394Library, Camera
from pydc1394.cmdline import add_common_options, handle_common_options

import cv2
import matplotlib.pyplot as plt
import numpy as np

cam = None


def signal_handler(signal, frame):
    global cam
    cam.stop()
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)

options, args = argparse.run()
loginit.run(options.verbosity)
logger = logging.getLogger('main')

l = DC1394Library()
cam = handle_common_options(options, l)

try:
    cam.start(interactive = True)
except IOError:
    exit(1)

dims = (9,6)
pts_per_board = dims[0] * dims[1]
nr_samples = 20

pt_counts = np.zeros((nr_samples, 1), dtype = int)                   #pts per image

frame = np.asarray(cam.current_image)
model_pts = np.zeros((nr_samples * pts_per_board, 3), dtype = float)
model_pts = model_pts.astype('float32')
image_pts = np.zeros((nr_samples * pts_per_board, 2), dtype = float)
image_pts = image_pts.astype('float32')
found, points = cv2.findChessboardCorners(frame, dims)
i = 0
"""

def main():

    global setup

    t = timeit.Timer(stmt="found, points = cv2.findChessboardCorners(frame, dims); cam.stop()", setup=setup)
    print t.timeit(number = 100) / 100.0
    print '\n'
    exit(0)


if __name__ == '__main__':

    main()
