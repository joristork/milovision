#!/usr/bin/env python
# encoding: utf-8
#
# This file is part of pydc1394.
#
# pydc1394 is free software: you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# pydc1394 is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with pydc1394.  If not, see
# <http://www.gnu.org/licenses/>.
#
# Copyright (C) 2009, 2010 by Holger Rapp <HolgerRapp@gmx.net>
# and the pydc1394 contributors (see README File)


from _dc1394core import *
from _dc1394core import _dll
from ctypes import *


from numpy import fromstring, ndarray
from threading import *

from Queue import Queue, Full

from _mode import _mode_map, create_mode


__all__ = ["DC1394Library", "Camera", "SynchronizedCams",
           "DC1394Error", "CameraError"]

class DC1394Error(Exception):
    """Base class for Exceptions"""
    pass

class CameraError(DC1394Error, RuntimeError):
    pass


class DC1394Library(object):
    """
    This wraps the dc1394 library object which is a nuisance to have
    around. This is bad design on behalve of DC1394. Oh well...  This
    object must stay valid until all cameras are closed
    But then use it well: it not only opens the library, collects
    a reference to the library and the camera list.
    """
    def __init__( self ):
        # we cache the dll, so it gets not deleted before we cleanup
        self._dll = _dll
        self._h = _dll.dc1394_new()

    def __del__(self):
        self.close()

    @property
    def h(self):
        "The handle to the library context."
        return self._h

    ###################################################################
    # Functions:
    ###################################################################

    def close( self ):
        """
        Close the Libraray permanently. All camera handles created with it
        are invalidated by this.
        """
        if self._h is not None:
            self._dll.dc1394_free( self._h )
        self._h = None

    def enumerate_cameras( self ):
        """
        Enumerate the cameras currently attached to the bus.

        :returns: a list of dictionaries with the following keys per camera:

            * unit
            * guid
            * vendor
            * model
        """
        l = POINTER(camera_list_t)()

        _dll.dc1394_camera_enumerate(self.h, byref(l))

        clist = []
        for i in xrange(l.contents.num):
            ids = l.contents.ids[i]
            #we can be nice to the users, providing some more
            #than mere GUID and unitIDs
            #also, if this fails, we have a problem:
            cam = self._dll.dc1394_camera_new(self.h, ids.guid)

            #it seems not all cameras have these fields:
            vendor = cam.contents.vendor if cam.contents.vendor else "unknown"
            model = cam.contents.model if cam.contents.model else "unknown"

            clist.append(
                { "unit": ids.unit,
                    # For what do we need this L anyway?!?!
                  #"guid": hex(ids.guid)[2:].strip("L"),
                  "guid": ids.guid,
                  "vendor":	vendor,
                  "model":	model,
                }
            )

            self._dll.dc1394_camera_free(cam)
        _dll.dc1394_camera_free_list(l)

        return clist


class Image(ndarray):
    """
    This class is a image returned by the camera. It is basically a
    numpy array with some additional information (like timestamps).

    It is not based on the video_frame structure of the dc1394, but rather
    augments the information from numpy through information of the acquisition
    of this image.
    """
    @property
    def position(self):
        "ROI position (offset)"
        return self._position
    @property
    def packet_size(self):
        "The size of a datapacket in bytes."
        return self._packet_size
    @property
    def packets_per_frame(self):
        "Number of packets per frame."
        return self._packets_per_frame
    @property
    def timestamp(self):
        "The IEEE Bustime when the picture was acquired (microseconds)"
        return self._timestamp
    @property
    def frames_behind(self):
        """
        The number of frames in the ring buffer that are yet to be accessed
        by the user
        """
        return self._frames_behind
    @property
    def id(self):
        "the frame position in the ring buffer"
        return self._id

