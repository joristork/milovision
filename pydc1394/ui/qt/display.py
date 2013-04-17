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


"""
This file contains a live Display Widget and a Live Display Window
that can be used to interactively display a Camera image

this package requires pyqt4
"""

from __future__ import division

import time

from OpenGL.GL import *
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtOpenGL import *
import numpy as np

try:
    from Utils import saveload as Sl
except ImportError:
    pass

__all__ = [ "LiveCameraWin", "ImageDisplay", ]

class AcquisitionThread(QThread):
    def __init__(self, cam, parent = None):
        super(AcquisitionThread, self).__init__(parent)
        self._stopped = False
        self._mutex = QMutex()

        self._cam = cam

        self.start()

    def stop(self):
        try:
            self._mutex.lock()
            self._stopped = True
        finally:
            self._mutex.unlock()

    def isStopped(self):
        s = False
        try:
            self._mutex.lock()
            s = self._stopped
        finally:
            self._mutex.unlock()
        return s

    def run(self):
        if not self._cam.running:
            self._cam.start(interactive=True)

        while not self.isStopped():
            self._cam.new_image.acquire()
            if not self._cam.running:
                self.stop()
            else:
                self.emit(SIGNAL("newImage"), self._cam.current_image)
            self._cam.new_image.release()

class LiveCameraWin(QWidget):
    def __init__(self, cam, zoom = 1.0, parent = None):
        super(LiveCameraWin, self).__init__(parent)

        self.camWidget = ImageDisplay(cam.mode.shape, cam.mode.dtype, zoom)

        mainLayout = QHBoxLayout()
        mainLayout.addWidget(self.camWidget)
        self.setLayout(mainLayout)

        self.setWindowTitle(
            "Camera %s, GUID %s, %s, %.1f fps" % (
                cam.model, cam.guid, str(cam.mode), cam.fps)
        )

        self.acquisitionThread = AcquisitionThread(cam)

        self.connect(self.acquisitionThread,
            SIGNAL("newImage"), self.camWidget.newImage)

    def sizeHint(self):
        msh = self.camWidget.minimumSizeHint()
        return QSize( msh.width() + self.layout().margin()*2,
                      msh.height() + self.layout().margin()*2)

    def closeEvent(self, evt):
        self.acquisitionThread.stop()

