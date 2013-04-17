#!/usr/bin/env python
#
# Milovision: A camera pose estimation programme
# 
# Copyright (C) 2013 Joris Stork
# See LICENSE.txt
#
# printer.py

"""
:synopsis: Produces tables and plots from pipeline data, to aid in analysis 

.. moduleauthor:: Joris Stork <joris@wintermute.eu>

"""

# standard library and third party packages
import string
import numpy as np
import matplotlib.pyplot as plt
import logging
from mpl_toolkits.mplot3d import axes3d
import pickle
import time

# milovision modules
from output import Pipeline_Output

class Printer(object):
    """ 
    Contains: convenience functions to extract relevant data for plots and
    stats; plotting and statistics generating functions; and a main routine in
    "final" that determines the kinds of output to be generated.
    
    """

    def __init__(self, pipe = None):
        """ sets logger and current pipeline object """
        
        self.logger = logging.getLogger('Printer')
        self.pipe = pipe


    def in_loop(self, output):
        """ for in-loop printouts of pipelina data (not at exit) """

        pass


    def get_angle(self, a, b):
        """ return (smallest? check this) angle between vectors a and b """

        return np.arccos(np.dot(a/np.linalg.norm(a),b/np.linalg.norm(b)))


    def get_Cs(self, outputs, indices = None):
        """ returns actual marker centres as numpy array """

        if indices:
            Cs = np.zeros((len(indices), 3))
            o = [] 
            for index in indices:
                o.append(outputs[index])
            outputs = o
        else:
            Cs = np.zeros((len(outputs), 3))
        for i, output in enumerate(outputs):
            Cs[i] = output.markers.get_C_mm()
        return Cs


    def get_Ns(self, outputs, indices = None):
        """ returns actual marker normals as numpy array """

        if indices:
            Ns = np.zeros((len(indices), 3))
            o = [] 
            for index in indices:
                o.append(outputs[index])
            outputs = o
        else:
            Ns = np.zeros((len(outputs), 3))
        for i, output in enumerate(outputs):
            Ns[i] = output.markers.get_normal_mm()
        return Ns


    def get_est_Cs(self, outputs):
        """ returns estimated marker centres as numpy array """

        est_Cs = []
        for i, output in enumerate(outputs):
            ecs = output.get_est_Cs_flat_mm()
            if ecs.any():
                for ec in ecs:
                    est_Cs.append(ec)
        return np.array(est_Cs)


    def get_est_Ns(self, outputs):
        """ returns estimated marker normals as numpy array """

        est_Ns = []
        for i, output in enumerate(outputs):
            ens = output.get_est_Ns_flat_mm()
            if ens.any():
                for en in ens:
                    est_Ns.append(en)
        return np.array(est_Ns)


    def get_times(self, outputs):
        """ returns ordered array of times elapsed per output """

        times = np.zeros((len(outputs), ))
        for i, output in enumerate(outputs):
            times[i] = output.time()
        return times


    def get_data(self, outputs, get= None, match= False):
        """ 
        Collects data of the required classes for all non-empty output objects
        into a single dict with nx3 array values. 
        NB: with the 'match' flag set the actual values are repeated as many
        times as there are estimates per output object.
        
        """

        o = outputs[0]
        temp= o.get_data(stub=True, get= get, match= match)

        nr_vectors = {key:0 for key in get}

        for o in outputs:
            batch = o.get_data(get= get, match= match)
            if batch == None:
                continue
            for key, value in batch.items():
                temp[key].append(value)
                nr_vectors[key] += len(value)

        data = {}
        for key, value in temp.items():
            data[key] = np.zeros((nr_vectors[key],3))
            k = 0
            for output_vector_set in value:
                for vector in output_vector_set:
                    data[key][k] = vector
                    k += 1
        return data


    def unwrap_cfg(self, options, setting):
        """ converts options to a dict of config key-value pairs """
    
        cfg = {}
        for key, value in setting.items():
            if value is not None:
                cfg[key] = options[key][value]
            else:
                cfg[key] = None
        return cfg['xmodes'], cfg['ymodes'], cfg['data_cfgs']


    def histogram(self, outputs, options, units, setting):
        """ 
        Produces histograms for the given outputs, tailored to the classes of
        data selected. First determines the bins, then populates these, then
        plots the result using Matplotlib.
        'options' determines the types of data available.
        'setting' determines which data types are required
        'units' are the units of measurement strings corresponding to the
        respective data classes. these are inserted into the histogram legends.
        
        """

        kCs, kNs, keCs, krs = 'actual Cs', 'actual Ns', 'est. Cs','recognition'
        xmode, ymode, data_cfg = self.unwrap_cfg(options, setting)
        xmode_unit, ymode_unit = units[xmode], units[ymode]
        self.logger.info('creating %s against %s histogram' % (ymode,xmode))
        match = (data_cfg == 'matched')
        nr_bins = 100

        plt_data = {xmode:np.zeros((nr_bins,)), ymode:np.zeros((nr_bins,))}

        if data_cfg == 'recognition':
            get = kCs, keCs, kNs, krs
        if data_cfg == 'matched':
            get = kCs, keCs, kNs
        data = self.get_data(outputs, get= get, match= match)

        Y = np.zeros((data[kCs].shape[0],))
        if ymode == 'mean error':
            for i, (C, eC) in enumerate(zip(data[kCs],data[keCs])):
                dif = C - eC
                Y[i] = np.linalg.norm(dif)
        elif ymode == 'recognition rate':
            Y = data[krs].flatten()

        X = np.zeros(data[kCs].shape[0])

        if xmode == 'angle':
            for i, (C, N) in enumerate(zip(data[kCs],data[kNs])):
                X[i] = self.get_angle(-C,N)

        elif xmode == 'distance to cam':
            for i, C in enumerate(data[kCs]):
                X[i] = np.linalg.norm(C)

        Xmin, Xmax = np.min(X), np.max(X)
        bin_bounds, step = np.linspace(Xmin, Xmax, nr_bins+1, retstep= True)
        plt_data[xmode] = bin_bounds[:-1] # bin boundary values
        X_bin_indices = np.digitize(X, plt_data[xmode])
        bincount = np.zeros((nr_bins,))

        bins = [[] for x in xrange(nr_bins)]
        for i, y in enumerate(Y):
            plt_data[ymode][X_bin_indices[i]-1] += y
            bincount[X_bin_indices[i]-1] += 1
            bins[X_bin_indices[i]-1].append(y)
        std = np.zeros((nr_bins,))
        for i in xrange(nr_bins):
            if bins[i]:
                std[i] = np.std(bins[i])
            
        for i, total in enumerate(plt_data[ymode]):
            if (1. * total * bincount[i]) == 0:
                continue
            plt_data[ymode][i] = total / bincount[i]

        fig = plt.figure()
        ax = plt.subplot(111)
        rwidth = step 
        if ymode == 'recognition rate':
            rects = ax.bar(plt_data[xmode], plt_data[ymode], rwidth, color='b')
        else:
            rects = ax.bar(plt_data[xmode], plt_data[ymode], rwidth, color='b', yerr=std, ecolor='r')

        ax.set_title('%s against %s' % (ymode, xmode))
        ax.set_xlabel(xmode+xmode_unit)
        ax.set_ylabel(ymode+ymode_unit)
        ax.grid(True)
        if data_cfg == 'arecognition':
            for rect in rects:
                height = rect.get_height()
                ax.text(rect.get_x()+rect.get_width()/2., 1.05*height, '%d'%int(height), ha= 'center', va= 'bottom')

        plt.show()


    def scatter(self, outputs, options, units, setting):
        """ 
        Plots from two equal length 1D arrays of scalars. Uses Matplotlib.
        'options' determines the types of data available.
        'setting' determines which data types are required
        'units' are the units of measurement strings corresponding to the
        respective data classes. these are inserted into the histogram legends.
        
        """

        xmode, ymode, data_cfg = self.unwrap_cfg(options, setting)
        xmode_unit, ymode_unit = units[xmode], units[ymode]

        self.logger.info('creating 2d %s vs %s scatterplot' % (xmode,ymode))
        get = 'actual Cs', 'est. Cs'
        match = (data_cfg == 'matched')
        data = self.get_data(outputs, get= get, match= match)
        keys = data.keys()
        fig = plt.figure()
        ax = plt.subplot(111)
        ax.scatter(data[keys[0]][:,2], data[keys[1]][:,2])
        ax.set_xlabel(keys[0]+' '+xmode+xmode_unit)
        ax.set_ylabel(keys[1]+' '+ymode+ymode_unit)
        ax.grid(True)
        self.logger.info('displaying point cloud')
        plt.show()


    def point_cloud(self, outputs, options, units, setting):
        """ 
        Plots sets of 3d points, each with a different shape and colour. Uses
        Matplotlib.
        'options' determines the types of data available.
        'setting' determines which data types are required
        'units' are the units of measurement strings corresponding to the
        respective data classes. these are inserted into the histogram legends.
        
        """

        self.logger.info('creating point cloud')
        _, _, data_cfg = self.unwrap_cfg(options, setting)
        get = 'actual Cs', 'est. Cs'
        match = (data_cfg == 'matched')
        data = self.get_data(outputs, match= match, get= get)
        fig = plt.figure()
        ax = fig.gca(projection='3d')
        ax.scatter3D(0, 0, 0, c = 'm', marker = 'p')
        ax.grid(True)
        ax.plot([],[],[],'p',c='m', label='Camera')
        cl = 'g', 'b', 'r'      # colours
        m = '+', 'o', '^'       # plot markers
        s = '1', '4', '1'       # marker sizes
        for i, (key,v) in enumerate(data.items()):
            ax.scatter3D(v[:,0],v[:,1],v[:,2], c = cl[i], marker = m[i])
            ax.plot([],[],[],m[i],c=cl[i], label=key)
        ax.set_xlabel('x')
        ax.set_ylabel('y')
        ax.set_zlabel('z')
        ax.legend()
        self.logger.info('displaying point cloud')
        plt.show()


    def print_stats(self, outputs, options, units, setting):
        """   
        Prints stats from the selected data, as plain text to stdout.
        'options' determines the types of data available.
        'setting' determines which data types are required
        'units' are the units of measurement strings corresponding to the
        respective data classes. these are inserted into the histogram legends.
        
        """

        _, _, data_cfg = self.unwrap_cfg(options, setting)
        get = 'actual Cs', 'est. Cs', 'actual Ns', 'est. Ns'
        match = (data_cfg == 'matched')
        data = self.get_data(outputs, get= get, match = match)
        nr_ests = data['est. Cs'].shape[0]
        normal_angles = np.zeros((nr_ests,))
        incidence_angles = np.zeros((nr_ests,))

        if self.pipe.options.simulate:

            dist = np.zeros((nr_ests,))
            dif = np.zeros((nr_ests, 3))
            dist_to_cam = np.zeros((nr_ests,))
            for i in xrange(nr_ests):
                dif[i] = data['actual Cs'][i] - data['est. Cs'][i]
                dist[i] = np.linalg.norm(dif[i])
                dist_to_cam[i] = np.linalg.norm(data['actual Cs'][i])

            print '\n --- simulation data ---'
            print '\n focal length: ',outputs[-1].cam.get_focal_mm()
            for i in xrange(len(data['actual Cs'])):
                ci = data['actual Cs'][i]
                ni = data['actual Ns'][i]
                eni = data['est. Ns'][i]
                normal_angles[i] = self.get_angle(ni,eni)
                incidence_angles[i] = self.get_angle(ni,-ci)

            print '\n --- simulation stats ---'
            print '\nrecorded on: ',time.ctime()
            print '\nnr. poses generated: ',len(outputs)
            print '\nnr. estimates: ',nr_ests
            print '\nmin depth: ',np.min(data['actual Cs'][:,2])
            print '\nmax depth: ',np.max(data['actual Cs'][:,2])
            print '\n-- distance (C-estC)(mm):'
            print 'max.: ',np.max(dist)
            print 'min.: ',np.min(dist)
            print 'mean: ',np.mean(dist)
            print 'st. dev.: ',np.std(dist)
            print '\n -- difference (C-estC)(mm):'
            print 'mean:\n',np.mean(dif, axis=0)
            print '\n--angle (norm, estnorm)(deg):'
            print 'max.: ',np.degrees(np.max(normal_angles))
            print 'min.: ',np.degrees(np.min(normal_angles))
            print 'mean: ',np.degrees(np.mean(normal_angles))
            print 'st. dev.: ',np.degrees(np.std(normal_angles))
            print '\n--angle of incidence(deg):'
            print 'max.: ',np.degrees(np.max(incidence_angles))
            print 'min.: ',np.degrees(np.min(incidence_angles))
            print 'mean: ',np.degrees(np.mean(incidence_angles))
            print 'st.dev.: ',np.degrees(np.std(incidence_angles))
            print '\n--distance (marker-cam)(mm):'
            print 'max.: ',np.max(dist_to_cam)
            print 'min.: ',np.min(dist_to_cam)
            print 'mean: ',np.mean(dist_to_cam)
            print 'st.dev.: ',np.std(dist_to_cam)
            print '\n'

        else:
            print '\n-- printout not configured --\n'



    def final(self, outputs = None):
        """ 
        Printer's main function.
        Writes all pipeline outputs to a pickle file.
        Reads pickled outputs from file if required.
        Then defines plotting options and available data classes. Not very
        elegant, but this puts all options and the code to choose from them in
        one place. The options and the setting dicts are pretty
        self-explanatory.
        
        """

        options = {}
        units = {}
        settings = []
        if not self.pipe.options.simulate:
            pickle.dump(outputs, open('output/outputs_fwcam.pickle', 'wb'))
            self.logger.info('outputs saved to disk')
            data_cfg = 'estCs'
            if not outputs:
                return
        else:
            if not outputs:
                outputs = pickle.load(open('output/outputs.pickle', 'rb'))
                self.logger.info('outputs loaded from disk')
            else:
                pickle.dump(outputs, open('output/outputs.pickle', 'wb'))
                self.logger.info('outputs saved to disk')

            options['xmodes'] = 'distance to cam','angle', 'depth'
            options['ymodes'] = 'mean error','recognition rate', 'depth'
            options['data_cfgs'] = 'matched','recognition' 
            units['distance to cam'] = ' (mm)'
            units['depth'] = ' (mm)'
            units['mean error'] = ' (mm)'
            units['recognition rate'] = ''
            units['angle'] = ' (rad)'

            setting = {'xmodes':None,'ymodes':None,'data_cfgs':0}
            self.print_stats(outputs, options, units, setting)
            self.point_cloud(outputs, options, units, setting)

            setting = {'xmodes':2,'ymodes':2,'data_cfgs':0}
            self.scatter(outputs, options, units, setting)

            settings.append({'xmodes':0,'ymodes':0,'data_cfgs':0})
            settings.append({'xmodes':1,'ymodes':0,'data_cfgs':0})
            settings.append({'xmodes':0,'ymodes':1,'data_cfgs':1})
            settings.append({'xmodes':1,'ymodes':1,'data_cfgs':1})
            for setting in settings:
                self.histogram(outputs, options, units, setting)