class _CamAcquisitonThread(Thread):
    def __init__(self,cam, condition ):
        """
        This class is created and launched whenever a camera is start()ed.
        It continously acquires the pictures from the camera and sets a
        condition to inform other threads of the arrival of a new picture
        """
        Thread.__init__(self)

        self._cam = cam
        self._should_abort = False

        self._last_frame = None
        self._condition = condition

        #create a lock object from the threading module; see LockType.__doc__
        self._abortLock = Lock()

        self.start()

    def abort(self):
        self._abortLock.acquire()
        self._should_abort = True
        self._abortLock.release()

    def run(self):
        """
        Core function which contains the acquisition loop
        """

        while 1:
            self._abortLock.acquire()
            sa = self._should_abort
            self._abortLock.release()

            if sa:
                break

            if self._last_frame:
                self._cam._dll.dc1394_capture_enqueue(
                    self._cam._cam, self._last_frame
                )

            #the actual image acquisition:
            frame = POINTER(video_frame_t)()
            self._cam._dll.dc1394_capture_dequeue(self._cam._cam,
                CAPTURE_POLICY_WAIT, byref(frame)
            );

            #get the buffer from the frame (this is part of the ring buffer):
            Dtype = c_char*frame.contents.image_bytes
            buf = Dtype.from_address(frame.contents.image)

            self._last_frame = frame

            self._condition.acquire()
            #generate an Image class from the buffer:
            img = fromstring(buf, dtype=self._cam.mode.dtype).reshape(
                self._cam.mode.shape
            ).view(Image)

            img._position, img._packet_size, img._packets_per_frame, \
                img._timestamp, img._frames_behind, img._id = \
                frame.contents.position, frame.contents.packet_size, \
                frame.contents.packets_per_frame, frame.contents.timestamp, \
                frame.contents.frames_behind,frame.contents.id
            self._cam._current_img = img

            # is the camera streaming to a queue?
            if self._cam._queue:
                # Will throw an exception if you're to slow while processing
                self._cam._queue.put_nowait(img)

            self._condition.notifyAll()
            self._condition.release()

        # Return the last frame
        if self._last_frame:
            self._cam._dll.dc1394_capture_enqueue(
                self._cam._cam, self._last_frame
        )
        self._last_frame = None


