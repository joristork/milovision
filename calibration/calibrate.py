#!/usr/bin/env python
#
# Milovision: A camera pose estimation programme
# 
# Copyright (C) 2013 Joris Stork
# See LICENSE.txt
#
# calibrate.py

"""
:synopsis:  Estimates the camera's intrinsic parameters and writes these to
            file. NB: currently requires a 9x6 chessboard (nr. inner points).
            
            This module is partly inspired from example code in: 
            “Computer vision with the OpenCV library”, in: Gary Bradski
            & Adrian Kaebler - OReilly (2008).


.. moduleauthor:: Joris Stork <joris@wintermute.eu>

"""

__author__ = "Joris Stork"

# standard library and third party packages
import sys
import signal
import logging
import time
from pydc1394 import DC1394Library, Camera
from pydc1394.cmdline import add_common_options, handle_common_options
import cv2
import matplotlib.pyplot as plt
import numpy as np

# milovision modules
import loginit
import argparse

cam = None


def signal_handler(signal, frame):
    """ ensures a clean exit on receiving a ctrl-c """

    print '\n\nctrl-c received. Shutting down camera and exiting.'
    global cam
    cam.stop()
    sys.exit(0)


def main():
    """ 
    See module synopsis. Passes image stream from camera driver to OpenCV's
    chessboard corner finder until a threshold number of point correspondence
    sets are achieved. Passes these sets to OpenCV/CalibrateCamera2, and writes
    the resulting estimate for the camera intrinsics to file using Numpy's save
    function.
    
    """

    #p = optparse.OptionParser(usage="Usage: %prog [ options ]\n"
    #  "This program lets the camera run in free running mode.")
    options, args = argparse.run()
    loginit.run(options.verbosity)
    logger = logging.getLogger('main')

    #add_common_options(p)

    l = DC1394Library()
    global cam
    cam = handle_common_options(options, l)

    try:
        cam.start(interactive = True)
    except IOError:
        print 'error: cannot open stream' 
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
    i = 0

    while i < nr_samples:
        frame = np.asarray(cam.current_image)
        found, points = cv2.findChessboardCorners(frame, dims, flags=cv2.CALIB_CB_FAST_CHECK)
        if found and ((points.shape)[0] == pts_per_board):
            cv2.drawChessboardCorners(frame, (6,9), points, found)
            cv2.imshow("win2", frame)
            cv2.waitKey(2)
            step = i * pts_per_board
            j = 0

            while j < pts_per_board:
                image_pts[step, 0] = points[j, 0, 0]
                image_pts[step, 1] = points[j, 0, 1]
                model_pts[step, 0] = float(j) / float(dims[0])
                model_pts[step, 1] = float(j) % float(dims[0])
                model_pts[step, 2] = 0.0
                step += 1
                j += 1

            pt_counts[i, 0] = pts_per_board
            cv2.waitKey(2)
            i += 1
            time.sleep(1)

        else:
            cv2.imshow("win2", frame)
            cv2.waitKey(2)

    camera_matrix = np.array([
        [2.23802515e+03, 0.0, 5.89782959e+02], 
        [0.0, 2.07124146e+03, 4.55921570e+02], 
        [0.0, 0.0, 1.]
        ])
    dist_coeffs = np.zeros(4)

    np.save("image_pts.npy", image_pts)
    np.save("model_pts.npy", model_pts)

    success, intrinsic, distortion_coeffs, rot_est_vecs, transl_est_vecs = cv2.calibrateCamera(model_pts, image_pts, frame.shape, camera_matrix, dist_coeffs, flags=cv2.CALIB_USE_INTRINSIC_GUESS)

    np.save("intrinsic.npy", intrinsic)
    np.save("distortion_coeffs.npy", distortion_coeffs)
    np.save("calibration_rotation_vectors.npy", rot_est_vecs)
    np.save("calibration_translation_vectors.npy", transl_est_vecs)


if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)

    main()
