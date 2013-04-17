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


"""This file wraps the dc1394 library functions"""

from ctypes import *
from ctypes.util import find_library
import sys


try:
    _dll = cdll.LoadLibrary(find_library('dc1394'))
except Exception, e:
    raise RuntimeError("FATAL: dc1394 could not be found or opened: %s" % e)
#end try

###########################################################################
#                                  ENUMS                                  #
###########################################################################
#All these enum values should be transparent forth and back. The numbers
#need to be interpreted in human readable form, but the user should also
# be able to get the numbers back easily, even in an automated way
#The standard ctypes way would define a variable for each enum value.
#A dict structure should be more flexible.

def invert_dict( to_invert ):
    res = {}
    for (i,j) in to_invert.iteritems():
        res[j] = i
    #end for
    return res
#end invert_dict

#All error values to be interpreted:
error_vals = {
        0: 'SUCCESS',
       -1: 'FAILURE',
       -2: 'NOT_A_CAMERA',
       -3: 'FUNCTION_NOT_SUPPORTED',
       -4: 'CAMERA_NOT_INITIALIZED',
       -5: 'MEMORY_ALLOCATION_FAILURE',
       -6: 'TAGGED_REGISTER_NOT_FOUND',
       -7: 'NO_ISO_CHANNEL',
       -8: 'NO_BANDWIDTH',
       -9: 'IOCTL_FAILURE',
      -10: 'CAPTURE_IS_NOT_SET',
      -11: 'CAPTURE_IS_RUNNING',
      -12: 'RAW1394_FAILURE',
      -13: 'FORMAT7_ERROR_FLAG_1',
      -14: 'FORMAT7_ERROR_FLAG_2',
      -15: 'INVALID_ARGUMENT_VALUE',
      -16: 'REQ_VALUE_OUTSIDE_RANGE',
      -17: 'INVALID_FEATURE',
      -18: 'INVALID_VIDEO_FORMAT',
      -19: 'INVALID_VIDEO_MODE',
      -20: 'INVALID_FRAMERATE',
      -21: 'INVALID_TRIGGER_MODE',
      -22: 'INVALID_TRIGGER_SOURCE',
      -23: 'INVALID_ISO_SPEED',
      -24: 'INVALID_IIDC_VERSION',
      -25: 'INVALID_COLOR_CODING',
      -26: 'INVALID_COLOR_FILTER',
      -27: 'INVALID_CAPTURE_POLICY',
      -28: 'INVALID_ERROR_CODE',
      -29: 'INVALID_BAYER_METHOD',
      -30: 'INVALID_VIDEO1394_DEVICE',
      -31: 'INVALID_OPERATION_MODE',
      -32: 'INVALID_TRIGGER_POLARITY',
      -33: 'INVALID_FEATURE_MODE',
      -34: 'INVALID_LOG_TYPE',
      -35: 'INVALID_BYTE_ORDER',
      -36: 'INVALID_STEREO_METHOD',
      -37: 'BASLER_NO_MORE_SFF_CHUNKS',
      -38: 'BASLER_CORRUPTED_SFF_CHUNK',
      -39: 'BASLER_UNKNOWN_SFF_CHUNK',
}

#All error codes to be asked back:
error_codes = invert_dict( error_vals )

error_t = c_int
ERROR_MIN = min(error_vals.keys())
ERROR_MAX = max(error_vals.keys())
ERROR_NUM =(ERROR_MAX-ERROR_MIN+1)

#Logging enum
log_vals={
        768 : 'LOG_ERROR',
        769 : 'LOG_WARNING',
        770 : 'LOG_DEBUG',
        }

log_codes = invert_dict( log_vals )
log_t = c_int
LOG_MIN = min(log_vals.keys())
LOG_MAX = max( log_vals.keys())
LOG_NUM = LOG_MAX - LOG_MIN

iidc_version_vals = {
      544: 'IIDC_VERSION_1_04',
      545: 'IIDC_VERSION_1_20',
      546: 'IIDC_VERSION_PTGREY',
      547: 'IIDC_VERSION_1_30',
      548: 'IIDC_VERSION_1_31',
      549: 'IIDC_VERSION_1_32',
      550: 'IIDC_VERSION_1_33',
      551: 'IIDC_VERSION_1_34',
      552: 'IIDC_VERSION_1_35',
      553: 'IIDC_VERSION_1_36',
      554: 'IIDC_VERSION_1_37',
      555: 'IIDC_VERSION_1_38',
      556: 'IIDC_VERSION_1_39',
}
iidc_version_codes = invert_dict( iidc_version_vals )

iidc_version_t = c_int
#VIDEO_MODE:
#Now this is complicated, because by standard the resolution is the first
#then the video mode.
video_mode_vals = {
       64: '160x120_YUV444',
       65: '320x240_YUV422',
       66: '640x480_YUV411',
       67: '640x480_YUV422',
       68: '640x480_RGB8',
       69: '640x480_Y8',
       70: '640x480_Y16',
       71: '800x600_YUV422',
       72: '800x600_RGB8',
       73: '800x600_Y8',
       74: '1024x768_YUV422',
       75: '1024x768_RGB8',
       76: '1024x768_Y8',
       77: '800x600_Y16',
       78: '1024x768_Y16',
       79: '1280x960_YUV422',
       80: '1280x960_RGB8',
       81: '1280x960_Y8',
       82: '1600x1200_YUV422',
       83: '1600x1200_RGB8',
       84: '1600x1200_Y8',
       85: '1280x960_Y16',
       86: '1600x1200_Y16',
       87: 'EXIF',
       88: 'FORMAT7_0',
       89: 'FORMAT7_1',
       90: 'FORMAT7_2',
       91: 'FORMAT7_3',
       92: 'FORMAT7_4',
       93: 'FORMAT7_5',
       94: 'FORMAT7_6',
       95: 'FORMAT7_7',
}
video_mode_codes = invert_dict( video_mode_vals )

video_mode_t = c_int32
VIDEO_MODE_MIN = min(video_mode_vals.keys())
VIDEO_MODE_MAX = max(video_mode_vals.keys())
VIDEO_MODE_NUM = (VIDEO_MODE_MAX - VIDEO_MODE_MIN + 1)
VIDEO_MODE_FORMAT7_MIN = video_mode_codes['FORMAT7_0']
VIDEO_MODE_FORMAT7_MAX = video_mode_codes['FORMAT7_7']
VIDEO_MODE_FORMAT7_NUM = (VIDEO_MODE_FORMAT7_MAX - VIDEO_MODE_FORMAT7_MIN + 1)

#these tuples can provide the default resolution / color scheme codes
video_mode_details = {
       64: (160,120,'YUV444'),
       65: (320,240,'YUV422'),
       66: (640,480,'YUV411'),
       67: (640,480,'YUV422'),
       68: (640,480,'RGB8'),
       69: (640,480,'Y8'),
       70: (640,480,'Y16'),
       71: (800,600,'YUV422'),
       72: (800,600,'RGB8'),
       73: (800,600,'Y8'),
       74: (1024,768,'YUV422'),
       75: (1024,768,'RGB8'),
       76: (1024,768,'Y8'),
       77: (800,600,'Y16'),
       78: (1024,768,'Y16'),
       79: (1280,960,'YUV422'),
       80: (1280,960,'RGB8'),
       81: (1280,960,'Y8'),
       82: (1600,1200,'YUV422'),
       83: (1600,1200,'RGB8'),
       84: (1600,1200,'Y8'),
       85: (1280,960,'Y16'),
       86: (1600,1200,'Y16'),
       87: 'EXIF',
       88: 'FORMAT7_0',
       89: 'FORMAT7_1',
       90: 'FORMAT7_2',
       91: 'FORMAT7_3',
       92: 'FORMAT7_4',
       93: 'FORMAT7_5',
       94: 'FORMAT7_6',
       95: 'FORMAT7_7',
}


# Color codings
color_coding_vals = {
      352: 'Y8',
      353: 'YUV411',
      354: 'YUV422',
      355: 'YUV444',
      356: 'RGB8',
      357: 'Y16',
      358: 'RGB16',
      359: 'Y16S',
      360: 'RGB16S',
      361: 'RAW8',
      362: 'RAW16',
}

color_coding_codes = invert_dict( color_coding_vals )

#for some extra interpretation:
color_coding_codes['MONO8'] = color_coding_codes['Y8']
color_coding_codes['MONO16'] = color_coding_codes['Y16']
color_coding_codes['MONO16S'] = color_coding_codes['Y16S']

color_coding_t = c_int
COLOR_CODING_MIN =  min(color_coding_vals.keys())
COLOR_CODING_MAX =  max(color_coding_vals.keys())
COLOR_CODING_NUM = (COLOR_CODING_MAX - COLOR_CODING_MIN + 1)


#COLOR_FILTER:
color_filter_vals = {
      512: 'RGGB',
      513: 'GBRG',
      514: 'GRBG',
      515: 'BGGR',
}
color_filter_codes = invert_dict( color_filter_vals )

color_filter_t = c_int

COLOR_FILTER_MIN =  min(color_filter_vals.keys())
COLOR_FILTER_MAX =  max(color_filter_vals.keys())
COLOR_FILTER_NUM = (COLOR_FILTER_MAX - COLOR_FILTER_MIN + 1)

# Byte order
byte_order_vals = {
      800: 'BYTE_ORDER_UYVY',
      801: 'BYTE_ORDER_YUYV',
}
byte_order_codes = invert_dict( byte_order_vals )

byte_order_t = c_int
BYTE_ORDER_MIN =  min(byte_order_vals.keys())
BYTE_ORDER_MAX =  max(byte_order_vals.keys())
BYTE_ORDER_NUM = (BYTE_ORDER_MAX - BYTE_ORDER_MIN + 1)

