'''
USB Configuration class.
Each instance represents a single USB configuration.
In most cases it should not be subclassed.
'''
import struct
from numap.core.usb_base import USBBaseActor
from numap.core.usb import DescriptorType
from numap.fuzz.helpers import mutable
from numap.core.phy import BaseUSBConfiguration


class USBConfiguration(USBBaseActor, BaseUSBConfiguration):

    name = 'Configuration'

    # Those attributes can be ORed
    # At least one should be selected
    ATTR_BASE = 0x80
    ATTR_SELF_POWERED = ATTR_BASE | 0x40
    ATTR_REMOTE_WAKEUP = ATTR_BASE | 0x20

    def __init__(
        self, app, phy,
        index, string, interfaces,
        attributes=ATTR_SELF_POWERED,
        max_power=0x32, # ? facedancer.USBConfiguration default is 250
    ):
        '''
        :param app: nümap application
        :param phy: Physical connection
        :param index: configuration index (starts from 1)
        :param string: configuration string
        :param interfaces: list of interfaces for this configuration
        :param attributes: configuratioin attributes. one or more of USBConfiguration.ATTR_* (default: ATTR_SELF_POWERED)
        :param max_power: maximum power consumption of this configuration (default: 0x32)
        '''

        USBBaseActor.__init__(self, app, phy)
        BaseUSBConfiguration.__init__(self, index, string, interfaces, attributes, max_power)

        self.usb_class = None
        self.usb_vendor = None
        for i in self.interfaces:
            i.set_configuration(self)
            # this is fool-proof against weird drivers
            if i.usb_class is not None:
                self.usb_class = i.usb_class
            if i.usb_vendor is not None:
                self.usb_vendor = i.usb_vendor

    @mutable('configuration_descriptor')
    def get_descriptor(self, usb_type='fullspeed', valid=False):
        # This function allows extra keyword arguments
        kwargs = {
            'usb_type': usb_type,
            'valid': valid,
        }
        return BaseUSBConfiguration.get_descriptor(self, **kwargs)

    @mutable('other_speed_configuration_descriptor')
    def get_other_speed_descriptor(self, usb_type='fullspeed', valid=False):
        '''
        Get the other speed configuration descriptor.
        We implement it the same as configuration descriptor,
        only with different descriptor type.

        :return: a string of the entire other speed configuration descriptor
        '''
        interface_descriptors = b''
        for i in self.interfaces:
            interface_descriptors += i.get_descriptor(usb_type, valid)
        bLength = 9  # always 9
        bDescriptorType = DescriptorType.other_speed_configuration
        wTotalLength = len(interface_descriptors) + 9
        bNumInterfaces = len(self.interfaces)
        d = struct.pack(
            '<BBHBBBBB',
            bLength,
            bDescriptorType,
            wTotalLength & 0xffff,
            bNumInterfaces,
            self.configuration_index,
            self.configuration_string_index,
            self.attributes,
            self.max_power
        )
        return d + interface_descriptors
