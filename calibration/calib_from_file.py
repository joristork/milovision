#!/usr/bin/env python
#
# Milovision: A camera pose estimation programme
# 
# Copyright (C) 2013 Joris Stork
# See LICENSE.txt
#
# calib_from_file.py

"""
:synopsis:  Using corresponding points loaded from npy files on disk: estimates
            the camera's intrinsic parameters and writes these to file. NB:
            currently requires 9x6 chessboard (inner points)

.. moduleauthor:: Joris Stork <joris@wintermute.eu>

"""

__author__ = "Joris Stork"

import sys

import cv2
import matplotlib.pyplot as plt
import numpy as np



def main():
    """ serialises intrinsics estimates from CalibrateCamera2 to disk """

    camera_matrix = np.array([
        [1.60000000e+03, 0.0, 6.90000000e+02], 
        [0.0, 1.60000000e+03, 4.80000000e+02], 
        [0.0, 0.0, 1.]
        ])

    dist_coeffs = np.zeros(4)

    image_pts = [np.load("image_pts.npy")]
    model_pts = [np.load("model_pts.npy")]

    #print image_pts.shape
    #print model_pts.shape

    imsize = (960, 1280)

    success, intrinsic, distortion_coeffs, rot_est_vecs, transl_est_vecs = cv2.calibrateCamera(model_pts, image_pts, imsize, camera_matrix, dist_coeffs, flags=cv2.CALIB_USE_INTRINSIC_GUESS)

    np.save("intrinsic.npy", intrinsic)
    np.save("distortion_coeffs.npy", distortion_coeffs)
    np.save("calibration_rotation_vectors.npy", rot_est_vecs)
    np.save("calibration_translation_vectors.npy", transl_est_vecs)


if __name__ == '__main__':

    main()