#Enums for color conversions:
#A list of de-mosaicing techniques for Bayer-patterns.
#The speed of the techniques can vary greatly, as well as their quality.
bayer_method_vals = {
        0 : 'BAYER_METHOD_NEAREST',
        1 : 'BAYER_METHOD_SIMPLE',
        2 : 'BAYER_METHOD_BILINEAR',
        3 : 'BAYER_METHOD_HQLINEAR',
        4 : 'BAYER_METHOD_DOWNSAMPLE',
        5 : 'BAYER_METHOD_EDGESENSE',
        6 : 'BAYER_METHOD_VNG',
        7 : 'BAYER_METHOD_AHD'}
bayer_method_codes = invert_dict( bayer_method_vals )

bayer_method_t = c_int
BAYER_METHOD_MIN = min( bayer_method_vals.keys() )
BAYER_METHOD_MAX = max( bayer_method_vals.keys() )
BAYER_METHOD_NUM = BAYER_METHOD_MAX - BAYER_METHOD_MIN

#A list of known stereo-in-normal-video modes used by manufacturers like Point
# Grey Research and Videre Design.

stereo_method_vals = {
        0 : 'STEREO_METHOD_INTERLACED',
        1 : 'STEREO_METHOD_FIELD' }
stereo_method_codes = invert_dict( stereo_method_vals )

stereo_method_t = c_int

STEREO_METHOD_MIN = min( stereo_method_vals.keys())
STEREO_METHOD_MAX = max( stereo_method_vals.keys())
STEREO_METHOD_NUM = STEREO_METHOD_MAX - STEREO_METHOD_MIN

#############################################################################
#
#TRIGGER_MODE:
trigger_mode_vals = {
      384: 'TRIGGER_MODE_0',
      385: 'TRIGGER_MODE_1',
      386: 'TRIGGER_MODE_2',
      387: 'TRIGGER_MODE_3',
      388: 'TRIGGER_MODE_4',
      389: 'TRIGGER_MODE_5',
      390: 'TRIGGER_MODE_14',
      391: 'TRIGGER_MODE_15',
}
trigger_mode_codes = invert_dict( trigger_mode_vals )

trigger_mode_t = c_int
TRIGGER_MODE_MIN = min(trigger_mode_vals.keys())
TRIGGER_MODE_MAX = max(trigger_mode_vals.keys())
TRIGGER_MODE_NUM =(TRIGGER_MODE_MAX - TRIGGER_MODE_MIN + 1)

#FRAMERATE
framerate_vals = {
       32: 1.875,
       33: 3.75,
       34: 7.5,
       35: 15.,
       36: 30,
       37: 60.,
       38: 120.,
       39: 240.,
}
framerate_codes = invert_dict( framerate_vals )

framerate_t = c_int
FRAMERATE_MIN = min( framerate_vals.keys() )
FRAMERATE_MAX = max( framerate_vals.keys() )
FRAMERATE_NUM =(FRAMERATE_MAX - FRAMERATE_MIN + 1)


#ISO_SPEED
speed_vals = {
        0: 100,
        1: 200,
        2: 400,
        3: 800,
        4: 1600,
        5: 3200,
}
speed_codes = invert_dict( speed_vals )
speed_t = c_int
ISO_SPEED_MIN = min( speed_vals.keys())
ISO_SPEED_MAX = max( speed_vals.keys())
ISO_SPEED_NUM = (ISO_SPEED_MAX - ISO_SPEED_MIN + 1)

#FEATURE:
feature_vals = {
      416: 'brightness',
      417: 'exposure',
      418: 'sharpness',
      419: 'white_balance',
      420: 'hue',
      421: 'saturation',
      422: 'gamma',
      423: 'shutter',
      424: 'gain',
      425: 'iris',
      426: 'focus',
      427: 'temperature',
      428: 'trigger',
      429: 'trigger_delay',
      430: 'white_shading',
      431: 'framerate',
      432: 'zoom',
      433: 'pan',
      434: 'tilt',
      435: 'optical_filter',
      436: 'capture_size',
      437: 'capture_quality',
}

feature_codes = invert_dict( feature_vals )
feature_t = c_int
FEATURE_MIN = min( feature_vals.keys())
FEATURE_MAX = max( feature_vals.keys())
FEATURE_NUM = (FEATURE_MAX - FEATURE_MIN + 1)

#TRIGGER_SOURCE
trigger_source_vals = {
      576: 'TRIGGER_SOURCE_0',
      577: 'TRIGGER_SOURCE_1',
      578: 'TRIGGER_SOURCE_2',
      579: 'TRIGGER_SOURCE_3',
      580: 'TRIGGER_SOURCE_SOFTWARE',
}
trigger_source_codes = invert_dict( trigger_source_vals )
trigger_source_t = c_int
TRIGGER_SOURCE_MIN = min( trigger_source_vals.keys())
TRIGGER_SOURCE_MAX = max( trigger_source_vals.keys())
TRIGGER_SOURCE_NUM =(TRIGGER_SOURCE_MAX - TRIGGER_SOURCE_MIN + 1)

#for some reason my camera reports 0 and 1
# on the http://damien.douxchamps.net/ieee1394/libdc1394/v2.x/api/types/
#it also reports 0 and 1 values
#in my current control.h:
#trigger_polarity_vals = {
#      704: 'TRIGGER_ACTIVE_LOW',
#      705: 'TRIGGER_ACTIVE_HIGH',
#}
trigger_polarity_vals = {
      0: 'TRIGGER_ACTIVE_LOW',
      1: 'TRIGGER_ACTIVE_HIGH',
}
trigger_polarity_codes = invert_dict( trigger_polarity_vals )

trigger_polarity_t = c_int
TRIGGER_ACTIVE_MIN = min( trigger_polarity_vals.keys())
TRIGGER_ACTIVE_MAX = max( trigger_polarity_vals.keys())
TRIGGER_ACTIVE_NUM =(TRIGGER_ACTIVE_MAX - TRIGGER_ACTIVE_MIN + 1)

#FEATURE_MODE
feature_mode_vals = {
      736: 'manual',
      737: 'auto',
      738: 'one_push',
}
feature_mode_codes = invert_dict( feature_mode_vals )

feature_mode_t = c_int
FEATURE_MODE_MIN = min( feature_mode_vals.keys() )
FEATURE_MODE_MAX = max( feature_mode_vals.keys() )
FEATURE_MODE_NUM = (FEATURE_MODE_MAX - FEATURE_MODE_MIN + 1)

capture_flag_codes= {\
        "CAPTURE_FLAGS_CHANNEL_ALLOC" : 0x00000001,\
        "CAPTURE_FLAGS_BANDWIDTH_ALLOC" : 0x00000002,\
        "CAPTURE_FLAGS_DEFAULT" : 0x00000004,\
        "CAPTURE_FLAGS_AUTO_ISO" : 0x00000008
}
capture_flag_vals = invert_dict( capture_flag_codes )

###########################################################################
#                               STRUCTURES                                #
###########################################################################

class color_codings_t(Structure):
     pass
color_codings_t._fields_ = [
    ("num", c_uint32),
    ("codings", (color_coding_t)*COLOR_CODING_NUM),
]

# Video modes
class video_modes_t(Structure):
     pass
video_modes_t._fields_ = [
    ("num", c_uint32),
    ("modes", (video_mode_t)*VIDEO_MODE_NUM),
]

#For some obscured reason this overrides the video_mode_t
#We do not need this (hopefully)
#class video_mode_t(Structure):
#     pass
#video_mode_t._fields_ = [
#    ("num", c_uint32),
#    ("modes", (video_mode_t)*VIDEO_MODE_NUM),
#]

#these folks have logical ON/OFF = True/False values
bool_t = c_int
switch_t = c_int

class camera_t(Structure):
     pass
camera_t._fields_ = [
    ("guid", c_uint64),
    ("unit", c_int),
    ("unit_spec_ID", c_uint32),
    ("unit_sw_version", c_uint32),
    ("unit_sub_sw_version", c_uint32),
    ("command_registers_base", c_uint32),
    ("unit_directory", c_uint32),
    ("unit_dependent_directory", c_uint32),
    ("advanced_features_csr", c_uint64),
    ("PIO_control_csr", c_uint64),
    ("SIO_control_csr", c_uint64),
    ("strobe_control_csr", c_uint64),
    ("format7_csr", (c_uint64)*8),
    ("iidc_version", iidc_version_t),
    ("vendor", c_char_p),
    ("model", c_char_p),
    ("vendor_id", c_uint32),
    ("model_id", c_uint32),
    ("bmode_capable", bool_t),
    ("one_shot_capable", bool_t),
    ("multi_shot_capable", bool_t),
    ("can_switch_on_off", bool_t),
    ("has_vmode_error_status", bool_t),
    ("has_feature_error_status", bool_t),
    ("max_mem_channel", c_int),
    ("flags", c_uint32),
]

class camera_id_t(Structure):
     pass
camera_id_t._fields_ = [
    ("unit", c_uint16),
    ("guid", c_uint64),
]

class camera_list_t(Structure):
     pass
camera_list_t._fields_ = [
    ("num", c_uint32),
    ("ids", POINTER(camera_id_t)),
]

class framerates_t(Structure):
    pass
framerates_t._fields_ = [
    ("num", c_uint32),
    ("framerates", (framerate_t)*FRAMERATE_NUM),
]
class feature_modes_t(Structure):
     pass
feature_modes_t._fields_ = [
    ("num", c_uint32),
    ("modes", (feature_mode_t)*FEATURE_MODE_NUM),
]

class trigger_modes_t(Structure):
     pass
trigger_modes_t._fields_ = [
    ("num", c_uint32),
    ("modes", (trigger_mode_t)*TRIGGER_MODE_NUM),
]

class trigger_sources_t(Structure):
     pass
trigger_sources_t._fields_ = [
    ("num", c_uint32),
    ("sources", (trigger_source_t)*TRIGGER_SOURCE_NUM),
]

class feature_info_t(Structure):
     pass