##################################
# Camera Property implementation #
##################################
class CameraProperty(object):
    """This class implements a simple Property of the camera"""

    def __init__( self, cam, name, id, absolute_capable ):
        self._id = id
        self._name = name
        self._absolute_capable = absolute_capable
        self._dll = cam._dll
        self._cam = cam

    def val():
        doc = "The current value of this property"
        def fget(self):
            if self._name == "white_balance":
                #white has its own call since it returns 2 values
                blue = c_uint32()
                red = c_uint32()
                self._dll.dc1394_feature_whitebalance_get_value(
                    self._cam._cam, byref(blue), byref(red)
                )
                return (blue.value, red.value)

            if self._absolute_capable:
                val = c_float()
                self._dll.dc1394_feature_get_absolute_value(
                    self._cam._cam, self._id, byref(val)
                )

                if self._name == "shutter" :
                    # We want shutter in ms -> if it is absolute capable.
                    val.value *= 1000.
            else:
                val = c_uint32()
                self._dll.dc1394_feature_get_value(
                    self._cam._cam, self._id, byref(val)
                )
            return val.value

        def fset(self, value):
            if self._name == "white_balance":
                #white has its own call since it returns 2 values
                blue, red = value
                self._dll.dc1394_feature_whitebalance_set_value(
                    self._cam._cam, blue, red
                )
            else:
                if self._absolute_capable:
                    val = float(value)
                    # We want shutter in ms
                    if self._name == "shutter":
                        val /= 1000.
                    self._dll.dc1394_feature_set_absolute_value(
                        self._cam._cam, self._id, val
                    )
                else:
                    val = int(value)
                    self._dll.dc1394_feature_set_value(
                        self._cam._cam, self._id, val
                    )
        return locals()
    val = property(**val())

    @property
    def range(self):
        "The RO foo property."
        if self._absolute_capable:
            min, max = c_float(), c_float()
            self._dll.dc1394_feature_get_absolute_boundaries( self._cam._cam,\
                                                self._id, byref(min),byref(max))
            # We want shutter in ms
            if self._name == "shutter":
                min.value *=1000
                max.value *=1000
        else:
            min, max = c_uint32(), c_uint32()
            self._dll.dc1394_feature_get_boundaries(
                self._cam._cam, self._id, byref(min),byref(max)
            )
        return (min.value,max.value)

    @property
    def can_be_disabled(self):
        "Can this property be disabled"
        k = bool_t()
        self._dll.dc1394_feature_is_switchable(self._cam._cam,
                self._id, byref(k)
        )
        return bool(k.value)

    def on():
        doc = """\
        Toggle this feature on and off;
        For the trigger this means the external trigger ON/OFF"""

        def fget(self):
            k = bool_t()
            if self._name.lower() == "trigger":
                self._dll.dc1394_external_trigger_get_power(
                    self._cam._cam, byref(k)
                )
            else:
                self._dll.dc1394_feature_get_power(self._cam._cam, self._id,
                   byref(k)
                )
            return bool(k.value)

        def fset(self, value):
            k = bool(value)
            if self._name.lower() == "trigger":
                self._dll.dc1394_external_trigger_set_power(self._cam._cam, k)
            else :
                self._dll.dc1394_feature_set_power( self._cam._cam, self._id, k)
        return locals()
    on = property(**on())

    @property
    def pos_modes(self):
        "The possible control modes for this feature (auto,manual,...)"

        if self._name.lower() == "trigger":
            #we need a trick:
            finfo = feature_info_t()
            finfo.id = self._id
            _dll.dc1394_feature_get( self._cam._cam,  byref(finfo) )
            modes = finfo.trigger_modes

            return [ trigger_mode_vals[ modes.modes[i]] for
                    i in xrange(modes.num)
            ]
        modes = feature_modes_t()
        _dll.dc1394_feature_get_modes(self._cam._cam, self._id, byref(modes))
        return [ feature_mode_vals[modes.modes[i]] for i in xrange(modes.num) ]

    def mode():
        """The current control mode this feature is running in.

        For the trigger it shows the trigger modes (from the dc1394
        website):
        mode 0:     Exposure starts with a falling edge and stops when
                    the the exposure specified by the SHUTTER feature
                    is elapsed.
        mode 1:     Exposure starts with a falling edge and stops with
                    the next rising edge.
        mode 2:     The camera starts the exposure at the first falling
                    edge and stops the integration at the nth falling
                    edge. The parameter n is a prameter of the trigger
                    that can be set with camera.trigger.val parameter.
        mode 3:     This is an internal trigger mode. The trigger is
                    generated every n*(period of fastest framerate).
                    Once again, the parameter n can be set with
                    camera.trigger.val.
        mode 4:     A multiple exposure mode. N exposures are performed
                    each time a falling edge is observed on the trigger
                    signal. Each exposure is as long as defined by the
                    SHUTTER (camera.shutter) feature.
        mode 5:     Another multiple exposure mode. Same as Mode 4
                    except that the exposure is is defined by the
                    length of the trigger pulse instead of the SHUTTER
                    feature.

        mode 14 and 15: vendor specified trigger mode.
            """
        def fget(self):
            if self._name.lower() == "trigger":
                mode = trigger_mode_t()
                _dll.dc1394_external_trigger_get_mode(
                    self._cam._cam, byref(mode)
                )
                return trigger_mode_vals[ mode.value ]

            mode = feature_mode_t()
            _dll.dc1394_feature_get_mode(self._cam._cam, self._id, byref(mode))
            return feature_mode_vals[mode.value]

        def fset(self, value):
            if value in self.pos_modes:
                if self._name.lower() == "trigger":
                    key = trigger_mode_codes[ value ]
                    _dll.dc1394_external_trigger_set_mode(self._cam._cam, key)
                else:
                    key = feature_mode_codes[ value ]
                    _dll.dc1394_feature_set_mode(self._cam._cam, self._id,key )
            else:
                    print "Invalid %s mode: %s" %(self._name, value)
        return locals()
    mode = property(**mode())

    def polarity_capable(self):
        """
        Is this feature polarity capable?  This is valid for the trigger
        only.
        """
        finfo = feature_info_t()
        finfo.id = self._id
        _dll.dc1394_feature_get( self._cam._cam,  byref(finfo) )
        #polarity_capable is an bool_t = int field:
        return bool( finfo.polarity_capable )

    def polarity():
        doc = """The polarity of the external trigger. If the trigger
                has polarity (camera.trigger.polarity_capable == True),
                then it has two possible values. These are returned by:
                camera.trigger.pos_polarities.
                """
        def fget(self):
            pol = trigger_polarity_t()
            _dll.dc1394_external_trigger_get_polarity(self._cam._cam,
                byref(pol)
            )
            if trigger_polarity_vals.has_key( pol.value ):
                return trigger_polarity_vals[ pol.value ]
            else :
                return pol.value

        def fset(self, pol):
            if self.polarity_capable:
                if trigger_polarity_codes.has_key( pol ):
                    key = trigger_polarity_codes[ pol ]
                    _dll.dc1394_external_trigger_set_polarity(
                        self._cam._cam, key
                    )
                else:
                    print "Invalid external trigger polarity: %s" %pol
        return locals()
    polarity = property( **polarity())

    def pos_polarities(self):
        return trigger_polarity_codes.keys()

    def source():
        doc = "Actual source of the external trigger"
        def fget(self):
            source = trigger_source_t()
            _dll.dc1394_external_trigger_get_source(self._cam._cam,
                byref(source)
            )
            return trigger_source_vals[ source.value ]

        def fset(self, source):
            if trigger_source_codes.has_key( source ):
                key = trigger_source_codes[ source ]
                _dll.dc1394_external_trigger_set_source(self._cam._cam, key)
            else:
                print "Invalid external trigger source: %s" %source
        return locals()
    source = property( **source())

    def pos_sources(self):
        """ List the possible external trigger sources of the camera"""
        src = trigger_sources_t()
        _dll.dc1394_external_trigger_get_supported_sources(self._cam._cam,
            byref(src)
        )
        return [ trigger_source_vals[src.sources[i]] for i in xrange(src.num) ]

    def software_trigger():
        doc = "Set and get the software trigger (active or not)."
        def fget(self):
            res = switch_t()
            _dll.dc1394_software_trigger_get_power(self._cam._cam, byref(res))
            return bool( res.value )
        def fset(self, value):
            k = bool(value)
            _dll.dc1394_software_trigger_set_power(self._cam._cam, k)
        return locals()
    software_trigger = property( **software_trigger() )