class ImageDisplay(QGLWidget):
    def __init__(self, shape, dtype, zoom = 1.0, parent=None):
        """
        This function implements a Panel which can display Live Video stream
        to the user. It also implements saving the current image to a file
        by keyboard stroke.

        The Display is implemented using OpenGL, it defines a GLGanvas with
        the same coordinate frame as the shown image (0,0 is therefore the
        top left border).

        shape  - numpy shape tuple of data to display
        dtype  - numpy data type of image data to display
        zoom   - how much should the image be resized
        parent - parent of this panel
        """

        f = QGLFormat()
        # The next line decides if the image flickers or not.
        # Unfortunately, if the image doesn't flicker, we do not get
        # a high enough frame rate to display our camera images if we try
        # to display them all. We now use a QTimer to redraw our window
        # every 1/60 of a second, and this seems to work well.
        f.setSwapInterval(1)
        super(ImageDisplay, self).__init__(f, parent)

        self._arr = np.empty(shape, dtype=dtype)
        self._gldrawmode = GL_LUMINANCE  if len(shape) == 2 else GL_RGB
        self._zoom = zoom

        if dtype[-1] in ['1','8']:
            self._glinternal = GL_UNSIGNED_BYTE
        elif dtype[-2:] == '16' or dtype[-1] == '2':
            self._glinternal = GL_UNSIGNED_SHORT
        else:
            raise RuntimeError, "Unknown datatype!"

        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        sizePolicy.setHeightForWidth(True)
        self.setSizePolicy(sizePolicy)

        self.setFocusPolicy(Qt.WheelFocus)

        # We redraw our image 60 times per second; no matter what kind of camera
        # is attached
        self.aTimer = QTimer()
        self.connect(self.aTimer, SIGNAL("timeout()"), self.updateGL)
        self.aTimer.start(1000/60)

        # Initialisations for FPS calculation
        self._ltime = time.time()
        self._drawn_frames = 0
        self._totframes = 0

    def minimumSizeHint(self):
        return QSize(self._arr.shape[1]*self._zoom,
                     self._arr.shape[0]*self._zoom)

    def heightForWidth(self, w):
        return w/self._arr.shape[1] * self._arr.shape[0]

    def newImage(self, i):
        self._arr = i
        # self.updateGL()

    def keyPressEvent(self, evt):
        key = evt.key()
        if key == Qt.Key_F:
            print "FPS: %.2f" % self._fps
        elif key == Qt.Key_Space:
            Sl.save_image_with_number(
                self._arr, "image", "jpg",".")
        elif key in map(ord, '123456789'):
            self._zoom = int(chr(key))
            self.resize(self.minimumSizeHint())
            self.parent().adjustSize()
        elif key in map(ord,'!"$%&/()') + [ 167 ]:
            if evt.modifiers() & Qt.SHIFT:
                val = {
                    ord('!'): 1,
                    ord('"'): 2,
                    167: 3,
                    ord('$'): 4,
                    ord('%'): 5,
                    ord('&'): 6,
                    ord('/'): 7,
                    ord('('): 8,
                    ord(')'): 9,
                }[key]
                self._zoom = 1/val
            self.resize(self.minimumSizeHint())
            self.parent().adjustSize()
        else:
            return QGLWidget.keyPressEvent(self, evt)

    def initializeGL( self ):
        """
        This function initalizes OpenGL according to what we need
        in this context
        """
        glEnable(GL_TEXTURE_2D);					# Enable Texture Mapping
        glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MAG_FILTER,GL_NEAREST); #  Set Texture Max Filter
        glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MIN_FILTER,GL_NEAREST); # Set Texture Min Filter

        # Determine the texture size (which must be 2**x)
        texdim_w, texdim_h = 32,32
        while texdim_w < self._arr.shape[1]:
            texdim_w *= 2
        while texdim_h < self._arr.shape[0]:
            texdim_h *= 2
        self._texture_coords = (float(self._arr.shape[1])/texdim_w,float(self._arr.shape[0])/texdim_h)

        # Generate our Texture
        # The next line makes sure that bytes are read in the correct
        # order while unpacking from python
        glPixelStoref(GL_UNPACK_SWAP_BYTES, 1)
        glTexImage2D(GL_TEXTURE_2D, 0, self._gldrawmode, texdim_w, texdim_h, 0, self._gldrawmode, self._glinternal, None)

        # Set our viewport
        w,h = self.width(), self.height()

        glViewport(0, 0, w, h)
        glClear( GL_COLOR_BUFFER_BIT );

        # Set our Projection to Orthographic and the coordinate system
        # like the picture
        glMatrixMode( GL_PROJECTION );
        glLoadIdentity();
        glOrtho(0.0, self._arr.shape[1], self._arr.shape[0], 0.0, -1.0, 1.0);

        glMatrixMode( GL_MODELVIEW );
        glLoadIdentity();

        # self._quadric = gluNewQuadric()


    def resizeGL(self, width, height):
        # Reset our Viewpoint.
        glViewport(0, 0, width, height)

    def paintGL(self):
        # Remake the Texture from the new image data
        glTexSubImage2D (GL_TEXTURE_2D, 0, 0, 0,
            self._arr.shape[1], self._arr.shape[0],
            self._gldrawmode, self._glinternal, self._arr);

        glColor3f( 1.,1.,1. )

        # Draw the imageplane
        x,y = self._texture_coords
        glBegin(GL_QUADS)
        glTexCoord2f(0.0, 0.); glVertex3f(0., 0., - .5)
        glTexCoord2f(x, 0.); glVertex3f(self._arr.shape[1], 0., - .5)
        glTexCoord2f(x, y); glVertex3f(self._arr.shape[1],
                            self._arr.shape[0], - .5)
        glTexCoord2f(0., y); glVertex3f(0., self._arr.shape[0], - .5)
        glEnd()

        # Calculate the FPS
        ctime = time.time()
        dtime = ctime-self._ltime
        if dtime > 1:
            fps= self._drawn_frames/dtime
            self._ltime = ctime
            self._drawn_frames = 0
            self._fps = fps
        self._drawn_frames += 1
        self._totframes += 1