feature_info_t._fields_ = [
    ("id", feature_t),
    ("available", bool_t),
    ("absolute_capable", bool_t),
    ("readout_capable", bool_t),
    ("on_off_capable", bool_t),
    ("polarity_capable", bool_t),
    ("is_on", switch_t),
    ("current_mode", feature_mode_t),
    ("modes", feature_modes_t),
    ("trigger_modes", trigger_modes_t),
    ("trigger_mode", trigger_mode_t),
    ("trigger_polarity", trigger_polarity_t),
    ("trigger_sources", trigger_sources_t),
    ("trigger_source", trigger_source_t),
    ("min", c_uint32),
    ("max", c_uint32),
    ("value", c_uint32),
    ("BU_value", c_uint32),
    ("RV_value", c_uint32),
    ("B_value", c_uint32),
    ("R_value", c_uint32),
    ("G_value", c_uint32),
    ("target_value", c_uint32),
    ("abs_control", switch_t),
    ("abs_value", c_float),
    ("abs_max", c_float),
    ("abs_min", c_float),
]

class featureset_t(Structure):
     pass
featureset_t._fields_ = [
    ("feature", (feature_info_t)*FEATURE_NUM),
]

class video_frame_t(Structure):
     pass
video_frame_t._fields_ = [
    ("image", c_void_p),
    ("size", (c_uint32)*2),
    ("position", (c_uint32)*2),
    ("color_coding", color_coding_t),
    ("color_filter", color_filter_t),
    ("yuv_byte_order", c_uint32),
    ("data_depth", c_uint32),
    ("stride", c_uint32),
    ("video_mode", video_mode_t),
    ("total_bytes", c_uint64), #the buffer + the unused part
    ("image_bytes", c_uint32), #the length of the image buffer in bytes
    ("padding_bytes", c_uint32),
    ("packet_size", c_uint32),
    ("packets_per_frame", c_uint32),
    ("timestamp", c_uint64),
    ("frames_behind", c_uint32),
    ("camera", POINTER(camera_t)),
    ("id", c_uint32),
    ("allocated_image_bytes", c_uint64),
    ("little_endian", bool_t),
    ("data_in_padding", bool_t),
]

class format7mode_t(Structure):
    pass
format7mode_t._fields_ = [
        ("present", bool_t ),
        ("size_x", c_uint32),
        ("size_y", c_uint32),
        ("max_size_x", c_uint32),
        ("max_size_y", c_uint32),
        ("pos_x", c_uint32),
        ("pos_y", c_uint32),
        ("unit_size_x", c_uint32),
        ("unit_size_y", c_uint32),
        ("unit_pos_x", c_uint32),
        ("unit_pos_y", c_uint32),
        ("color_codings", color_codings_t),
        ("color_coding", color_coding_t),
        ("pixnum", c_uint32),
        ("packet_size", c_uint32),
        ("unit_packet_size", c_uint32),
        ("max_packet_size", c_uint32),
        ("total_bytes", c_uint64),
        ("color_filter", color_filter_t),
        ]
#end of class format7mode_t

class format7modeset_t(Structure):
    pass
format7modeset_t._fields_=[
        ("mode", format7mode_t * VIDEO_MODE_FORMAT7_NUM),
        ]
#end of class format7modeset_t

#End structures....

CAPTURE_POLICY_WAIT=672
CAPTURE_POLICY_POLL=673

QUERY_FROM_CAMERA= -1
USE_MAX_AVAIL    = -2
USE_RECOMMENDED  = -3

###########################################################################
#                            PYTHON FUNCTIONS                             #
###########################################################################
# Global Error checking functions
def _errcheck( rtype, func, arg ):
    """This function checks for the errortypes declared by the error_t above.
        Use it for functions with restype=error_t to receive correct error
        messages from the library.
    """
    if rtype != 0:
        raise RuntimeError("Error in dc1394 function call: %s"
                    % error_vals[rtype])
    return rtype


###########################################################################
#                                FUNCTIONS                                #
###########################################################################
#Reminder:
# By default the ctypes API does not know or care about how a dll funciton
# should be called. This may lead a lot of crashes and memory corruption.
# I think it is safer to declare all functions here, independent of usage,
# so at least the API can handle the ingoing/returning parameters properly.
#
# restypes: the result type of the function
# argyypes: type of the arguments
# Many of the functions require a lib_pointer to the opened lib.
#
# many of the dc1394 functions return an error value, these can be handled
# by the _errcheck funciton above
###############################################################################
# Startup functions: camera.h
###############################################################################
#to start the library:
_dll.dc1394_new.argtypes = None
_dll.dc1394_new.restype = c_void_p

_dll.dc1394_free.argtypes = [c_void_p]
_dll.dc1394_free.restype = None

#Bus level functions:
# Sets and gets the broadcast flag of a camera. If the broadcast flag is set,
# all devices on the bus will execute the command. Useful to sync ISO start
# commands or setting a bunch of cameras at the same time. Broadcast only works
# with identical devices (brand/model). If the devices are not identical your
# mileage may vary. Some cameras may not answer broadcast commands at all. Also,
# this only works with cameras on the SAME bus (IOW, the same port).

_dll.dc1394_camera_get_broadcast.argtypes = [ c_void_p, POINTER(bool_t) ]
_dll.dc1394_camera_get_broadcast.errcheck = _errcheck

_dll.dc1394_camera_set_broadcast.argtypes = [ c_void_p, bool_t ]
_dll.dc1394_camera_set_broadcast.errcheck = _errcheck

# Resets the IEEE1394 bus which camera is attached to.
# A "rude" function to reset the bus (after a connection hanging
# due to program crash); it causes other devices using the bus
# to new enumerate and may disrupt other activities:
_dll.dc1394_reset_bus.argtypes = [POINTER(camera_t)]
_dll.dc1394_reset_bus.restype = error_t
_dll.dc1394_reset_bus.errcheck = _errcheck

_dll.dc1394_read_cycle_timer.argtypes = [ POINTER(camera_t), POINTER(c_uint32), POINTER(c_uint64)]
_dll.dc1394_read_cycle_timer.restype=error_t
_dll.dc1394_read_cycle_timer.errcheck = _errcheck

#Gets the IEEE1394 node ID of the camera (not often needed):
_dll.dc1394_camera_get_node.argtypes = [POINTER(camera_t), POINTER(c_uint32), POINTER(c_uint32)]
_dll.dc1394_camera_get_node.restype = error_t
_dll.dc1394_camera_get_node.errcheck = _errcheck

#list of cameras on the computer;
# if present, multiple cards will be probed:
_dll.dc1394_camera_enumerate.argtypes = [ c_void_p, POINTER(POINTER(camera_list_t)) ]
_dll.dc1394_camera_enumerate.restype = error_t
_dll.dc1394_camera_enumerate.errcheck = _errcheck

#free up the list when done (no return values):
_dll.dc1394_camera_free_list.argtype = [POINTER(camera_list_t)]
_dll.dc1394_camera_free_list.restype = None

#create a new camera based on a 64 bit GUID:
_dll.dc1394_camera_new.argtypes = [ c_void_p, c_uint64 ]
_dll.dc1394_camera_new.restype = POINTER(camera_t)

#create a new camera based on the GUID and a unit:
_dll.dc1394_camera_new_unit.argtypes = [ c_void_p, c_uint64, c_int ]
_dll.dc1394_camera_new_unit.restype = POINTER(camera_t)

#free the camera (no return value):
_dll.dc1394_camera_free.argtypes = [ POINTER(camera_t) ]
_dll.dc1394_camera_free.restype = None

#print camera information to a file:
#we can do this ourselves, this funciton is unused; FILE* goes as a void* for now.
_dll.dc1394_camera_print_info.argtypes = [POINTER(camera_t), c_void_p]
_dll.dc1394_camera_print_info.restype = error_t
_dll.dc1394_camera_print_info.errcheck = _errcheck

###################################################################################
# FEATURE CONTROL (control.h)#
###################################################################################
#Collects the available features for the camera described by node and stores them in features
_dll.dc1394_feature_get_all.argtypes = [ POINTER(camera_t), POINTER(featureset_t) ]
_dll.dc1394_feature_get_all.restype = error_t
_dll.dc1394_feature_get_all.errcheck = _errcheck

# Stores the bounds and options associated with the feature described by feature->feature_id
_dll.dc1394_feature_get.argtypes = [ POINTER(camera_t), POINTER(feature_info_t) ]
_dll.dc1394_feature_get.restype = error_t
_dll.dc1394_feature_get.errcheck = _errcheck

#Displays the bounds and options of the given feature
_dll.dc1394_feature_print.argtypes = [POINTER(feature_info_t), c_void_p]
_dll.dc1394_feature_print.restype = error_t
_dll.dc1394_feature_print.errcheck = _errcheck

# Displays the bounds and options of every feature supported by the camera
_dll.dc1394_feature_print_all.argtypes = [ POINTER(featureset_t), c_void_p ]
_dll.dc1394_feature_print_all.restype = error_t
_dll.dc1394_feature_print_all.errcheck = _errcheck

#white balance: get/set
_dll.dc1394_feature_whitebalance_get_value.argtypes=[POINTER(camera_t), POINTER(c_uint32), POINTER(c_uint32)]
_dll.dc1394_feature_whitebalance_get_value.restype = error_t
_dll.dc1394_feature_whitebalance_get_value.errcheck = _errcheck

_dll.dc1394_feature_whitebalance_set_value.argtypes=[POINTER(camera_t), c_uint32, c_uint32]
_dll.dc1394_feature_whitebalance_set_value.restype = error_t
_dll.dc1394_feature_whitebalance_set_value.errcheck = _errcheck

#Temperature: get/set
_dll.dc1394_feature_temperature_get_value.argtypes=[POINTER(camera_t), POINTER(c_uint32), POINTER(c_uint32)]
_dll.dc1394_feature_temperature_get_value.restype = error_t
_dll.dc1394_feature_temperature_get_value.errcheck = _errcheck

_dll.dc1394_feature_temperature_set_value.argtypes=[POINTER(camera_t), c_uint32]
_dll.dc1394_feature_temperature_set_value.restype = error_t
_dll.dc1394_feature_temperature_set_value.errcheck = _errcheck

#white shading:
_dll.dc1394_feature_whiteshading_get_value.argtypes=[POINTER(camera_t), POINTER(c_uint32), POINTER(c_uint32), POINTER(c_uint32) ]
_dll.dc1394_feature_whiteshading_get_value.restype = error_t
_dll.dc1394_feature_whiteshading_get_value.errcheck = _errcheck

