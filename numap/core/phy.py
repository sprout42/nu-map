"""
Temporary compatibility shim for using FaceDancer2 to replace the umap PHY architecture.
"""

# TODO: Would be better if we could automatically discover the phy backend by 
# attempting to import facedancer, and if that fails fall back to the old 
# method.
#
# TODO: It feels like it would be more elegant to have the base USB classes 
# associated with the phy class itself, but then to define the numap.core.usb_* 
# classes we would need a metaclass shim which is annoying and I don't feel like 
# doing that now, I'm already making a big enough mess.

import logging

try:
    # Attempt to import the facedancer package
    import facedancer

    # It feels cleaner to have the facedancer package referenced only here 
    # rather than all throughout the numap USB class modules
    from facedancer.USB import USB as BaseUSB
    from facedancer.USBClass import USBClass as BaseUSBClass 
    from facedancer.USBConfiguration import USBConfiguration as BaseUSBConfiguration 
    from facedancer.USBDevice import USBDevice as BaseUSBDevice 
    from facedancer.USBDevice import USBDeviceRequest as BaseUSBDeviceRequest 
    from facedancer.USBEndpoint import USBEndpoint as BaseUSBEndpoint 
    from facedancer.USBInterface import USBInterface as BaseUSBInterface 
    # currently unused
    #from facedancer.USBProxy import USBProxy as BaseUSBProxy 
    from facedancer.USBVendor import USBVendor as BaseUSBVendor 

    class Phy(object):
        """ PHY definition for using the FaceDancer2 generic USB-emulation backend. Mostly a pass-through. """

        name = "FaceDancer2"

        def __init__(self):
            """ Initializes a new FaceDancerPhy """
            # Generate our logging backend.
            self.logger = logging.getLogger('numap')
            #self.backend = facedancer

            # Now patch the base package classes
            self._patch_facedancer_classes()

        def _patch_facedancer_classes(self):
            """ patches the facedancer.USB* classes to point to the numap.core.usb* classes """
            # We need to ensure that new USB classes that are created by the 
            # facedancer code get mapped to our numap USB classes.  To achieve 
            # that patch the facedancer.USB* classes to point to numap.core.usb* 
            # classes
            import facedancer.USB 
            import numap.core.usb
            facedancer.USB.USB = numap.core.usb.USB

            import facedancer.USBClass
            import numap.core.usb_class
            facedancer.USBClass.USBClass = numap.core.usb_class.USBClass

            import facedancer.USBConfiguration
            import numap.core.usb_configuration
            facedancer.USBConfiguration.USBConfiguration = numap.core.usb_configuration.USBConfiguration

            import facedancer.USBDevice
            import numap.core.usb_device
            facedancer.USBDevice.USBDevice = numap.core.usb_device.USBDevice
            # No need to customize the USBDeviceRequest at the moment
            #facedancer.USBDevice.USBDeviceRequest = numap.core.usb_device.USBDeviceRequest

            import facedancer.USBEndpoint
            import numap.core.usb_endpoint
            facedancer.USBEndpoint.USBEndpoint = numap.core.usb_endpoint.USBEndpoint

            import facedancer.USBInterface
            import numap.core.usb_interface
            facedancer.USBInterface.USBInterface = numap.core.usb_interface.USBInterface

            # No numap USBProxy class yet
            #import facedancer.USBProxy

            import facedancer.USBVendor
            import numap.core.usb_vendor
            facedancer.USBVendor.USBVendor = numap.core.usb_vendor.USBVendor

        def get_phy(self, *args, **kwargs):
            """ Returns the app that will run the physical device """
            #subcls = facedancer.FacedancerUSBApp(*args, **kwargs)
            # class USBApp(subcls):
            # ...
            return facedancer.FacedancerUSBApp(*args, **kwargs)

except:
    raise
