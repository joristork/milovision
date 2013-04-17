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


import wx
# OpenGL Stuff
from wx import glcanvas
from OpenGL.GL import *
from OpenGL.GLU import *

import time

# Numpy array is our picture
from numpy import empty

__all__ = [ "NewImageEvent", "LiveImageDisplay", "LiveImageDisplayPanel" ]

###########################################################################
#                             NEW IMAGE EVENT                             #
###########################################################################
EVT_NEW_IMAGE_ID = wx.NewId()

def EVT_NEW_IMAGE(win, func):
    """
    Define new Image event. This Event is send by the acquisition threads
    or the function that sends new images to display. The receiver then
    displays the image and updates it's display accordingly.
    """
    win.Connect(-1, -1, EVT_NEW_IMAGE_ID, func)

class NewImageEvent(wx.PyEvent):
    """
    Simple event to carry arbitrary result data. I our case we expect a
    numpy array with picture data inside.
    """
    def __init__(self, data):
        """Init Result Event."""
        wx.PyEvent.__init__(self)
        self.SetEventType(EVT_NEW_IMAGE_ID)
        self.data = data

###########################################################################
#                    class LiveImageDisplayPanel                          #
###########################################################################
class LiveImageDisplayPanel(glcanvas.GLCanvas):
    imageUpdateEvent = wx.NewEventType()

    def __init__(self,parent, shape, dtype, zoom = 1.0, defcapture_dir = "."):
        """
        This function implements a Panel which can display Live Video stream
        to the user. It also implements saving the current image to a file by
        keyboard stroke.

        The Display is implemented using OpenGL, it defines a GLGanvas with
        the same coordinate frame as the shown image (0,0 is therefore the top
        left border).  The user can also register points and lines to be
        displayed in the display while drawing

        parent         - parent of this panel
        shape          - numpy shape tuple of data to display
        dtype          - numpy data type of image data to display
        zoom           - how much should the image be resized
        defcapture_dir - Directory to save captured images to
        """
        wx.glcanvas.GLCanvas.__init__(self,parent,-1)

        # Initialize Variables
        self._caputure_dir = defcapture_dir
        self._fps = 0
        self._gldrawmode = GL_LUMINANCE if len(shape) == 2 else GL_RGB
        if dtype[-1] in ['1','8']:
            self._glinternal = GL_UNSIGNED_BYTE
        elif dtype[-2:] == '16' or dtype[-1] == '2':
            self._glinternal = GL_UNSIGNED_SHORT
        else:
            raise RuntimeError, "Unknown datatype!"
        self._gl_initialized=False
        # For dot drawing
        self._quadric = None
        self._dots = []
        # Empty array to make sure we always have something to draw
        self._arr = empty( shape, dtype )

        # Initialisations for FPS calculation
        self._ltime = time.time()
        self._drawn_frames = 0
        self._totframes = 0

        # Inform WX of our desired size
        self.SetSize((shape[1]*zoom,shape[0]*zoom))
        self.SetSizeHints(-1,-1,maxW=shape[1]*zoom,maxH=shape[0]*zoom)

        # Bind
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_SIZE, self.OnResize)
        self.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)
        self.Bind(wx.EVT_ERASE_BACKGROUND, self.OnEraseBackground)


    def InitGL( self ):
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
        glTexImage2D(GL_TEXTURE_2D, 0, self._gldrawmode, texdim_w, texdim_h, 0, self._gldrawmode, self._glinternal, None)

        # Set our viewport
        w,h = self.GetSize()
        glViewport(0, 0, w, h)
        glClear( GL_COLOR_BUFFER_BIT );

        # Set our Projection to Orthographic and the coordinate system
        # like the picture
        glMatrixMode( GL_PROJECTION );
        glLoadIdentity();
        glOrtho(0.0, self._arr.shape[1], self._arr.shape[0], 0.0, -1.0, 1.0);

        glMatrixMode( GL_MODELVIEW );
        glLoadIdentity();

        self._quadric = gluNewQuadric()

        self._gl_initialized = True

    def __del__( self ):
        del self._arr

        if self._quadric:
            gluDeleteQuadric( self._quadric )
            self._quadric = None

    def OnKeyDown( self, event ):
        # If our Parent has a KeyDown Function written,
        # he might want to overwrite this our default behaviour
        try:
            if self.GetParent().OnKeyDown(event,self._arr):
                return True
        except AttributeError, e:
            pass

        if chr( event.GetUniChar() ) in ['F', 'f']:
            print self.get_fps()
        # elif chr( event.GetUniChar() ) == ' ':
        #     Sl.save_image_with_number(
        #         self._arr, "image", "jpg",self._caputure_dir)

    def OnEraseBackground( self, event ):
        pass # Do nothing, to avoid flashing on MSW

    def OnResize( self, event ):
        # Reset our Viewpoint.
        size = self.GetClientSize()
        if self.GetContext():
            self.SetCurrent()
            glViewport(0, 0, size.width, size.height)
        event.Skip()

    def OnPaint( self, event  ):
        "This function draws our GLContext with the image"
        dc = wx.PaintDC( self )
        self.SetCurrent()
        if not self._gl_initialized:
            self.InitGL()
        # Remake the Texture from the new image data
        glTexSubImage2D (GL_TEXTURE_2D, 0, 0, 0, self._arr.shape[1], self._arr.shape[0], self._gldrawmode, self._glinternal, self._arr);

        glColor3f( 1.,1.,1. )

        # Draw the imageplane
        x,y = self._texture_coords
        glBegin(GL_QUADS)
        glTexCoord2f(0.0,0.); glVertex3f( 0.,0., -.5 )
        glTexCoord2f(x,0.); glVertex3f( self._arr.shape[1],0., -.5 )
        glTexCoord2f(x,y); glVertex3f( self._arr.shape[1],self._arr.shape[0], -.5 )
        glTexCoord2f(0.,y); glVertex3f( 0.,self._arr.shape[0], -.5 )
        glEnd()

        # Draw the dots
        glDisable(GL_TEXTURE_2D);					# Disable Texture Mapping
        for idx,(pos,radius,color) in enumerate(self._dots):
            x,y = pos

            glTranslate( x,y,0 )

            glColor3fv( color )
            gluDisk( self._quadric, 0, radius, 25, 1 )

            glTranslate( -x,-y,0 )

        # print "Done with dots!"

        glEnable(GL_TEXTURE_2D);					# Enable Texture Mapping

        self.SwapBuffers()

        # Calculate the FPS
        ctime = time.time()
        dtime = ctime-self._ltime
        if dtime > 1:
            fps= self._drawn_frames/dtime
            self._ltime = ctime
            self._drawn_frames = 0
            self._fps = fps
            # print "\r%.2f fps" % (fps),
        self._drawn_frames += 1
        self._totframes += 1

    def get_fps( self ):
        return self._fps