_dll.dc1394_feature_whiteshading_set_value.argtypes=[POINTER(camera_t), c_uint32, c_uint32, c_uint32 ]
_dll.dc1394_feature_whiteshading_set_value.restype = error_t
_dll.dc1394_feature_whiteshading_set_value.errcheck = _errcheck

#Bounds and options of a feature, relative values:
_dll.dc1394_feature_get_value.argtypes = [ c_void_p, c_int, POINTER(c_uint32) ]
_dll.dc1394_feature_get_value.restype = error_t
_dll.dc1394_feature_get_value.errcheck = _errcheck

_dll.dc1394_feature_set_value.argtypes = [ c_void_p, c_int, c_uint32 ]
_dll.dc1394_feature_set_value.restype = error_t
_dll.dc1394_feature_set_value.errcheck = _errcheck

#Tells whether a feature is present or not
_dll.dc1394_feature_is_present.argtypes = [POINTER( camera_t ),feature_t, POINTER(bool_t) ]
_dll.dc1394_feature_is_present.restype = error_t
_dll.dc1394_feature_is_present.errcheck = _errcheck

#Tells whether a feature is readable or not
_dll.dc1394_feature_is_readable.argtypes = [ POINTER(camera_t),feature_t, POINTER(bool_t) ]
_dll.dc1394_feature_is_readable.restype = error_t
_dll.dc1394_feature_is_readable.errcheck = _errcheck

#Gets the boundaries of a feature
_dll.dc1394_feature_get_boundaries.argtypes= [ POINTER(camera_t),feature_t, POINTER(c_uint32), POINTER(c_uint32)]
_dll.dc1394_feature_get_boundaries.restype = error_t
_dll.dc1394_feature_get_boundaries.errcheck = _errcheck

#Tells whether a feature is switcheable or not (ON/OFF)
_dll.dc1394_feature_is_switchable.argtypes = [POINTER(camera_t),feature_t, POINTER(bool_t)]
_dll.dc1394_feature_is_switchable.restype = error_t
_dll.dc1394_feature_is_switchable.errcheck = _errcheck

#Set/Get power:
_dll.dc1394_feature_get_power.argtypes = [POINTER(camera_t),feature_t, POINTER(switch_t)]
_dll.dc1394_feature_get_power.restype = error_t
_dll.dc1394_feature_get_power.errcheck = _errcheck

_dll.dc1394_feature_set_power.argtypes = [POINTER(camera_t),feature_t, switch_t]
_dll.dc1394_feature_set_power.restype = error_t
_dll.dc1394_feature_set_power.errcheck = _errcheck

#Tells whether a feature can be controlled in absolute mode
_dll.dc1394_feature_has_absolute_control.argtypes = [POINTER(camera_t),feature_t, POINTER(bool_t)]
_dll.dc1394_feature_has_absolute_control.restype = error_t
_dll.dc1394_feature_has_absolute_control.errcheck = _errcheck

#Gets the absolute boundaries of a feature
_dll.dc1394_feature_get_absolute_boundaries.argtypes = [ POINTER(camera_t),feature_t, POINTER(c_float), POINTER(c_float)]
_dll.dc1394_feature_get_absolute_boundariesrestype = error_t
_dll.dc1394_feature_get_absolute_boundaries.errcheck = _errcheck

#Get/Set absolute value:
_dll.dc1394_feature_get_absolute_value.argtypes = [ c_void_p, c_int, POINTER(c_float) ]
_dll.dc1394_feature_get_absolute_value.restype = error_t
_dll.dc1394_feature_get_absolute_value.errcheck = _errcheck

_dll.dc1394_feature_set_absolute_value.argtypes = [ c_void_p, c_int, c_float ]
_dll.dc1394_feature_set_absolute_value.restype = error_t
_dll.dc1394_feature_set_absolute_value.errcheck = _errcheck

#Gets the status of absolute control of a feature
_dll.dc1394_feature_get_absolute_control.argtypes = [POINTER(camera_t),feature_t, POINTER(switch_t)]
_dll.dc1394_feature_get_absolute_control.restype = error_t
_dll.dc1394_feature_get_absolute_control.errcheck = _errcheck

#Sets absolute control ON/OFF
_dll.dc1394_feature_set_absolute_control.argtypes = [POINTER(camera_t),feature_t, switch_t]
_dll.dc1394_feature_set_absolute_control.restype = error_t
_dll.dc1394_feature_set_absolute_control.errcheck = _errcheck


#get/set Feature mode:
_dll.dc1394_feature_get_modes.argtypes=[POINTER(camera_t),feature_t, POINTER(feature_modes_t)]
_dll.dc1394_feature_get_modes.restype = error_t
_dll.dc1394_feature_get_modes.errcheck = _errcheck

_dll.dc1394_feature_get_mode.argtypes = [POINTER(camera_t),feature_t, POINTER(feature_mode_t)]
_dll.dc1394_feature_get_mode.restype = error_t
_dll.dc1394_feature_get_mode.errcheck = _errcheck

_dll.dc1394_feature_set_mode.argtypes = [POINTER(camera_t),feature_t, feature_mode_t]
_dll.dc1394_feature_set_mode.restype = error_t
_dll.dc1394_feature_set_mode.errcheck = _errcheck

###################################################################################
# Trigger:

#Sets the polarity of the external trigger
_dll.dc1394_external_trigger_set_polarity.argtypes = [ POINTER(camera_t), trigger_polarity_t ]
_dll.dc1394_external_trigger_set_polarity.restype = error_t
_dll.dc1394_external_trigger_set_polarity.errcheck = _errcheck

#Gets the polarity of the external trigger
_dll.dc1394_external_trigger_get_polarity.argtypes = [ POINTER(camera_t), POINTER(trigger_polarity_t) ]
_dll.dc1394_external_trigger_get_polarity.restype = error_t
_dll.dc1394_external_trigger_get_polarity.errcheck = _errcheck

#Tells whether the external trigger can change its polarity or not
_dll.dc1394_external_trigger_has_polarity.argtypes = [ POINTER(camera_t), POINTER(bool_t)]
_dll.dc1394_external_trigger_has_polarity.restype = error_t
_dll.dc1394_external_trigger_has_polarity.errcheck = _errcheck

#Switch between internal and external trigger
_dll.dc1394_external_trigger_set_power.argtypes = [POINTER(camera_t), switch_t ]
_dll.dc1394_external_trigger_set_power.restype = error_t
_dll.dc1394_external_trigger_set_power.errcheck = _errcheck

#Gets the status of the external trigger
_dll.dc1394_external_trigger_get_power.restype = error_t
_dll.dc1394_external_trigger_get_power.argtypes = [ POINTER(camera_t), POINTER(switch_t)]
_dll.dc1394_external_trigger_get_power.errcheck = _errcheck

# Sets the external trigger mode
_dll.dc1394_external_trigger_set_mode.restype = error_t
_dll.dc1394_external_trigger_set_mode.argtypes = [POINTER(camera_t), trigger_mode_t]
_dll.dc1394_external_trigger_set_mode.errcheck = _errcheck

#Gets the external trigger mode
_dll.dc1394_external_trigger_get_mode.restype = error_t
_dll.dc1394_external_trigger_get_mode.argtypes = [POINTER(camera_t), POINTER(trigger_mode_t)]
_dll.dc1394_external_trigger_get_mode.errcheck = _errcheck

# Sets the external trigger source
_dll.dc1394_external_trigger_set_source.restype = error_t
_dll.dc1394_external_trigger_set_source.argtypes = [POINTER(camera_t), trigger_source_t]
_dll.dc1394_external_trigger_set_source.errcheck = _errcheck

#Gets the external trigger source
_dll.dc1394_external_trigger_get_source.restype =error_t
_dll.dc1394_external_trigger_get_source.argtypes = [POINTER(camera_t),POINTER(trigger_source_t) ]
_dll.dc1394_external_trigger_get_source.errcheck = _errcheck

#Gets the list of available external trigger source
_dll.dc1394_external_trigger_get_supported_sources.restype =error_t
_dll.dc1394_external_trigger_get_supported_sources.argtypes = [POINTER(camera_t),POINTER(trigger_sources_t) ]
_dll.dc1394_external_trigger_get_supported_sources.errcheck = _errcheck

#Turn software trigger on or off
_dll.dc1394_software_trigger_set_power.restype = error_t
_dll.dc1394_software_trigger_set_power.argtypes = [POINTER( camera_t ), switch_t]
_dll.dc1394_software_trigger_set_power.errcheck = _errcheck

#ets the state of software trigger
_dll.dc1394_software_trigger_get_power.restype = error_t
_dll.dc1394_software_trigger_get_power.argtypes = [POINTER(camera_t ), POINTER(switch_t)]
_dll.dc1394_software_trigger_get_power.errcheck = _errcheck

##########################################################################################
# PIO, SIO and Strobe Functions
# Sends a quadlet on the PIO (output)
_dll.dc1394_pio_set.restype = error_t
_dll.dc1394_pio_set.argtypes = [POINTER(camera_t ), c_uint32 ]
_dll.dc1394_pio_set.errcheck = _errcheck

#Gets the current quadlet at the PIO (input)
_dll.dc1394_pio_get.restype = error_t
_dll.dc1394_pio_get.argtypes = [POINTER( camera_t),POINTER(c_uint32 )]
_dll.dc1394_pio_get.errcheck = _errcheck

#Other functionalities
#reset a camera to factory default settings
_dll.dc1394_camera_reset.restype = error_t
_dll.dc1394_camera_reset.argtypes = [POINTER(camera_t) ]
_dll.dc1394_camera_reset.errcheck = _errcheck

#turn a camera on or off
_dll.dc1394_camera_set_power.restype = error_t
_dll.dc1394_camera_set_power.argtypes = [POINTER(camera_t ), switch_t ]
_dll.dc1394_camera_set_power.errcheck = _errcheck

