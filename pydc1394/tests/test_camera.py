#!/usr/bin/env python -tt
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

import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), os.path.pardir))

import time
from collections import defaultdict

import nose
from nose.tools import *
from nose.plugins.attrib import attr

from camera import DC1394Library, Camera, CameraError

# Is a camera connected?
_has = defaultdict(lambda bool: False)
def _check_camera_and_features():
    l = DC1394Library()
    cams = l.enumerate_cameras()
    if len(cams):
        _has["camera"] = True

    # This is somewhat unproper: we open the camera here, even
    # though we have tests below to ensure that the camera works.
    # we put this in a catch all Exception though; if opening does not
    # work, we will only run the most basic tests
    # try:
    c = None
    try:
        c = Camera(l, cams[0]['guid'])

        print "c.modes: %s" % (c.modes,)
        if "FORMAT7_0" in (m.name for m in c.modes):
            _has["format7"] = True
    except:
        pass
    finally:
        if c is not None:
            c.close()

_check_camera_and_features()

def needs(f, what):
    def skipper(*args, **kwargs):
        if not what in _has:
            raise nose.SkipTest("This test needs the following device "
                "or feature: %s!" % what)
        else:
            return f(*args, **kwargs)
    return nose.tools.make_decorator(f)(skipper)
need_cam = lambda f: needs(f, "camera")
need_format7 = lambda f: needs(f, "format7")


class LibBase(object):
    @need_cam
    def setUp(self):
        self.l = DC1394Library()
    @need_cam
    def tearDown(self):
        self.l.close()

class CamBase(LibBase):
    @need_cam
    def setUp(self):
        LibBase.setUp(self)
        cams = self.l.enumerate_cameras()
        self.c = Camera(self.l, cams[0]['guid'])
        mode = self.c.modes[0]
        self.c.mode = mode
        self.c.fps = mode.framerates[-1]

    @need_cam
    def tearDown(self):
        self.c.stop()
        self.c.close()
        LibBase.tearDown(self)

# Camera opening and closing
class TestInstantiation(LibBase):
    @need_cam
    def test(self):
        cams = self.l.enumerate_cameras()
        c = Camera(self.l, cams[0]['guid'])
        c.close()

    @need_cam
    @raises(CameraError)
    def test_failure(self):
        Camera(self.l, "deadbeef")

    @need_cam
    @raises(CameraError)
    def test_invalid_mode(self):
        cams = self.l.enumerate_cameras()
        c = Camera(self.l, cams[0]['guid'], mode=(23323,232323,"Y16"))
        c.close()

    @need_cam
    @raises(CameraError)
    def test_invalid_isospeed(self):
        cams = self.l.enumerate_cameras()
        c = Camera(self.l, cams[0]['guid'], isospeed=12393)
        c.start()
        c.shot()
        c.stop()
        c.close()

# From now on, we assume that we can get a camera instance
class TestCamera(CamBase):
    @need_cam
    def test_acquisition(self):
        self.c.start()
        i = self.c.shot()
        eq_(i.shape, self.c.mode.shape)
        self.c.stop()



    @need_cam
    @attr('slow')
    def test_reset(self):
        self.c.start()
        self.c.reset_bus()

    @need_cam
    def test_manual_shutter_time_setting(self):
        try:
            self.c.shutter.mode = 'manual'
            smin, smax = self.c.shutter.range
            val = round(smin + (smax-smin)/2.)
            self.c.shutter.val = val
            # Setting the fps is just approximate on most cameras
            ok_( abs(self.c.shutter.val-val) < 2.)
        except AttributeError:
            pass # Maybe camera does not support this

    @need_format7
    def test_mode7(self):
        smallest_mode = self.c.modes[0]
        m, = filter(lambda k: k.name == "FORMAT7_0", self.c.modes)

        m.setup((smallest_mode.shape[1], smallest_mode.shape[0]), (0,0),
            color_coding = "Y8")

        self.c.mode = m

        self.c.start()
        i = self.c.shot()
        self.c.stop()

        assert_equal(i.shape, m.shape)
        assert_equal(i.dtype, m.dtype)

class TestModeSetting(CamBase):
    def _run(self, m):
        self.c.mode = m
        self.c.start()
        i = self.c.shot()
        self.c.stop()

        eq_(self.c.mode, self._mode)
        eq_(i.shape, self._mode.shape)
        eq_(i.dtype, self._mode.dtype)

    @need_cam
    def test_set_mode_with_tuple(self):
        self._mode = self.c.modes[0]
        self._run(self._mode)

    @need_cam
    def test_set_mode_with_str(self):
        self._mode = self.c.modes[0]
        descr = str(self._mode)
        print "descr: %s" % (descr)
        self._run(descr)


