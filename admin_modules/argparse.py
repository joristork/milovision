#
# Milovision: A camera pose estimation programme
# 
# Copyright (C) 2013 Joris Stork
# See LICENSE.txt
#
# argparse.py
"""
:synopsis:  Parses command line arguments using the optparse library.
            Note that we use the now deprecated optparse library to maintain
            compatibility with the pydc1394 library. This application and the
            pydc1394 library it uses should eventually be refactored to the
            newer argparse library.

.. moduleauthor:: Joris Stork <joris@wintermute.eu>

"""

__author__ = "Joris Stork"

from optparse import OptionParser
from pydc1394.cmdline import add_common_options

def run():
    """ parses command line args; adds to options defined in pydc/cmdline.py """

    usage = "usage: %prog [options] file"
    parser = OptionParser(usage)
    add_common_options(parser)

    parser.add_option("-v", "--verbosity", dest="verbosity",
            help="set stdout verbosity (0: critical, 1: error, 2: warning, 3: info, 4: debug)",
            type="int")
    parser.add_option("-n", "--modules", dest="nr_modules", default=1,
            help="set number of pipeline stages to run (1: edge detection; 2: ellipse fitting; 3: pose-1; 4: identify markers; 5: pose-2; 6: register data), default is all",
            type="int")
    parser.add_option("-s", "--simulate", dest="simulate",
            help="set simulation mode (-2: linear generated markers; -1: random generated markers; 0<:preset marker configurations by index nr)",
            type="int")
    parser.add_option("-w", "--windows", dest="windows",
            help="set image display (0: off; 1: on [default])",
            type="int")
    parser.add_option("-d", "--disk", dest="disk",
            help="load marker poses from disk (0: off [default]; 1: on)",
            type="int")
    parser.add_option("-t", "--simtime", dest="simtime",
            help="number of seconds to run simulation (default: 60)",
            type="int")

    (options, args) = parser.parse_args()

    if not options.verbosity:
        options.verbosity = 2

    if not options.simulate:
        options.simulate = 0

    return options, args