#Download a camera setup from the memory
_dll.dc1394_memory_busy.restype = error_t
_dll.dc1394_memory_busy.argtypes = [POINTER(camera_t), POINTER(bool_t)]
_dll.dc1394_memory_busy.errcheck = _errcheck

#Uploads a camera setup in the memory
#Note that this operation can only be performed a certain number of
#times for a given camera, as it requires reprogramming of an EEPROM.

_dll.dc1394_memory_save.restype = error_t
_dll.dc1394_memory_save.argtypes = [POINTER(camera_t ), c_uint32 ]
_dll.dc1394_memory_save.errcheck = _errcheck

#Tells whether the writing of the camera setup in memory is finished or not
_dll.dc1394_memory_load.restype = error_t
_dll.dc1394_memory_load.argtypes = [POINTER(camera_t), c_uint32 ]
_dll.dc1394_memory_load.errcheck = _errcheck

###############################
# VIDEO FUNCTIONS from video.h
###############################
#Gets a list of video modes supported by the camera
_dll.dc1394_video_get_supported_modes.argtypes = [ c_void_p, POINTER(video_modes_t) ]
_dll.dc1394_video_get_supported_modes.restype = error_t
_dll.dc1394_video_get_supported_modes.errcheck = _errcheck

#ets a list of supported video framerates for a given video mode.
#This function only works with non-scalable formats
_dll.dc1394_video_get_supported_framerates.restype = error_t
_dll.dc1394_video_get_supported_framerates.argtypes = [POINTER(camera_t), video_mode_t, POINTER(framerates_t) ]
_dll.dc1394_video_get_supported_framerates.errcheck = _errcheck

#Gets the current framerate. This is meaningful only if the video mode is not scalable
_dll.dc1394_video_get_framerate.restype = error_t
_dll.dc1394_video_get_framerate.argtypes = [ POINTER(camera_t), POINTER(framerate_t )]
_dll.dc1394_video_get_framerate.errcheck = _errcheck

#Sets the current framerate. This is meaningful only if the video mode is not scalable
_dll.dc1394_video_set_framerate.restype = error_t
_dll.dc1394_video_set_framerate.argtypes = [POINTER(camera_t), framerate_t ]
_dll.dc1394_video_set_framerate.errcheck = _errcheck

#Gets the current vide mode
_dll.dc1394_video_get_mode.restype = error_t
_dll.dc1394_video_get_mode.argtypes = [ POINTER(camera_t), POINTER(video_mode_t )]
_dll.dc1394_video_get_mode.errcheck = _errcheck

#Sets the current vide mode
_dll.dc1394_video_set_mode.restype = error_t
_dll.dc1394_video_set_mode.argtypes = [POINTER(camera_t), video_mode_t ]
_dll.dc1394_video_set_mode.errcheck = _errcheck

#Gets the current operation mode
_dll.dc1394_video_get_operation_mode.argtypes = [ c_void_p, POINTER(c_int) ]
_dll.dc1394_video_get_operation_mode.restype = error_t
_dll.dc1394_video_get_operation_mode.errcheck = _errcheck

#Sets the current operation mode
_dll.dc1394_video_set_operation_mode.restype = error_t
_dll.dc1394_video_set_operation_mode.argtypes = [ c_void_p, c_int]
_dll.dc1394_video_set_operation_mode.errcheck = _errcheck

#Gets the current ISO speed
_dll.dc1394_video_get_iso_speed.restype = error_t
_dll.dc1394_video_get_iso_speed.argtypes = [POINTER(camera_t),POINTER( speed_t )]
_dll.dc1394_video_get_iso_speed.errcheck = _errcheck

#Sets the current ISO speed. Speeds over 400Mbps require 1394B
_dll.dc1394_video_set_iso_speed.restype = error_t
_dll.dc1394_video_set_iso_speed.argtypes = [POINTER(camera_t), speed_t ]
_dll.dc1394_video_set_iso_speed.errcheck = _errcheck

#Gets the current ISO channel
_dll.dc1394_video_get_iso_channel.restype = error_t
_dll.dc1394_video_get_iso_channel.argtypes = [POINTER(camera_t),POINTER(c_uint32)]
_dll.dc1394_video_get_iso_channel.errcheck = _errcheck

#Sets the current ISO channel
_dll.dc1394_video_set_iso_channel.restype = error_t
_dll.dc1394_video_set_iso_channel.argtypes = [POINTER(camera_t), c_uint32 ]
_dll.dc1394_video_set_iso_channel.errcheck = _errcheck

#Gets the current data depth, in bits. Only meaningful for 16bpp video modes (RAW16, RGB48, MONO16,...)
_dll.dc1394_video_get_data_depth.restype = error_t
_dll.dc1394_video_get_data_depth.argtypes = [POINTER(camera_t), POINTER(c_uint32) ]
_dll.dc1394_video_get_data_depth.errcheck = _errcheck

#Starts/stops the isochronous data transmission. In other words, use this to control the image flow
_dll.dc1394_video_set_transmission.restypes = error_t
_dll.dc1394_video_set_transmission.argtypes = [ c_void_p, c_int ]
_dll.dc1394_video_set_transmission.errcheck = _errcheck

#Gets the status of the video transmission
_dll.dc1394_video_get_transmission.restype = error_t
_dll.dc1394_video_get_transmission.argtypes = [POINTER(camera_t), POINTER(switch_t)]
_dll.dc1394_video_get_transmission.errcheck = _errcheck

#Turns one-shot mode on or off
_dll.dc1394_video_set_one_shot.restype = error_t
_dll.dc1394_video_set_one_shot.argtype = [POINTER(camera_t), switch_t]
_dll.dc1394_video_set_one_shot.errcheck = _errcheck

#Gets the status of the one-shot mode
_dll.dc1394_video_get_one_shot.restype = error_t
_dll.dc1394_video_get_one_shot.argtypes = [POINTER(camera_t), POINTER(bool_t)]
_dll.dc1394_video_get_one_shot.errcheck = _errcheck

#Turns multishot mode on or off
_dll.dc1394_video_set_multi_shot.restype = error_t
_dll.dc1394_video_set_multi_shot.argtypes =[POINTER(camera_t), c_uint32, switch_t]
_dll.dc1394_video_set_multi_shot.errcheck = _errcheck

#Gets the status of the multi-shot mode
_dll.dc1394_video_get_multi_shot.restype = error_t
_dll.dc1394_video_get_multi_shot.argtypes = [POINTER(camera_t), POINTER(bool_t), POINTER(c_uint32)]
_dll.dc1394_video_get_multi_shot.errcheck = _errcheck

#Gets the bandwidth usage of a camera.
## This function returns the bandwidth that is used by the camera *IF* ISO was ON.
## The returned value is in bandwidth units. The 1394 bus has 4915 bandwidth units
## available per cycle. Each unit corresponds to the time it takes to send one
## quadlet at ISO speed S1600. The bandwidth usage at S400 is thus four times the
## number of quadlets per packet. Thanks to Krisitian Hogsberg for clarifying this.
_dll.dc1394_video_get_bandwidth_usage.restype = error_t
_dll.dc1394_video_get_bandwidth_usage.argtypes = [POINTER(camera_t),POINTER(c_uint32)]
_dll.dc1394_video_get_bandwidth_usage.errcheck = _errcheck

################################
# CAPTURE functions, capture.h
################################
#Setup the capture, using a ring buffer of a certain size (num_dma_buffers) and
# certain options (flags)
_dll.dc1394_capture_setup.argtypes = [ POINTER(camera_t), c_uint32, c_uint32 ]
_dll.dc1394_capture_setup.restype = error_t
_dll.dc1394_capture_setup.errcheck = _errcheck

#Stop the capture
_dll.dc1394_capture_stop.argtypes = [ POINTER(camera_t) ]
_dll.dc1394_capture_stop.restype = error_t
_dll.dc1394_capture_stop.errcheck = _errcheck

#Gets a file descriptor to be used for select(). Must be called after dc1394_capture_setup()
#Error check can do nothing with this one;
#we also do not really need this, since we do not want to dump files from the C library.
_dll.dc1394_capture_get_fileno.restype =  c_int
_dll.dc1394_capture_get_fileno.argtypes =[ POINTER(camera_t) ]

#Captures a video frame. The returned struct contains the image buffer, among others.
# This image buffer SHALL NOT be freed, as it represents an area
# in the memory that belongs to the system.
_dll.dc1394_capture_dequeue.restype = error_t
_dll.dc1394_capture_dequeue.argtypes = [ POINTER(camera_t), c_int, POINTER(POINTER(video_frame_t)) ]
_dll.dc1394_capture_dequeue.errcheck = _errcheck

#Returns a frame to the ring buffer once it has been used.
_dll.dc1394_capture_enqueue.restype = error_t
_dll.dc1394_capture_enqueue.argtypes = [ POINTER(camera_t), POINTER(video_frame_t) ]
_dll.dc1394_capture_enqueue.errcheck = _errcheck

#Returns DC1394_TRUE if the given frame (previously dequeued) has been detected to be
# corrupt (missing data, corrupted data, overrun buffer, etc.). Note that certain types
# of corruption may go undetected in which case DC1394_FALSE will be returned.  The
# ability to detect corruption also varies between platforms.  Note that corrupt frames
# still need to be enqueued with dc1394_capture_enqueue() when no longer needed by the user.
_dll.dc1394_capture_is_frame_corrupt.restype = bool_t
_dll.dc1394_capture_is_frame_corrupt.argtypes = [ POINTER(camera_t), POINTER(video_frame_t) ]

#####################################################################
# Conversion (covert.h)
#####################################################################
#parameters: *source, *dest, width, height, source_color_coding, bits
_dll.dc1394_convert_to_YUV422.restype = error_t
_dll.dc1394_convert_to_YUV422.argtypes = [ POINTER(c_uint8), POINTER( c_uint8), c_uint32, \
                                        c_uint32, c_uint32, color_coding_t, c_uint32 ]
_dll.dc1394_convert_to_YUV422.errcheck = _errcheck