class LiveImageDisplay(wx.Frame):
    def __init__(self,parent,id,title, shape, dtype,
        zoom = 1.0, pos = wx.DefaultPosition, style = wx.DEFAULT_FRAME_STYLE):
        """
        This is the parent frame for a LiveImageDisplayPanel.
        It is not necessary, but if the Panel is used alone in one frame
        it is quite handy.
        """
        wx.Frame.__init__(self, parent, id, title, pos, wx.Size(200, 150),
            style = wx.DEFAULT_FRAME_STYLE & ~ (wx.RESIZE_BORDER | wx.RESIZE_BOX | wx.MAXIMIZE_BOX))

        self._ldp = LiveImageDisplayPanel( self, shape, dtype, zoom )

        sizer = wx.BoxSizer( wx.HORIZONTAL )
        sizer.Add( self._ldp, 1, wx.EXPAND)

        self.SetSizer( sizer )
        sizer.Fit(self)
        self.SetAutoLayout( True )
        self.Fit()

        self.get_fps = self._ldp.get_fps

        # Connect, so we can send this event to this livedisplay
        EVT_NEW_IMAGE(self, self.OnNewImage)

    def __del__( self ):
        try:
            del self._ldp
        except AttributeError: # already deleted, also ok
            pass

    def OnNewImage( self, event ):
        self.SetNewImage(event.data)

    def SetNewImage( self, img ):
        """
        Note: This function must not be called from another
        thread, use wx.Post(win,NewImageEvent(img)) for that
        """
        self._ldp._arr = img
        self._ldp.Refresh()

    def ResetDots( self ):
        self._ldp._dots = []

    def AddDot( self, pos, radius, color ):
        self._ldp._dots.append(
            (pos,radius,color)
        )

