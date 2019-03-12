"""
Temporary compatibility shim for using FaceDancer2 to replace the umap PHY architecture.
"""

import logging

try:
    from facedancer import FacedancerUSBApp
except ImportError:
    pass
else:

    class FaceDancerPhy:
        """ PHY definition for using the FaceDancer2 generic USB-emulation backend. Mostly a pass-through. """

        name = "FaceDancer2"

        def __init__(self, arguments):
            """ Initializes a new FaceDancerPhy.

            Parameters:
                arguments -- The argument string passed in from the command line.
            """

            # Generate our logging backend.
            self.logger = logging.getLogger('numap')

            # And create our FD2 connection.
            # TODO: support specifying exact types / parameters?
            self.backend = FacedancerUSBApp()


        def __getattr__(self, name):
            """ This compatibilty shim mostly works by passing things through to the FaceDancer backend. """
            return getattr(self.backend, name)
