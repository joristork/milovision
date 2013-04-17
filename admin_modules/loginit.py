#
# Milovision: A camera pose estimation programme
# 
# Copyright (C) 2013 Joris Stork
# See LICENSE.txt
#
# loginit.py
"""
:synopsis:  Provides logging functionality based on the "logging" library.

.. moduleauthor:: Joris Stork <joris@wintermute.eu>

"""

__author__ = "Joris Stork"

import logging


def run(verbosity):
    logging_levels = {0: logging.CRITICAL,
                      1: logging.ERROR,
                      2: logging.WARNING,
                      3: logging.INFO,
                      4: logging.DEBUG}
    
    logging.basicConfig(format='%(asctime)s %(levelname)-7s %(name)-14s %(message)s',
                        level=4,
                        filename='log',
                        filemode='w'
                        )
    console = logging.StreamHandler()
    console.setLevel(logging_levels[int(verbosity)])
    formatter = logging.Formatter(fmt='%(asctime)s %(levelname)-7s %(name)-14s %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)

    return logging.getLogger('main')
