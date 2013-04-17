#
# Milovision: A camera pose estimation programme
# 
# Copyright (C) 2013 Joris Stork
# See LICENSE.txt
#
# pipeline_output.py
""" 
:synopsis:  Contains the Pipeline_Output class, which holds all useful data
            produced by one pipeline run.

.. moduleauthor:: Joris Stork <joris@wintermute.eu>

"""

import logging
import time
import numpy as np


class Pipeline_Output(object):
    """ 
    Holds all relevant pose estimation and performance data emerging from the
    pipeline.
    
    """

    def __init__(self, sim = False):
        """ 
        Sets simulator, camera, marker and timestamp attributes. Records time at
        which each image is received (secs since Epoch).
        
        """

        self.start_time = time.time()
        self.sim = sim
        self.cam = None
        self.markers = []
        self.est_markers = []
        self.end_time = None


    def set(self, sim = False, cam = None, markers = None, estimates = None):
        """ 
        sets:
            sim: (boolean) flag to indicate whether this was a simulation
            cam: (GL_Camera_Vals or Real_Camera_Vals) camera's key parameters 
            markers: (Marker or GL_Marker) fiducial marker object
            est_markers: (Marker) pipeline pose estimation values 

        """

        if sim:
            self.sim = sim
        if cam:
            self.cam = cam
        if markers:
            self.markers = markers
        if est_markers:
            self.est_markers = estimates


    def complete(self, failed = False):
        """ records time at which all values have been filled in """

        self.end_time = time.time()


    def time(self):
        """ returns time from instantiation to completion, in seconds """

        return self.end_time - self.start_time


    def reset_markers_and_time(self):
        """ prepares output for next pipeline loop """

        self.start_time = time.time()
        self.markers = []
        self.est_markers = []


    def get_est_Cs_flat_mm(self):
        """ 
        Returns estimated centres in a nx3 flat array of 3d vectors (useful for
        single marker). Note: posea always generates two estimates per
        est_marker.
        
        """

        eCs = np.zeros((len(self.est_markers)*2,3))
        for i, m in enumerate(self.est_markers): # any nr of markers
            for j, e in enumerate(m.get_C_mm()): # two centre estimates
                for k, c in enumerate(e):        # three coordinates
                    eCs[i*2+j,k] = c
        return eCs


    def get_est_Ns_flat_mm(self):
        """ 
        Returns estimated normals in a nx3 flat array of 3d vectors (useful for
        single marker). Note: posea always generates two estimates per
        est_marker.
        
        """

        enrms = np.zeros((len(self.est_markers)*2,3))
        for i, m in enumerate(self.est_markers): # any nr of markers
            for j, n in enumerate(m.get_N_mm()): # two normal estimates
                for k, c in enumerate(n):        # three coordinates
                    enrms[i*2+j,k] = c
        return enrms


    def get_data(self, stub= False, match= False, get= None):
        """
        This function is designed to facilitate the retrieval of data to produce
        plots as in the printer module, by returning data a dict whose keys are
        the names of the required classes of data, such as 'est. Cs' for
        estimated centres. 
        
        The array of vectors corresonding to each key is in chronological order
        by virtue of the same order of the outputs array. 

        The function checks whether the combination of parameters is
        contradictory and returns None if the data in the current output object
        is incomplete for the given data request.

        "get" specifies the required data classes as a list of ID strings.
        
        If "match" is set, the actual values are duplicated so that the arrays
        of actual values are as long as the arrays of estimates and each actual
        value has a corresonding estimated value at the same array index in the
        appropriate array. 
        
        If "stub" is set, the dict is returned with empty lists as values.  
        
        NB: this function does not take multiple marker scenes into account.

        """

        if stub:
            stub = {}
            for key in get:
                stub[key] = []
            return stub

        data = {}
        nr_eCs, nr_eNs, nr_Cs, nr_Ns = 0, 0, 0, 0
        recognised = 0

        if match and ('recognition' in get):
            self.logger.error('tried to retrieve recognition in matched mode')
            return None

        eCs = self.get_est_Cs_flat_mm()
        nr_eCs = len(eCs)
        C = self.markers[0].get_C_mm()
        nr_Cs = len(C)
        eNs = self.get_est_Ns_flat_mm()
        nr_eNs = len(eNs)
        N = self.markers[0].get_N_mm()
        nr_Ns = len(N)

        if 'est. Cs' in get:
            if nr_eCs:
                data['est. Cs'] = eCs
            elif match:
                return None
            else:
                data['est. Cs'] = []
            
        if 'actual Cs' in get:
            if match and nr_eCs and nr_Cs:
                data['actual Cs'] = np.tile(C, nr_eCs).reshape(nr_eCs, 3)
            elif match:
                return None
            elif nr_Cs:
                data['actual Cs'] = np.tile(C, nr_Cs).reshape(nr_Cs, 3)
            else:
                data['actual Cs'] = []

        if 'est. Ns' in get:
            if nr_eNs:
                data['est. Ns'] = eNs
            elif match:
                return None
            else:
                data['est. Ns'] = []
            
        if 'actual Ns' in get:
            if match and nr_eNs and nr_Ns:
                data['actual Ns'] = np.tile(N, nr_eNs).reshape(nr_eNs, 3)
            elif match:
                return None
            elif nr_Ns:
                data['actual Ns'] = np.tile(N, nr_Ns).reshape(nr_Ns, 3)
            else:
                data['actual Ns'] = []

        if 'recognition' in get:
            if (nr_eCs and nr_Cs):
                data['recognition'] = np.ones((1,1))
            elif nr_Cs:
                data['recognition'] = np.zeros((1,1))

        elif nr_eCs + nr_Cs + nr_eNs + nr_Ns == 0:
                return None
        
        return data