class Camera(object):
    """
    This class represents a IEEE1394 Camera on the BUS. It currently
    supports all features of the cameras except white balancing.

    You can pass all features the camera supports as additional arguments
    to this classes constructor.  For example: shutter = 7.4, gain = 8

    The cameras pictures can be accessed in two ways. Either way, use
    start() to beginn the capture.  If you are always interested in the
    latest picture use the new_image Condition, wait for it, then use
    cam.current_image for your processing. This mode is called interactive
    because it is used in live displays.  An alternative way is to use
    shot() which gurantees to deliver all pictures the camera acquires
    in the correct order. Note though that you have to process these
    pictures with a certain speed, otherwise the caching queue will
    overrun. This mode is called serial. Note that you can theoretically
    also use the first acquisition mode here, but this seldom makes
    sense since you need a processing of the pictures anyway.

    :arg lib:        the library to open the camera for
    :type lib:       :class:`~DC1394Library`
    :arg guid:       GUID of this camera. Can be a hexstring or the integer
                     value
    :arg mode:       acquisition mode, e.g. (640, 480, "Y8"). If you pass None,
                     the current mode is kept. One can also use a string, such
                     as 'FORMAT7_0'
    :type mode:      :class:`tuple`, :class:`string` or :const:`None`
    :arg framerate:  desired framerate, if you pass None, the current camera
                     setting is kept
    :type framerate: :class:`float` or :const:`None`
    :arg isospeed:   desired isospeed, you might want to use 800 if your bus
                     supports it
    :type isospeed:  :class:`int`
    """

    def __init__( self, lib, guid, mode = None,
                 framerate = None, isospeed = 400, **feat):
        self._lib = lib
        if isinstance(guid,basestring):
            guid = int(guid,16)

        self._guid = guid
        self._cam = None
        #it is the same as _dll anyway...
        self._dll = lib._dll

        self._running = False
        self._running_lock = Lock()

        # For image acquisition
        self._new_image = Condition()
        self._current_img = None
        self._worker = None

        self.open()

        try:
            # Gather some informations about this camera
            # Will also set the properties accordingly
            self._all_features = self.__get_all_features()
            self._all_modes = self.__get_supported_modes()

            # Set all features to manual (if possible)
            for f in self._all_features:
                if 'manual' in self.__getattribute__(f).pos_modes:
                    self.__getattribute__(f).mode = 'manual'

            # Set acquisition mode and framerate, if no mode is requested,
            # we set a standard mode.
            self.mode = tuple(mode) if mode is not None else self.modes[0]

            #set the framerate:
            self.fps = self.mode.framerates[-1]

            try:
                self.framerate.mode = "auto"
            except AttributeError:
                pass # Feature not around, so what?

            # Set isospeed
            if isospeed :
                # If the speed is >= 800, set other operation mode
                #this is done automatically by the isospeed setting
                # self._operation_mode = "legacy" if isospeed < 800 else "1394b"
                self.isospeed = isospeed

            # Set other parameters
            for n,v in feat.items():
                if v is None:
                    continue
                self.__getattribute__(n).val = v
        except CameraError, e:
            self.close()
            raise


    def __del__(self):
        self.close()

    def start( self, bufsize = 4, interactive = False ):
        """
        Start the camera in free running acquisition

        bufsize     - how many DMA buffers should be used? If this value is
                      high, the lag between your currently processed picture
                      and reality might be higher but your risk to miss a frame
                      is also much lower.
        interactive - If this is true, shot() is not supported and no queue
                      overrun can occure
        """
        if self.running:
            return

        if not self._cam:
            raise CameraError("The camera is not opened!")

        # Set video mode and everything: done by the actual fsets in
        #self.mode, self.isospeed and self.fps
        #self._dll.dc1394_video_set_iso_speed( self._cam, self._wanted_speed )
        #self._dll.dc1394_video_set_mode( self._cam, self._wanted_mode )
        #self._dll.dc1394_video_set_framerate( self._cam, self._wanted_frate )
        self._dll.dc1394_capture_setup( self._cam, bufsize, \
                    capture_flag_codes["CAPTURE_FLAGS_DEFAULT"])

        # Start the acquisition
        self._dll.dc1394_video_set_transmission( self._cam, 1 )

        self._queue = None if interactive else Queue(1000)

        # Now, start the Worker thread
        self._worker = _CamAcquisitonThread( self, self._new_image )

        self._running_lock.acquire()
        self._running = True
        self._running_lock.release()

    def stop( self ):
        """Stop the camera and return all frames to the driver"""

        if not self.running:
            return

        assert(self._cam) # Otherwise it couldn't be running
        self._worker.abort()
        self._worker.join()

        self._queue = None

        #stop the camera:
        self._dll.dc1394_capture_stop( self._cam )
        self._dll.dc1394_video_set_transmission( self._cam, 0 )

        #stop the thread:
        self._running_lock.acquire()
        self._running = False
        self._running_lock.release()

    def reset_bus( self ):
        """
        This function resets the bus the camera is attached to. Note that
        this means that all cameras have to reenumerate and will drop frames.
        So only use this if you know what you are doing.

        Note that the camera the camera is closed after this and it is not
        guaranteed that you can reopen it with :method:`open` again. To be sure,
        you have to recreate a new Camera object.
        """
        if self.running:
            self.stop()

        self._dll.dc1394_reset_bus( self._cam )
        self.close()

        # This is needed so the generation is updated on Linux
        self._lib.enumerate_cameras()

    def shot( self ):
        """
        If the camera is running, this will acquire one frame from it and
        return it as a Image (numpy array + some informations).The memory
        is not copied, therefore you should not write on the array.

        Note that acquisition is always running in the background. This
        function alone is guaranteed to return all frames in running order.
        Use this function for your image processing, use cam.current_image
        for visualisation.
        """
        if not self.running:
            raise CameraError("Camera is not running!")
        if not self._queue:
            raise CameraError("Camera is running in interactive mode!")

        return self._queue.get()

    def open( self ):
        """Open the camera"""
        self._cam = _dll.dc1394_camera_new( self._lib.h, self._guid )
        if not self._cam:
            raise CameraError("Couldn't access camera!")

    def close(self):
        """Close the camera. Stops it, if it was running"""
        if self.running:
            self.stop()

        if self._cam:
            _dll.dc1394_camera_free( self._cam )
            self._cam = None

    ###########################################################################
    #                     INFORMATION GATERHING FUNCTIONS                     #
    ###########################################################################
    def __get_supported_modes( self ):
        """
        Get all the supported video modes of the camera.  This calls the
        builting dc1394 function and converts the returned codes to a
        readable list. Any element of this list can be used to set a video
        mode of the camera.

        Parameters: None
        Returns:    list of available video modes
        """
        if not self._cam:
            raise CameraError("The camera is not opened!")

        modes = video_modes_t()

        _dll.dc1394_video_get_supported_modes( self._cam, byref(modes))
        return [_mode_map[i](self._cam, i)
                for i in modes.modes[:modes.num]]

        # return [ Mode(video_mode_details[modes.modes[i]] for i in range(modes.num)]

    def __get_all_features( self ):
        """
        Use a built in dc1394 function to read out all available features
        of the given camera.

        All features, which are capable of absolute values, are set to
        absolute value mode.

        Parameters: None Return value: fills up and returns the self._features
        list
        """

        if not self._cam:
            raise CameraError("The camera is not opened!")

        fs = featureset_t()
        _dll.dc1394_feature_get_all( self._cam, byref(fs) )


        self._features = []

        # We set all features that are capabale of it to absolute values
        for i in range(FEATURE_NUM):
            s = fs.feature[i]
            if s.available:
                if s.absolute_capable:
                    _dll.dc1394_feature_set_absolute_control(self._cam, s.id, 1)
                name = feature_vals[s.id]
                self._features.append( name )
                self.__dict__[name] = CameraProperty(self, name, s.id,
                    s.absolute_capable
                )

        return self._features

    def get_register( self, offset ):
        """Get the control register value of the camera a the given offset"""
        if not self._cam:
            raise CameraError("The camera is not opened!")

        val = c_uint32()
        _dll.dc1394_get_control_registers( self._cam, offset, byref(val), 1)
        return val.value

    def set_register( self, offset, value ):
        """Set the control register value of the camera at the given offset to
        the given value"""
        if not self._cam:
            raise CameraError("The camera is not opened!")

        val = c_uint32(value)
        _dll.dc1394_set_control_registers( self._cam, offset, byref(val), 1)

    ###########################################################################
    #                               PROPERTIES                                #
    ###########################################################################
    def broadcast():
        doc = \
        """
        This sets if the camera tries to synchronize with other cameras on
        the bus.

        Note:   that behaviour might be strange if one camera tries to
                broadcast and another not.

        Note 2: that this feature is currently only supported under linux
                and I have not seen it working yet though I tried it with
                cameras that should support it. So use on your own risk!
        """
        def fget(self):
            if not self._cam:
                raise CameraError("The camera is not opened!")

            k = bool_t()
            self._dll.dc1394_camera_get_broadcast( self._cam, byref(k))
            if k.value == 1:
                return True
            else:
                return False

        def fset(self, value):
            if not self._cam:
                raise CameraError("The camera is not opened!")

            use =  1 if value else 0
            self._dll.dc1394_camera_set_broadcast( self._cam, use )

        return locals()
    broadcast = property(**broadcast())

    @property
    def current_image(self):
        "Threadsafe access to the current image of the camera"
        # We do proper locking
        self._new_image.acquire()
        self._new_image.wait(3.)
        i = self._current_img
        self._new_image.release()
        return i

    @property
    def new_image(self):
        "The Condition to wait for when you want a new Image"
        return self._new_image

    @property
    def running(self):
        """
        This is a thread safe propertie which can check
        if the camera is (still) running
        """
        self._running_lock.acquire()
        rv = self._running
        self._running_lock.release()
        return rv

    @property
    def model(self):
        "The name of this camera (string)"
        if not self._cam:
            raise CameraError("The camera is not opened!")

        return self._cam.contents.model

    @property
    def guid(self):
        "The Guid of this camera as string"
        if not self._cam:
            raise CameraError("The camera is not opened!")

        return hex(self._cam.contents.guid)[2:-1]

    @property
    def vendor(self):
        "The vendor of this camera (string)"
        if not self._cam:
            raise CameraError("The camera is not opened!")

        return self._cam.contents.vendor

    def mode():
        """
        The current video mode of the camera.

        The video modes are what let you choose the image size and color
        format. Two special format classes exist: the :class:`Exif`
        mode (which is actually not supported by any known camera)
        and :class:`Format7` which is the scalable image format.
        Format7 allows you to change the image size, framerate, color
        coding and crop region.

        Important note: your camera will not support all the video modes
        but will only supports a more or less limited subset of them.

        Use :attr:`modes` to obtain a list of valid modes for this camera.

        This property can be written as either a string describing a simple
        mode: "640x480_Y8", as a tuple (640, 480, "Y8") or as a Mode class.
        If you want to use Format7 use the Format7 class.
        """
        def fget(self):
            # vmod = video_mode_t()
            # self._dll.dc1394_video_get_mode(self._cam, byref(vmod))
            return self._mode
        def fset(self, mode):
            if isinstance(mode, (tuple,basestring)):
                try:
                    mode = create_mode(self._cam, mode)
                except KeyError:
                    raise CameraError("Invalid mode for this camera!")
            self._mode = mode
            _dll.dc1394_video_set_mode(self._cam, mode.mode_id)
        return locals()
    mode = property(**mode())


    def fps():
        """
        The framerate belonging to the current camera mode.

        For non-scalable video formats (not :class:`Format7`) there is a
        set of standard frame rates one can choose from. A list
        of all the framerates supported by your camera for a specific
        video mode can be obtained from :attr:`Mode.rates`.

        .. note::
           You may also be able to set the framerate with the
           :attr:`framerate` feature if present.

        .. note::
           Framerates are used with fixed-size image formats (Format_0
           to Format_2).  In :class:`Format7` modes the camera can tell
           an actual value, but one can not set it.  Unfortunately the
           returned framerate may have no sense at all.  If you use
           Format_7 you should set the framerate by adjusting the number
           of bytes per packet (:attr:`Format7.packet_size`) and/or the
           shutter time.
        """
        def fget(self):
            ft = framerate_t()
            _dll.dc1394_video_get_framerate(self._cam, byref(ft))
            return framerate_vals[ft.value]
        def fset(self, framerate):
            wanted_frate = framerate_codes[framerate]
            _dll.dc1394_video_set_framerate(self._cam, wanted_frate)
        return locals()

    fps = property(**fps())

    def isospeed():
        doc = \
            """ The isospeed of the camera.

                If queried, returns the actual isospeed value.
                If set, it tries setting the speed.

                One can get the actual set value of the camera or set from:
                100, 200, 400, 800, 1600, 3200 if the camera supports them.

                Above 400 the 1394b high speed mode has to be available
                (the function tries to set it).
            """
        def fget(self):
            sp = speed_t()
            self._dll.dc1394_video_get_iso_speed( self._cam, byref(sp) )
            return speed_vals[ sp.value ]

        def fset(self, isospeed):
            if speed_codes.has_key( isospeed ):
                try:
                    self._operation_mode = 'legacy' if isospeed < 800 \
                        else '1394b'
                except RuntimeError:
                    raise CameraError(
                        "1394b mode is not supported by hardware, but needed!"
                    )
                else:
                    sp = speed_codes[ isospeed ]
                    self._dll.dc1394_video_set_iso_speed(self._cam, sp )
            else:
                raise CameraError("Invalid isospeed: %s" % isospeed)
        return locals()
    isospeed = property( **isospeed() )

    def _operation_mode():
        doc = \
        """
        This can toggle the camera mode into B mode (high speeds). This is
        a private property because you definitively do not want to change
        this as a user.
        """
        def fget(self):
            if not self._cam:
                raise CameraError("The camera is not opened!")

            k = c_int()
            self._dll.dc1394_video_get_operation_mode( self._cam, byref(k))
            if k.value == 480:
                return "legacy"
            else:
                return "1394b"
        def fset(self, value):
            if not self._cam:
                raise CameraError("The camera is not opened!")

            use =  480 if value == "legacy" else 481
            self._dll.dc1394_video_set_operation_mode( self._cam, use )
        return locals()
    _operation_mode = property(**_operation_mode())

    @property
    def modes(self):
        "Return all supported modes for this camera"
        return self._all_modes


    @property
    def features(self):
        """Return all features of this camera. You can use __getattr__ to
        directly access them then."""
        return self._all_features


