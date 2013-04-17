#Milovision: A camera pose estimation programme
#
# Milovision: A camera pose estimation programme
# 
# Copyright (C) 2013 Joris Stork
# See LICENSE.txt
#
# pipeline.py
""" 
:synopsis:  Contains the Pipeline class. Instantiations are pose estimation
            pipelines consisting of one or more modules, from contour detection
            to marker identification (the latter is not yet implemented). 

.. moduleauthor:: Joris Stork <joris@wintermute.eu>

"""

# standard and third party libraries
import cv2
import numpy as np
import sys
import time
import copy
import multiprocessing
import logging
import Image

# milovision libraries
from pipeline_modules import ContourFinder
from pipeline_modules import EllipseFitter
from pipeline_modules import PoseEstimatorA
from simulator import GL_Simulator
from output import Pipeline_Output, Printer
from camera_values import Camera_Vals
from marker import Marker


class Pipeline(object):
    """ 
    The Pipeline class contains the main application loop and instantiates and
    runs the required image processing modules as well as the optional
    simulator.
    
    """


    def __init__(self, options = None):
        """ sets logger, verbosity, and other execution variables """

        self.logger = logging.getLogger('Pipeline')
        self.options = options
        self.logger.info('initialised')
        self.windows = []
        self.modules = []
        self.loops = 0
        self.single_img = False
        self.fwcam = None
        self.processes = []
        self.outputs = []
        self.new_output = False
        self.start = time.time()
        self.ellipses = None
        self.already_shutting_down = False


    def set_fwcam(self, fwcam):
        """ sets the pipeline's pydc1394 camera object """

        self.fwcam = fwcam


    def set_image(self, image):
        """ loads a single image from disk """

        self.orig = np.copy(image)
        self.canvas = np.copy(self.orig)
        self.single_img = True


    def stop(self):
        """
        Sets the stop variables that trigger pipeline shutdown. Sends a stop
        message to the simulator if present, and waits for the simulator process
        to halt.
        
        """

        self.end = time.time()
        self.running = False
        self.logger.info('stopping pipeline')
        if self.options.simulate is not None:
            self.logger.info('waiting for simulator')
            for process in self.processes:
                self.q2sim.put('stop')
                process.join()
            self.logger.info('simulator complete')


    def cleanup(self):
        """ closes any OpenCV windows and/or camera to enable a clean exit """

        for window in self.windows:
            cv2.destroyWindow(window) # opencv bug: only closes windows at exit
        if hasattr(self, 'fwcam'):
            if self.fwcam:
                self.fwcam.stop()
        self.logger.info('cleanup completed')

    
    def shutdown(self):
        """ main exit routine with logging tasks; runs printer if required """

        self.stop()
        if self.already_shutting_down:
            self.logger.error('multiple shutdown attempts')
            sys.exit(0)
        self.already_shutting_down = True
        duration = self.end - self.start
        if self.modules:
            self.logger.info('processed %d images' % self.loops)
            self.logger.info('avg rate: %f fps' % (self.loops / duration))
        else:
            self.logger.info('loops: %d' % self.loops)
            self.logger.info('avg rate: %f loops /sec' % (self.loops / duration))
        avcts = 0.0
        avels = 0.0
        avmels = 0.0
        if self.modules:
            if (len(self.modules) > 0) and self.loops > 0:
                avcts = self.modules[0].nr_conts / self.loops
                self.modules[0].logger.info('avg contours /img: %f' % avcts)
            if (len(self.modules) > 1) and self.loops > 0:
                avels = self.modules[1].nr_ellipses / (self.loops * 1.0)
                avmels = self.modules[1].nr_candidates / (self.loops * 1.0)
                self.modules[1].logger.info('pre-filter ellipses /img: %f' % avels)
                self.modules[1].logger.info('post-filter ellipses /img: %f' % avmels)
            if len(self.modules) > 2:
                msg = 'used lopt1 %d times' % self.modules[2].nrlopt1
                self.modules[2].logger.info(msg)
                msg = 'used lopt2 %d times' % self.modules[2].nrlopt2
                self.modules[2].logger.info(msg)
                msg = 'used lopt3 %d times' % self.modules[2].nrlopt3
                self.modules[2].logger.info(msg)
        self.cleanup()
        printer = Printer(pipe = self)
        printer.final(outputs = self.outputs)
        self.logger.info('shutdown completed')
        sys.exit(0)


    def run(self):
        """ 
        Main application function. Starts image stream from real or simulated
        camera (or loads a single image); initialises any pipeline modules; and
        then enters the main pipeline processing loop. Once in the loop the
        pipeline runs until a shutdown flag is set. The message queue from the
        simulator, if there is one, is checked on each loop iteration for image
        data and synchronisation messages (such as a shutdown message).
        
        """

        self.running = True
        if self.fwcam and not self.single_img:
            self.fwcam.start(interactive = True)
            time.sleep(1)
            self.orig = np.copy(np.asarray(self.fwcam.current_image))
            self.canv = np.copy(self.orig)
            self.init_output = Pipeline_Output(sim=False)
            self.init_output.cam = Camera_Vals(camera_id = 'chameleon1')
            self.init_output.markers.append(Marker(cam=self.init_output.cam))
        elif self.options.simulate is not None:
            self.q2sim = multiprocessing.Queue()
            self.q2pipe = multiprocessing.Queue()
            queues = self.q2sim, self.q2pipe
            args = queues, self.options
            process = multiprocessing.Process(name='child', target=GL_Simulator, args=args)
            self.processes.append(process)
            process.start()
            self.init_output = Pipeline_Output(sim = True)
            self.q2sim.put(copy.deepcopy(self.init_output))
            incoming = self.q2pipe.get()
            if 'stop' in incoming:
                self.shutdown()
            elif 'simulglob' in incoming:
                _, self.orig, output = incoming
                self.outputs.append(copy.deepcopy(output))
                self.init_output.cam = self.outputs[0].cam

        m = []
        if self.options.nr_modules == 0:
            self.logger.info('running an empty pipeline')
        else:
            if self.options.nr_modules >=1:
                self.modules.append(ContourFinder(pipeline = self))
            if self.options.nr_modules >=2:
                self.modules.append(EllipseFitter(pipeline = self))
            if self.options.nr_modules >=3:
                self.modules.append(PoseEstimatorA(pipeline = self))
        self.logger.info('running with %d modules' % self.options.nr_modules)

        if self.options.windows:
            for module in self.modules:
                if not (module.__class__.__name__ == 'PoseEstimatorA'):
                    self.windows.append(module.__class__.__name__)

        if self.single_img:
            for module in self.modules:
                module.run()
                if self.options.windows:
                    cv2.imshow(module.__class__.__name__, self.canv)
                    cv2.waitKey(2)
                    time.sleep(5)
                self.shutdown()

        while self.running:
            if self.fwcam:
                self.orig = np.copy(np.asarray(self.fwcam.current_image))
                if self.options.windows:
                    cv2.imshow("original", self.orig)
            elif (self.options.simulate is not None) and self.outputs[-1].end_time:
                incoming = self.q2pipe.get()
                if 'stop' in incoming:
                    self.running = False
                    continue
                elif 'simulglob' in incoming:
                    _, self.orig, output = incoming
                    self.outputs.append(copy.deepcopy(output))
                    self.new_output = True
                else:
                    self.logger.error('unknown in queue: \'%s\''% incoming)
                    self.shutdown()
            self.canv = np.copy(self.orig)
            for module in self.modules:
                module.run()
                classname = module.__class__.__name__
                if not (self.options.windows and classname == 'PoseEstimatorA'):
                    cv2.imshow(module.__class__.__name__, self.canv)
            self.loops += 1
            self.outputs[-1].complete()
            if self.ellipses:
                self.ellipses = None
            if self.options.windows:
                cv2.waitKey(2)
            if time.time() - self.start >= self.options.simtime:
                self.running = False
        self.shutdown()