#Converts an image buffer to MONO8
_dll.dc1394_convert_to_MONO8.restype = error_t
_dll.dc1394_convert_to_MONO8.argtypes = [ POINTER(c_uint8), POINTER( c_uint8), c_uint32, \
                                        c_uint32, c_uint32, color_coding_t, c_uint32 ]
_dll.dc1394_convert_to_MONO8.errcheck = _errcheck

#Converts an image buffer to RGB8
_dll.dc1394_convert_to_RGB8.restype = error_t
_dll.dc1394_convert_to_RGB8.argtypes = [ POINTER(c_uint8), POINTER( c_uint8), c_uint32, \
                                        c_uint32, c_uint32, color_coding_t, c_uint32 ]
_dll.dc1394_convert_to_RGB8.errcheck = _errcheck


#####################################################################
#CONVERSION FUNCTIONS FOR STEREO IMAGES
#####################################################################
# changes a 16bit stereo image (8bit/channel) into two 8bit images on top of each other
_dll.dc1394_deinterlace_stereo.restype = error_t
_dll.dc1394_deinterlace_stereo.argtypes = [ POINTER(c_uint8), POINTER( c_uint8), c_uint32, \
                                        c_uint32 ]
_dll.dc1394_deinterlace_stereo.errcheck = _errcheck

##################################################################################################
# Color conversion functions for cameras that can output raw Bayer pattern images
# (color codings DC1394_COLOR_CODING_RAW8 and DC1394_COLOR_CODING_RAW16)
#	Credits and sources:
#		- Nearest Neighbor : OpenCV library
#		- Bilinear         : OpenCV library
#		- HQLinear         : High-Quality Linear Interpolation For Demosaicing Of Bayer-Patterned
#								Color Images, by Henrique S. Malvar, Li-wei He, and Ross Cutler,
#								in Proceedings of the ICASSP'04 Conference.
#		- Edge Sense II    : Laroche, Claude A. "Apparatus and method for adaptively interpolating
#								a full color image utilizing chrominance gradients"
#								U.S. Patent 5,373,322. Based on the code found on the website
#								http://www-ise.stanford.edu/~tingchen/ Converted to C and adapted
#								to all four elementary patterns.
#		- Downsample       : "Known to the Ancients"
#		- Simple           : Implemented from the information found in the manual of Allied Vision
#								Technologies (AVT) cameras.
#		- VNG              : Variable Number of Gradients, a method described in
#								http://www-ise.stanford.edu/~tingchen/algodep/vargra.html
#								Sources import from DCRAW by Frederic Devernay. DCRAW is a RAW
#								converter program by Dave Coffin. URL:
#								http://www.cybercom.net/~dcoffin/dcraw/
#		- AHD              : Adaptive Homogeneity-Directed Demosaicing Algorithm, by K. Hirakawa
#								and T.W. Parks, IEEE Transactions on Image Processing, Vol. 14,
#								Nr. 3, March 2005, pp. 360 - 369.
##################################################################################################
# Perform de-mosaicing on an 8-bit image buffer
# parameters: uint16_t *bayer, uint16_t *rgb, uint32_t width, uint32_t height,
# color_filter_t tile, bayer_method_t method
_dll.dc1394_bayer_decoding_8bit.restype = error_t
_dll.dc1394_bayer_decoding_8bit.argtypes = [ POINTER(c_uint8), POINTER(c_uint8), c_uint32,\
                                            c_uint32, color_filter_t, bayer_method_t ]
_dll.dc1394_bayer_decoding_8bit.errcheck = _errcheck

# Perform de-mosaicing on an 16-bit image buffer
# parameters: uint16_t *bayer, uint16_t *rgb, uint32_t width, uint32_t height,
# color_filter_t tile, bayer_method_t method, uint32_t bits
_dll.dc1394_bayer_decoding_16bit.restype = error_t
_dll.dc1394_bayer_decoding_16bit.argtypes = [ POINTER(c_uint8), POINTER(c_uint8), c_uint32,\
                                            c_uint32, color_filter_t, bayer_method_t, c_uint32 ]
_dll.dc1394_bayer_decoding_16bit.errcheck = _errcheck

##################################################################################################
#Frame based conversions
# Converts the format of a video frame.
# To set the format of the output, simply set the values of the corresponding fields
# in the output frame
# parameters: inframe and outframe
_dll.dc1394_convert_frames.restype = error_t
_dll.dc1394_convert_frames.argtypes = [ POINTER(video_frame_t), POINTER(video_frame_t) ]
_dll.dc1394_convert_frames.errcheck = _errcheck

#De-mosaicing of a Bayer-encoded video frame
#To set the format of the output, simply set the values of the corresponding fields
# in the output frame
_dll.dc1394_debayer_frames.restype = error_t
_dll.dc1394_debayer_frames.argtypes = [ POINTER(video_frame_t), POINTER(video_frame_t),\
                                        bayer_method_t ]
_dll.dc1394_debayer_frames.errcheck = _errcheck

# De-interlacing of stereo data for cideo frames
# To set the format of the output, simply set the values of the corresponding fields
# in the output frame
_dll.dc1394_deinterlace_stereo_frames.restype = error_t
_dll.dc1394_deinterlace_stereo_frames.argtypes = [POINTER(video_frame_t), POINTER(video_frame_t),\
                                            stereo_method_t ]
_dll.dc1394_deinterlace_stereo_frames.errcheck = _errcheck

#####################################################################################
# REGISTER FUNCTIONS (register.h)
#####################################################################################
# for these functions there is no documentation available in the include files
#parameters: *camera, offset, *value, num_register
_dll.dc1394_get_registers.restype = error_t
_dll.dc1394_get_registers.argtypes = [ POINTER(camera_t), c_uint64, POINTER(c_uint32), c_uint32 ]
_dll.dc1394_get_registers.errcheck = _errcheck

_dll.dc1394_set_registers.restype = error_t
_dll.dc1394_set_registers.argtypes = [ POINTER(camera_t), c_uint64, POINTER(c_uint32), c_uint32 ]
_dll.dc1394_set_registers.errcheck = _errcheck
#get_register = _dll.dc1394_get_registers(camera, offset, &value, 1)
#set_register = _dll.dc1394_set_registers(camera, offset, &value, 1)

#Get/Set command registers (parameters as above):
_dll.dc1394_get_control_registers.restype = error_t
_dll.dc1394_get_control_registers.argtypes = [ POINTER(camera_t), c_uint64, POINTER(c_uint32),\
                                                c_uint32 ]
_dll.dc1394_get_control_registers.errcheck = _errcheck

_dll.dc1394_set_control_registers.restype = error_t
_dll.dc1394_set_control_registers.argtypes = [ POINTER(camera_t), c_uint64, POINTER(c_uint32),\
                                                c_uint32 ]
_dll.dc1394_set_control_registers.errcheck = _errcheck
#get/set control register: the same with last parameter = 1.

#Get/Set advanced features register (parameters as above):
_dll.dc1394_get_adv_control_registers.restype = error_t
_dll.dc1394_get_adv_control_registers.argtypes = [ POINTER(camera_t), c_uint64, POINTER(c_uint32),\
                                                c_uint32 ]
_dll.dc1394_get_adv_control_registers.errcheck = _errcheck

_dll.dc1394_set_adv_control_registers.restype = error_t
_dll.dc1394_set_adv_control_registers.argtypes = [ POINTER(camera_t), c_uint64, POINTER(c_uint32),\
                                                c_uint32 ]
_dll.dc1394_set_adv_control_registers.errcheck = _errcheck
#get/set_advanced_control_register: calling with num_register=1

#get/set FORMAT7 registers:
#parameters: &camera, mode, offset, &value:
_dll.dc1394_get_format7_register.restype = error_t
_dll.dc1394_get_format7_register.argtypes = [ POINTER(camera_t), c_uint, c_uint64,\
                            POINTER(c_uint32) ]
_dll.dc1394_get_format7_register.errcheck = _errcheck

_dll.dc1394_set_format7_register.restype = error_t
_dll.dc1394_set_format7_register.argtypes = [ POINTER(camera_t), c_uint, c_uint64,\
                                            c_uint32]
_dll.dc1394_set_format7_register.errcheck = _errcheck

#Get/Set Absolute Control Registers
#parameters &camera, feature, offset, &value
_dll.dc1394_get_absolute_register.restype = error_t
_dll.dc1394_get_absolute_register.argtypes = [ POINTER(camera_t), c_uint, c_uint64,\
                                            POINTER(c_uint32) ]
_dll.dc1394_get_absolute_register.errcheck = _errcheck

_dll.dc1394_set_absolute_register.restype = error_t
_dll.dc1394_set_absolute_register.argtypes = [ POINTER(camera_t), c_uint, c_uint64,\
                                            c_uint32]
_dll.dc1394_set_absolute_register.errcheck = _errcheck

#Get/Set PIO Feature Registers
#params: &camera, offset, &value
_dll.dc1394_get_PIO_register.restype = error_t
_dll.dc1394_get_PIO_register.argtypes = [ POINTER(camera_t), c_uint64,POINTER(c_uint32) ]
_dll.dc1394_get_PIO_register.errcheck = _errcheck

_dll.dc1394_set_PIO_register.restype = error_t
_dll.dc1394_set_PIO_register.argtypes = [ POINTER(camera_t), c_uint64, c_uint32 ]
_dll.dc1394_set_PIO_register.errcheck = _errcheck

# Get/Set SIO Feature Registers
_dll.dc1394_get_SIO_register.restype = error_t
_dll.dc1394_get_SIO_register.argtypes = [ POINTER(camera_t), c_uint64,POINTER(c_uint32) ]
_dll.dc1394_get_SIO_register.errcheck = _errcheck

_dll.dc1394_set_SIO_register.restype = error_t
_dll.dc1394_set_SIO_register.argtypes = [ POINTER(camera_t), c_uint64, c_uint32 ]
_dll.dc1394_set_SIO_register.errcheck = _errcheck