class SynchronizedCams(object):
    def __init__(self, cam0,cam1):
        """This class synchronizes two (not more!) cameras
        by dropping frames from one until the timestamps
        of the acquired pictures are in sync. Make sure that the
        cameras are in the same mode (framerate, shutter)

        This function assumes point gray cameras which can do autosync
        """
        self._cam0 = cam0
        self._cam1 = cam1

    def close( self ):
        "Convenient function which closes both cams"
        self._cam0.close()
        self._cam1.close()

    @property
    def cam0(self):
        return self._cam0
    @property
    def cam1(self):
        return self._cam1

    def start(self, buffers = 4):
        self._cam0.start(buffers); self._cam1.start(buffers)

        self.sync()

    def stop(self):
        self._cam0.stop(); self._cam1.stop()

    def shot(self):
        """
        This function acquires two synchronized pictures from
        the cameras. Use this if you need pictures which were
        acquired around the same time. Do not use the cams individual shot
        functions. If you need a current image you can use cam.current_image
        at all times. You can also wait for the Condition cam.new_image
        and then use cam.current_image.

        note that the user has to check for themselves if the cameras
        are out of sync and must make sure they get back in sync.
        """
        i1 = self._cam0.shot()
        i2 = self._cam1.shot()

        return i1,i2


    def sync(self):
        """
        Try to sync the two cameras to each other. This will
        only work if both cameras synchronize on the bus time
        """
        ldiff = 100000000
        while 1:
            t1 = self._cam0.shot().timestamp
            t2 = self._cam1.shot().timestamp

            diff = t1-t2

            if abs(diff) < 500:
                break
            if diff < 0:
                self._cam0.shot()
            else:
                self._cam1.shot()
            ldiff = diff

