#
# Milovision: A camera pose estimation programme
# 
# Copyright (C) 2013 Joris Stork
# See LICENSE.txt
#
# posea.py
""" 
:synopsis:  Contains the first pose estimation PipelineModule,
            PoseEstimatorA.
            
            See thesis report for background and further details.

.. moduleauthor:: Joris Stork <joris@wintermute.eu>

"""

import logging
import copy
import cv2
from pipeline_module import PipelineModule
import numpy as np
from marker import Marker
import Image


class PoseEstimatorA(PipelineModule):
    """
    Describes two candidates for the centre and normal of the circles that
    may correspond to the ellipses found in an image.
    
    """

    def __init__(self, pipeline = None):
        """ 
        Initialises accounting variables, then sets focal length and circle
        radius values according to whether the camera is simulated or not.
        The pipeline logs the number of ellipses.
        
        """
        
        PipelineModule.__init__(self, pipeline = pipeline)
        self.nrlopt1 = 0
        self.nrlopt2 = 0
        self.nrlopt3 = 0
        if self.pipe.options.simulate:
            self.focal_length = self.pipe.outputs[-1].cam.get_focal()
            self.radius = self.pipe.outputs[-1].markers[0].get_circle_radius()*2.075
        else:
            self.focal_length = self.pipe.init_output.cam.get_focal()
            self.radius = self.pipe.init_output.markers[0].get_circle_radius()*2.075


    def get_quadratic(self, ellipse):
        """ 
        Obtains general quadratic form parameters (note that f does not denote
        the focal length) for :

        Ax^2 + 2Bxy + Cy^2 + 2Dx + 2Ey + F = 0

        And returns these in matrix form A, where p A p.T = 0 describes the
        ellipse (as in Chen et al., eqn. 2). The approach used is taken from:
        http://www.mathworks.ch/
            matlabcentral/answers/37124-ellipse-implicit-equation-coefficients
            
        """

        ((x_0, y_0), (b, a), alpha) = ellipse

        if b == 0.0 or a == 0.0:
            self.logger.error('b = %f, a = %f' % (b,a))
            sys.exit(0)

        X_0 = np.array([x_0, y_0])
        R_e = np.array([
            [np.cos(alpha), -(np.sin(alpha))],
            [np.sin(alpha), np.cos(alpha)]]
            )
        temp = np.diag(np.array([1.0 / np.power(a,2),1.0 / np.power(b,2)]))
        M = np.dot(R_e, np.dot(temp, R_e.T))
        A = M[0,0]
        B = M[0,1]
        C = M[1,1]
        D = A * x_0 + B * y_0
        E = B * x_0 + C * y_0
        F = np.dot(X_0.T, np.dot(M, X_0)) - 1.0

        return np.array([
            [A, B, D],
            [B, C, E],
            [D, E, F]
            ])


    def get_obl_el_cone(self, E, f):
        """ 
        Returns the matrix of the oblique elliptical cone, as in
        Chen et al. eqn. 5. 
        
        """

        return np.array([
            [E[0,0], E[0,1], - E[0,2] / f],
            [E[1,0], E[1,1], - E[1,2] / f],
            [- E[2,0] / f, - E[2,1] / f, E[2,2] / (f*f)]
            ])


    def get_chen_eigend(self, Q):
        """ 
        Returns the eigendecomposition of the ellipse matrix, ordered as
        specified in Chen et al.

        """
        
        l, V = np.linalg.eig(Q)

        rev_abs_sort_ind = np.argsort(np.power(np.abs(l), -1))
        l_opt1 = l[rev_abs_sort_ind]
        if (l_opt1[0] * l_opt1[1] > 0) and (l_opt1[1] * l_opt1[2] < 0):
            self.nrlopt1 += 1
            return l_opt1, V[:,rev_abs_sort_ind]
        else:
            l_opt2 = np.array([l_opt1[1],l_opt1[2],l_opt1[0]])
            if (l_opt2[0] * l_opt2[1] > 0) and (l_opt2[1] * l_opt2[2] < 0):
                self.nrlopt2 += 1
                return l_opt2, V[:,(1,2,0)]
            else:
                l_opt3 = np.array([l_opt1[0],l_opt1[2],l_opt1[1]])
                if (l_opt3[0] * l_opt3[1] > 0) and (l_opt3[1] * l_opt3[2] < 0):
                    self.nrlopt3 += 1
                    return l_opt3, V[:,(0,2,1)]
                else:
                    self.logger.error('could not satisfy Chen et al. eqn. 16')
                    sys.exit(0)


    def get_Cs_Ns(self, l, V, r):
        """ 
        Derives the centre and normal of the circle expressed in the camera
        coordinate system. Employs the definitions in Chen et al., eqn. 20.
        
        """

        Cs = np.zeros((8,3))
        Ns = np.zeros((8,3))
        signs = [1.0, -1.0]
        i = 0
        for s1 in signs:
            for s2 in signs:
                for s3 in signs:

                    z0 = (s3 * l[1] * r) / np.sqrt(-l[0] * l[2])

                    temp = np.array([
                        [s2 * (l[2]/l[1]) * np.sqrt((l[0]-l[1])/(l[0]-l[2]))],
                        [0],
                        [-s1 * (l[0]/l[1]) * np.sqrt((l[1]-l[2])/(l[0]-l[2]))]
                        ])

                    Cs[i] = (z0 * np.dot(V, temp)).flatten()

                    temp = np.array([
                        [s2 * np.sqrt((l[0]-l[1])/(l[0]-l[2]))],
                        [0],
                        [- s1 * np.sqrt((l[1]-l[2])/(l[0]-l[2]))]
                        ])

                    Ns[i] = (np.dot(V, temp)).flatten()

                    i += 1

        return Cs, Ns


    def remove_impossible(self, Cs, Ns):
        """ 
        As per Chen et al. eqn. 21, removes those (centre, normal) pairs that
        would represent a marker behind the camera or a marker facing away from
        the camera. This should leave two (C,N) pairs per ellipse.

        """

        c_result, n_result = np.zeros((2,3)), np.zeros((2,3))
        nr_found = 0
        for i in xrange(len(Cs)):
            zmask = np.array([[0.0, 0.0, 1.0]])
            faces = (np.dot(Ns[i].flatten(), zmask.T) < 0.0 )
            infront = (np.dot(Cs[i].flatten(), zmask.T) > 0.0)
            if faces and infront:
                c_result[nr_found] = Cs[i]
                n_result[nr_found] = Ns[i]
                nr_found += 1
        if not (nr_found == 2):
            self.logger.error('nr(candidate (C,N) pairs) not 2')
            self.pipe.shutdown()
            sys.exit(1)
        return c_result, n_result


    def run(self):
        """ 
        Proceeds in the following steps:
            1.  obtains the equation of the ellipse from the ellipse's
                bounding box, and the matrix describing the ellipse (as in
                Chen et al., eqn. 2.)
            2.  obtains the Q matrix describing the oblique elliptical cone
                (as in Chen et al., eqn. 5), from the matrix found in step 1, and
                from the camera's intrinsic parameters.
            3.  derives the set of possible contour and normal pairs
                {(C_i,N_i)} from the Q_c matrix. We order the
                eigendecomposition to satisfy equation 16 in Chen et al.
            4.  eliminates the impossible pairs, to obtain two candidate pairs.

        """


        if not self.pipe.ellipses and (self.pipe.options.simulate is None):
            self.pipe.outputs.append(copy.deepcopy(self.pipe.init_output))

        est_markers = []
        for ellipse in self.pipe.ellipses:
            E = self.get_quadratic(ellipse)
            Q = self.get_obl_el_cone(E, self.focal_length)
            l, V = self.get_chen_eigend(Q)
            Cs, Ns = self.get_Cs_Ns(l,V,self.radius)
            Cs, Ns = self.remove_impossible(Cs, Ns)
            cam = self.pipe.init_output.cam
            em = Marker(cam = cam, C = Cs, N = Ns)
            est_markers.append(em)
        if self.pipe.options.simulate:
            self.pipe.outputs[-1].est_markers = est_markers
        else:
            output = copy.deepcopy(self.pipe.init_output)
            output.est_markers = [est_marker]
            self.pipe.outputs.append(output)