# Get/Set Strobe Feature Registers
#params: &camera, offset, &value
_dll.dc1394_get_strobe_register.restype = error_t
_dll.dc1394_get_strobe_register.argtypes = [ POINTER(camera_t), c_uint64,POINTER(c_uint32) ]
_dll.dc1394_get_strobe_register.errcheck = _errcheck

_dll.dc1394_set_strobe_register.restype = error_t
_dll.dc1394_set_strobe_register.argtypes = [ POINTER(camera_t), c_uint64, c_uint32 ]
_dll.dc1394_set_strobe_register.errcheck = _errcheck

######################
# FORMAT 7 FUNCTIONS #
######################

#Gets the maximal image size for a given mode.
#parameters: &camera, video_mode, &hsize, &vsize:
_dll. dc1394_format7_get_max_image_size.restype = error_t
_dll. dc1394_format7_get_max_image_size.argtypes = [ POINTER(camera_t), video_mode_t,\
                                        POINTER( c_uint32), POINTER(c_uint32) ]
_dll. dc1394_format7_get_max_image_size.errcheck = _errcheck


#Gets the unit sizes for a given mode. The image size can only be a multiple
# of the unit size, and cannot be smaller than it.
#parameters: &camera, video_mode, &h_unit, &v_unit
_dll.dc1394_format7_get_unit_size.restype = error_t
_dll.dc1394_format7_get_unit_size.argtypes = [ POINTER(camera_t), video_mode_t,\
                                            POINTER( c_uint32), POINTER(c_uint32) ]
_dll.dc1394_format7_get_unit_size.errcheck = _errcheck


#Gets the current image size
_dll.dc1394_format7_get_image_size.restype = error_t
_dll.dc1394_format7_get_image_size.argtypes = [ POINTER(camera_t), video_mode_t,\
                                            POINTER( c_uint32), POINTER(c_uint32) ]
_dll.dc1394_format7_get_image_size.errcheck = _errcheck

#Sets the current image size
_dll.dc1394_format7_set_image_size.restype = error_t
_dll.dc1394_format7_set_image_size.argtypes = [ POINTER(camera_t), video_mode_t,\
                                            c_uint32, c_uint32 ]
_dll.dc1394_format7_set_image_size.errcheck = _errcheck


#Image position
#Gets the current image position
#parameters: &camera, video_mode, &left, &top
_dll.dc1394_format7_get_image_position.restype = error_t
_dll.dc1394_format7_get_image_position.argtypes = [ POINTER(camera_t), video_mode_t,\
                                            POINTER( c_uint32), POINTER(c_uint32) ]
_dll.dc1394_format7_get_image_position.errcheck = _errcheck

#Set image position:
_dll.dc1394_format7_set_image_position.restype = error_t
_dll.dc1394_format7_set_image_position.argtypes = [ POINTER(camera_t), video_mode_t,\
                                             c_uint32, c_uint32 ]
_dll.dc1394_format7_set_image_position.errcheck = _errcheck

#Gets the unit positions for a given mode. The image position can
#only be a multiple of the unit position (zero is acceptable).
#parameters: &camera, video_mode, &h_unit, &v_unit
_dll.dc1394_format7_get_unit_position.restype = error_t
_dll.dc1394_format7_get_unit_position.argtypes = [ POINTER(camera_t), video_mode_t,\
                                            POINTER( c_uint32), POINTER(c_uint32) ]
_dll.dc1394_format7_get_unit_position.errcheck = _errcheck

#color coding:
#Gets the current color coding
_dll.dc1394_format7_get_color_coding.restype = error_t
_dll.dc1394_format7_get_color_coding.argtypes = [ POINTER(camera_t), video_mode_t,\
                                                POINTER(color_coding_t) ]
_dll.dc1394_format7_get_color_coding.errcheck = _errcheck

#Gets the list of color codings available for this mode
_dll.dc1394_format7_get_color_codings.restype = error_t
_dll.dc1394_format7_get_color_codings.argtypes = [ POINTER(camera_t), video_mode_t,\
                                                POINTER(color_codings_t) ]
_dll.dc1394_format7_get_color_codings.errcheck = _errcheck

#Sets the current color coding
_dll.dc1394_format7_set_color_coding.restype = error_t
_dll.dc1394_format7_set_color_coding.argtypes = [ POINTER(camera_t), video_mode_t,\
                                                color_coding_t ]
_dll.dc1394_format7_set_color_coding.errcheck = _errcheck

#Gets the current color filter
_dll.dc1394_format7_get_color_filter.restype = error_t
_dll.dc1394_format7_get_color_filter.argtypes = [ POINTER(camera_t), video_mode_t,\
                                        POINTER(color_filter_t) ]
_dll.dc1394_format7_get_color_filter.errcheck = _errcheck

#packet
# Get the parameters of the packet size: its maximal size and its unit size.
# The packet size is always a multiple of the unit bytes and cannot be zero.
#parameters: &camera, video_mode, &unit_bytes, &max_bytes
_dll.dc1394_format7_get_packet_parameters.restype = error_t
_dll.dc1394_format7_get_packet_parameters.argtypes = [ POINTER(camera_t), video_mode_t,\
                                            POINTER( c_uint32), POINTER(c_uint32) ]
_dll.dc1394_format7_get_packet_parameters.errcheck = _errcheck

#Gets the current packet size
#parameters: &camera, video_mode, &packet size
_dll.dc1394_format7_get_packet_size.restype = error_t
_dll.dc1394_format7_get_packet_size.argtypes = [ POINTER(camera_t), video_mode_t,\
                                            POINTER( c_uint32 ) ]
_dll.dc1394_format7_get_packet_size.errcheck = _errcheck

#Sets the current packet size
_dll.dc1394_format7_set_packet_size.restype = error_t
_dll.dc1394_format7_set_packet_size.argtypes = [ POINTER(camera_t), video_mode_t,\
                                            c_uint32 ]
_dll.dc1394_format7_set_packet_size.errcheck = _errcheck

#Gets the recommended packet size. Ignore if zero.
#parameters: &camera, video_mode, &packet size
_dll.dc1394_format7_get_recommended_packet_size.restype = error_t
_dll.dc1394_format7_get_recommended_packet_size.argtypes = [ POINTER(camera_t), video_mode_t,\
                                            POINTER( c_uint32 ) ]
_dll.dc1394_format7_get_recommended_packet_size.errcheck = _errcheck

#Gets the number of packets per frame.
#parameters: &camera, video_mode, &packets per frame
_dll.dc1394_format7_get_packets_per_frame.restype = error_t
_dll.dc1394_format7_get_packets_per_frame.argtypes = [ POINTER(camera_t), video_mode_t,\
                                            POINTER( c_uint32 ) ]
_dll.dc1394_format7_get_packets_per_frame.errcheck = _errcheck

#Gets the data depth (e.g. 12, 13, 14 bits/pixel)
#parameters: &camera, video_mode, &data_depth
_dll.dc1394_format7_get_data_depth.restype = error_t
_dll.dc1394_format7_get_data_depth.argtypes = [ POINTER(camera_t), video_mode_t,\
                                            POINTER( c_uint32 ) ]
_dll.dc1394_format7_get_data_depth.errcheck = _errcheck

#Gets the frame interval in float format
#parameters: &camera, video_mode, &interval
_dll.dc1394_format7_get_frame_interval.restype = error_t
_dll.dc1394_format7_get_frame_interval.argtypes = [ POINTER(camera_t), video_mode_t,\
                                            POINTER( c_float ) ]
_dll.dc1394_format7_get_frame_interval.errcheck = _errcheck

#Gets the number of pixels per image frame
#parameters: &camera, video_mode, &pixnum
_dll.dc1394_format7_get_pixel_number.restype = error_t
_dll.dc1394_format7_get_pixel_number.argtypes = [ POINTER(camera_t), video_mode_t,\
                                            POINTER( c_uint32 ) ]
_dll.dc1394_format7_get_pixel_number.errcheck = _errcheck

#Get the total number of bytes per frame. This includes padding
#(to reach an entire number of packets)
#parameters: &camera, video_mode, &total_bytes
_dll.dc1394_format7_get_total_bytes.restype = error_t
_dll.dc1394_format7_get_total_bytes.argtypes = [ POINTER(camera_t), video_mode_t,\
                                            POINTER( c_uint64) ]
_dll.dc1394_format7_get_total_bytes.errcheck = _errcheck

#These functions get the properties of (one or all) format7 mode(s)
#Gets the properties of all Format_7 modes supported by the camera.
_dll.dc1394_format7_get_modeset.restype = error_t
_dll.dc1394_format7_get_modeset.argtypes = [ POINTER(camera_t), POINTER(format7modeset_t)]
_dll.dc1394_format7_get_modeset.errcheck = _errcheck


#Gets the properties of a Format_7 mode
_dll.dc1394_format7_get_mode_info.restype = error_t
_dll.dc1394_format7_get_mode_info.argtypes = [ POINTER(camera_t), video_mode_t,\
                                                POINTER(format7mode_t)]
_dll.dc1394_format7_get_mode_info.errcheck = _errcheck

#Joint function that fully sets a certain ROI taking all parameters into account.
# Note that this function does not SWITCH to the video mode passed as argument,
# it mearly sets it
#parameters: &camera, video_mode, color_coding, packet_size, left, top, width, height
_dll.dc1394_format7_set_roi.restype = error_t
_dll.dc1394_format7_set_roi.argtypes = [ POINTER(camera_t), video_mode_t, color_coding_t,\
                                        c_int32, c_int32, c_int32, c_int32, c_int32 ]
_dll.dc1394_format7_set_roi.errcheck = _errcheck


_dll.dc1394_format7_get_roi.restype = error_t
_dll.dc1394_format7_get_roi.argtypes = [ POINTER(camera_t), video_mode_t, POINTER(color_coding_t),\
                                        POINTER(c_int32), POINTER(c_int32), POINTER(c_int32),\
                                        POINTER(c_int32), POINTER(c_int32) ]
_dll.dc1394_format7_get_roi.errcheck = _errcheck


