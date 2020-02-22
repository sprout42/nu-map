'''
USB Interface class.
Each instance represents a single USB interface.
This is a base class, and should be subclassed.
'''
import struct
from numap.core.usb import interface_class_to_descriptor_type, DescriptorType
from numap.core.usb_base import USBBaseActor
from numap.core.usb_class import USBClass
from numap.fuzz.helpers import mutable
from numap.core.phy import BaseUSBInterface


class USBInterface(USBBaseActor, BaseUSBInterface):
    name = 'Interface'

    def __init__(
        self, app, phy, interface_number, interface_alternate, interface_class,
        interface_subclass, interface_protocol, interface_string_index,
        endpoints=None, descriptors=None, cs_interfaces=None,
        usb_class=None, usb_vendor=None,
    ):
        '''
        :param app: numap application
        :param phy: physical connection
        :param interface_number: interface number
        :param interface_alternate: alternate settings
        :param interface_class: interface class
        :param interface_subclass: interface subclass
        :param interface_protocol: interface protocol
        :param interface_string_index: interface string index
        :param endpoints: list of endpoints for this interface (default: None)
        :param descriptors: dictionary of descriptor handlers for the interface (default: None)
        :param cs_interfaces: list of class specific interfaces (default: None)
        :param usb_class: USB device class (default: None)
        :param usb_vendor: USB device vendor (default: None)
        '''
        USBBaseActor.__init__(self, app, phy)
        BaseUSBInterface.__init__(self, interface_number, interface_alternate,
                interface_class, interface_subclass, interface_protocol,
                interface_string_index, endpoints, descriptors)

        self.cs_interfaces = [] if cs_interfaces is None else cs_interfaces

        self.usb_class = usb_class
        self.usb_vendor = usb_vendor

        for e in self.endpoints:
            e.interface = self
            if self.usb_class is None:
                self.usb_class = e.usb_class
            if self.usb_vendor is None:
                self.usb_vendor = e.usb_vendor

        if self.usb_class:
            self.usb_class.interface = self
        if self.usb_vendor:
            self.usb_vendor.interface = self

    def _handle_legacy_interface_class(self, interface_class, descriptors):
        # Modified from the standard facedancer.USBInterface function to support 
        # the app & phy used by numap classes
        iclass_desc_num = interface_class_to_descriptor_type(interface_class)

        if iclass_desc_num and descriptors:
            descriptor = descriptors[iclass_desc_num]
        else:
            descriptor = None

        return USBClass(self.app, self.phy, interface_class, descriptor, iclass_desc_num)

    def handle_get_descriptor_request(self, req):
        self.debug('Received GET_DESCRIPTOR %s' % req)
        BaseUSBInterface.handle_get_descriptor_request(self, req)

    def handle_set_interface_request(self, req):
        self.debug('Received SET_INTERFACE request %s' % req)
        BaseUSBInterface.handle_set_interface_request(self, req)

    def default_handler(self, req):
        self.phy.send_on_endpoint(0, b'')
        self.debug('Received an unknown USBInterface request: %s, returned an empty response' % req)

    @mutable('interface_descriptor')
    def get_descriptor(self, usb_type='fullspeed', valid=False):
        # facedancerUSBInterface.get_descriptor() duplicated here to add 
        # cs_interface support
        bLength = 9
        bDescriptorType = DescriptorType.interface
        bNumEndpoints = len(self.endpoints)

        d = struct.pack(
            '<BBBBBBBBB',
            bLength,  # length of descriptor in bytes
            bDescriptorType,  # descriptor type 4 == interface
            self.number,
            self.alternate,
            bNumEndpoints,
            self.iclass.class_number,
            self.subclass,
            self.protocol,
            self.string_index
        )

        if self.iclass:
            iclass_desc_num = interface_class_to_descriptor_type(self.iclass)
            if iclass_desc_num:
                desc = self.descriptors[iclass_desc_num]
                if callable(desc):
                    desc = desc()
                d += desc

        for e in self.cs_interfaces:
            d += e.get_descriptor(usb_type, valid)

        for e in self.endpoints:
            d += e.get_descriptor(usb_type, valid)

        return d