#####################################################################################
# utilities (utils.h)
#####################################################################################
# Returns the image width and height (in pixels) corresponding to a video mode.
# Works for scalable and non-scalable video modes.
# parameters: &camera, video_mode, &width, &height
_dll.dc1394_get_image_size_from_video_mode.restype = error_t
_dll.dc1394_get_image_size_from_video_mode.argtypes = [ POINTER(camera_t), video_mode_t,\
                                        POINTER(c_int32), POINTER(c_int32) ]
_dll.dc1394_get_image_size_from_video_mode.errcheck = _errcheck


#Returns the given framerate as a float
_dll.dc1394_framerate_as_float.restype = error_t
_dll.dc1394_framerate_as_float.argtypes = [ framerate_t, POINTER(c_float)]
_dll.dc1394_framerate_as_float.errcheck = _errcheck

#Returns the number of bits per pixel for a certain color coding. This is the size
# of the data sent on the bus, the effective data depth may vary. Example: RGB16 is 16,
# YUV411 is 8, YUV422 is 8
_dll.dc1394_get_color_coding_data_depth.restype = error_t
_dll.dc1394_get_color_coding_data_depth.argtypes = [ color_coding_t, POINTER(c_uint32)]
_dll.dc1394_get_color_coding_data_depth.errcheck = _errcheck

#Returns the bit-space used by a pixel. This is different from the data depth! For instance,
# RGB16 has a bit space of 48 bits, YUV422 is 16bits and YU411 is 12bits.
_dll.dc1394_get_color_coding_bit_size.restype = error_t
_dll.dc1394_get_color_coding_bit_size.argtypes = [ color_coding_t, POINTER(c_uint32)]
_dll.dc1394_get_color_coding_bit_size.errcheck = _errcheck

#Returns the color coding from the video mode. Works with scalable image formats too.
_dll.dc1394_get_color_coding_from_video_mode.restype = error_t
_dll.dc1394_get_color_coding_from_video_mode.argtypes = [ POINTER(camera_t), video_mode_t,\
                                                        POINTER(color_coding_t) ]
_dll.dc1394_get_color_coding_from_video_mode.errcheck = _errcheck

#Tells whether the color mode is color or monochrome
_dll.dc1394_is_color.restype = error_t
_dll.dc1394_is_color.argtypes = [ color_coding_t, POINTER(bool_t)]
_dll.dc1394_is_color.errcheck = _errcheck

#Tells whether the video mode is scalable or not.
_dll.dc1394_is_video_mode_scalable.restype = bool_t
_dll.dc1394_is_video_mode_scalable.argtypes = [ video_mode_t ]


#Tells whether the video mode is "still image" or not ("still image" is
# currently not supported by any cameras on the market)
_dll.dc1394_is_video_mode_still_image.restype = bool_t
_dll.dc1394_is_video_mode_still_image.argtypes = [ video_mode_t ]

#Tells whether two IDs refer to the same physical camera unit.
_dll.dc1394_is_same_camera.restype = bool_t
_dll.dc1394_is_same_camera.argtypes = [ camera_id_t, camera_id_t ]

#Returns a descriptive name for a feature
_dll.dc1394_feature_get_string.restype = c_char_p
_dll.dc1394_feature_get_string.argtypes = [feature_t ]

#Returns a descriptive string for an error code
_dll.dc1394_error_get_string.restype = c_char_p
_dll.dc1394_error_get_string.argtypes = [error_t]

#Calculates the CRC16 checksum of a memory region. Useful to verify the CRC of
# an image buffer, for instance.
#parameters: &buffer, buffer_size
_dll.dc1394_checksum_crc16.restype = c_uint16
_dll.dc1394_checksum_crc16.argtypes = [ POINTER(c_uint8), c_uint32 ]


#####################################################################################
# ISO commangs (iso.h)
#####################################################################################
#dc1394_iso_set_persist
#param camera A camera handle.
# Calling this function will cause isochronous channel and bandwidth allocations to persist
# beyond the lifetime of this dc1394camera_t instance.  Normally (when this function is not
# called), any allocations would be automatically released upon freeing this camera or a
# premature shutdown of the application (if possible).  For this function to be used, it
# must be called prior to any allocations or an error will be returned.
_dll.dc1394_iso_set_persist.restype = error_t
_dll.dc1394_iso_set_persist.argtypes = [ POINTER( camera_t) ]
_dll.dc1394_iso_set_persist.errcheck = _errcheck

#dc1394_iso_allocate_channel:
#param &camera , channels_allowed, &channel
#channels_allowed: A bitmask of acceptable channels for the allocation. The LSB corresponds
# to channel 0 and the MSB corresponds to channe 63.  Only channels whose bit is set will
# be considered for the allocation If \a channels_allowed = 0, the complete set of channels
# supported by this camera will be considered for the allocation.
#Allocates an isochronous channel.  This function may be called multiple times, each time
# allocating an additional channel.  The channel is automatically re-allocated if there is a
# bus reset.  The channel is automatically released when this dc1394camera_t is freed or if
# the application shuts down prematurely.  If the channel needs to persist beyond the lifetime
# of this application, call \a dc1394_iso_set_persist() first.  Note that this function does
# _NOT_ automatically program @a camera to use the allocated channel for isochronous streaming.
# You must do that manually using \a dc1394_video_set_iso_channel().
_dll.dc1394_iso_allocate_channel.restype = error_t
_dll.dc1394_iso_allocate_channel.argtypes = [ POINTER( camera_t), c_uint64, POINTER(c_int)]
_dll.dc1394_iso_allocate_channel.errcheck = _errcheck

#dc1394_iso_release_channel:
# param &camera, channel_to_release
# Releases a previously allocated channel.  It is acceptable to release channels that were
# allocated by a different process or host.  If attempting to release a channel that is already
# released, the function will succeed.
_dll.dc1394_iso_release_channel.restype = error_t
_dll.dc1394_iso_release_channel.argtypes = [ POINTER( camera_t), c_int ]
_dll.dc1394_iso_release_channel.errcheck = _errcheck

#dc1394_iso_allocate_bandwidth
#param &camera, bandwidth_units
#bandwidth_units: the number of isochronous bandwidth units to allocate
#Allocates isochronous bandwidth.  This functions allocates bandwidth _in addition_ to any
# previous allocations.  It may be called multiple times.  The bandwidth is automatically
# re-allocated if there is a bus reset.  The bandwidth is automatically released if this
# camera is freed or the application shuts down prematurely.  If the bandwidth needs to
# persist beyond the lifetime of this application, call a dc1394_iso_set_persist() first.
_dll.dc1394_iso_allocate_bandwidth.restype = error_t
_dll.dc1394_iso_allocate_bandwidth.argtypes = [ POINTER( camera_t), c_int]
_dll.dc1394_iso_allocate_bandwidth.errcheck = _errcheck

#dc1394_iso_release_bandwidth:
#param &camera, bandwidth_units
#Releases previously allocated isochronous bandwidth.  Each \a dc1394camera_t keeps track of
# a running total of bandwidth that has been allocated. Released bandwidth is subtracted from
# this total for the sake of automatic re-allocation and automatic release on shutdown. It is
# also acceptable for a camera to release more bandwidth than it has allocated (to clean up for
# another process for example).  In this case, the running total of bandwidth is not affected.
# It is acceptable to release more bandwidth than is allocated in total for the bus.  In this
# case, all bandwidth is released and the function succeeds.
_dll.dc1394_iso_release_bandwidth.restype = error_t
_dll.dc1394_iso_release_bandwidth.argtypes = [ POINTER( camera_t), c_int ]
_dll.dc1394_iso_release_bandwidth.errcheck = _errcheck

#dc1394_iso_release_all:
#Releases all channels and bandwidth that have been previously allocated for this
# dc1394camera_t.  Note that this information can only be tracked per process, and there is
# no knowledge of allocations for this camera by previous processes.  To release resources in
# such a case, the manual release functions \a dc1394_iso_release_channel() and a
# dc1394_iso_release_bandwidth() must be used.
_dll.dc1394_iso_release_all.restype = error_t
_dll.dc1394_iso_release_all.argtypes = [ POINTER( camera_t)]
_dll.dc1394_iso_release_all.errcheck = _errcheck


#####################################################################################
#Log functions: log.h
#####################################################################################
# dc1394_log_register_handler: register log handler for reporting error, warning or debug
# statements. Passing NULL as argument turns off this log level.
# params: &log_handler, type_of_the_log, message_type, log_message
_dll.dc1394_log_register_handler.restype = error_t
_dll.dc1394_log_register_handler.argtypes = [log_t, c_void_p, c_void_p ]
_dll.dc1394_log_register_handler.errcheck = _errcheck

#dc1394_log_set_default_handler: set the log handler to the default handler
#At boot time, debug logging is OFF (handler is NULL). Using this function for the debug
# statements will start logging of debug statements usng the default handler.
_dll.dc1394_log_set_default_handler.restype = error_t
_dll.dc1394_log_set_default_handler.argtypes = [ log_t ]
_dll.dc1394_log_set_default_handler.errcheck = _errcheck

#dc1394_log_error: logs a fatal error condition to the registered facility
# This function shall be invoked if a fatal error condition is encountered. The message
# passed as argument is delivered to the registered error reporting function registered before.
#param [in] format,...: error message to be logged, multiple arguments allowed (printf style)
_dll.dc1394_log_error.restype = None
_dll.dc1394_log_error.argtypes = [ c_char_p]

# dc1394_log_warning: logs a nonfatal error condition to the registered facility
# This function shall be invoked if a nonfatal error condition is encountered. The message
# passed as argument is delivered to the registered warning reporting function registered before.
_dll.dc1394_log_warning.restype = None
_dll.dc1394_log_warning.argtypes = [ c_char_p ]

#dc1394_log_debug: logs a debug statement to the registered facility
# This function shall be invoked if a debug statement is to be logged. The message passed
# as argument is delivered to the registered debug reporting function registered before
# ONLY IF the environment variable DC1394_DEBUG has been set before the program starts.
_dll.dc1394_log_debug.restype = None
_dll.dc1394_log_debug.argtypes = [ c_char_p ]


############cleanup
del invert_dict
