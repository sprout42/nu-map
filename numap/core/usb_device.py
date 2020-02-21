# USBDevice.py
#
# Contains class definitions for USBDevice and USBDeviceRequest.

# TODO: replace with FaceDancer

import traceback
import struct
from numap.core.usb import DescriptorType, State, Request
from numap.core.usb_base import USBBaseActor
from numap.fuzz.helpers import mutable
from numap.core.phy import BaseUSBDevice, BaseUSBDeviceRequest


class USBDevice(USBBaseActor, BaseUSBDevice):
    name = 'Device'

    def __init__(
            self, app, phy, device_class, device_subclass,
            protocol_rel_num, max_packet_size_ep0, vendor_id, product_id,
            device_rev, manufacturer_string, product_string,
            serial_number_string, configurations=None, descriptors=None,
            usb_class=None, usb_vendor=None, bos=None):
        '''
        :param app: numap application
        :param phy: physical connection
        :param device_class: device class
        :param device_subclass: device subclass
        :param protocol_rel_num: protocol release number
        :param max_packet_size_ep0: maximum oacket size on EP0
        :param vendor_id: vendor id (i.e. VID)
        :param product_id: product id (i.e. PID)
        :param device_rev: device revision
        :param manufacturer_string: manufacturer name string
        :param product_string: product name string
        :param serial_number_string: serial number string
        :param configurations: list of available configurations (default: None)
        :param descriptors: dict of handler for descriptor requests (default: None)
        :param usb_class: USBClass instance (default: None)
        :param usb_vendor: USB device vendor (default: None)
        :param bos: USBBinaryStoreObject instance (default: None)
        '''

        USBBaseActor.__init__(self, app, phy)
        BaseUSBDevice.__init__(self, phy, device_class, device_subclass, protocol_rel_num, max_packet_size_ep0,
            vendor_id, product_id, device_rev, manufacturer_string, product_string, serial_number_string, configurations, 
            descriptors)

        if not descriptors:
            # Default descriptors, explicitly listing all functions here that 
            # are not handled by the base facedancer.USBDevice class, or 
            # modified by this class
            self.descriptors.update({
                DescriptorType.device: self.get_descriptor,
                DescriptorType.other_speed_configuration: self.get_other_speed_configuration_descriptor,
                DescriptorType.string: self.handle_get_string_descriptor_request,
                DescriptorType.hub: self.handle_get_hub_descriptor_request,
                DescriptorType.device_qualifier: self.get_device_qualifier_descriptor,
            })

            if bos:
                descriptors[DescriptorType.bos] = self.get_bos_descriptor

        # If the descriptors parameter was provided we should update the 
        # descriptors handler with it now because the default USBDevice handlers 
        # we just set may have overridden the custom values
        self.descriptors.update(descriptors)

        # not part of the default facedancer.USBDevice class
        self.bos = bos

        # unused?
        self.usb_class = usb_class
        self.usb_vendor = usb_vendor

        # this is fool-proof against weird drivers
        #if self.usb_class is None:
        #    self.usb_class = c.usb_class
        #if self.usb_vendor is None:
        #    self.usb_vendor = c.usb_vendor

        if self.usb_vendor:
            self.usb_vendor.device = self
        if self.usb_class:
            self.usb_class.device = self
        self.endpoints = {}

        # Add a task that will check if it is time to stop this USB device
        self.scheduler.add_task(lambda : if self.app.should_stop_phy(): self.stop())

    def setup_request_handlers(self):
        BaseUSBDevice.setup_request_handlers(self)

        # Extra handlers not set by the base facedancer.USBDevice class
        self.request_handlers[51] = self.handle_aoa_get_protocol_request

    @mutable('device_descriptor')
    def get_descriptor(self, index=0, usb_type='fullspeed', valid=False):
        return BaseUSBDevice.get_descriptor(self, usb_type=usb_type, valid=valid)

    # IRQ handlers
    #####################################################
    @mutable('device_qualifier_descriptor')
    def get_device_qualifier_descriptor(self, n):
        bDescriptorType = 6
        bNumConfigurations = len(self.configurations)
        bReserved = 0
        bMaxPacketSize0 = self.max_packet_size_ep0

        d = struct.pack(
            '<BHBBBBBB',
            bDescriptorType,
            self.usb_spec_version,
            self.device_class,
            self.device_subclass,
            self.protocol_rel_num,
            bMaxPacketSize0,
            bNumConfigurations,
            bReserved
        )
        d = struct.pack('B', len(d) + 1) + d
        return d

    def default_handler(self, req):
        """
        Called when there is no handler for the request
        """
        self.phy.send_on_endpoint(0, b'')
        self.debug('Received an unknown device request: %s, returned an empty response' % req)

    def handle_data_available(self, ep_num, data):
        if self.state == State.configured and ep_num in self.endpoints:
            # This function from the base class is duplicated here so this 
            # function can record that the target host appears to support this 
            # USB device.
            self.usb_function_supported('data received on endpoint %#x' % (ep_num))
            endpoint = self.endpoints[ep_num]
            if callable(endpoint.handler):
                endpoint.handler(data)

    #
    # No need to mutate this one, will mutate
    # USBConfiguration.get_descriptor instead
    #
    def get_configuration_descriptor(self, num):
        if num < len(self.configurations):
            return self.configurations[num].get_descriptor()
        else:
            return self.configurations[0].get_descriptor()

    def get_other_speed_configuration_descriptor(self, num):
        if num < len(self.configurations):
            return self.configurations[num].get_other_speed_descriptor()
        else:
            return self.configurations[0].get_other_speed_descriptor()

    def get_bos_descriptor(self, num):
        if self.bos:
            return self.bos.get_descriptor()
        # no bos? stall ep
        return None

    @mutable('string_descriptor_zero')
    def get_string0_descriptor(self):
        return BaseUSBDevice.handle_get_string_descriptor_request(self, 0)

    @mutable('string_descriptor')
    def get_string_descriptor(self, num):
        self.debug('get_string_descriptor: %#x (%#x)' % (num, len(self.strings)))
        return BaseUSBDevice.handle_get_string_descriptor_request(self, num)

    def handle_get_string_descriptor_request(self, num):
        if num == 0:
            return self.get_string0_descriptor()
        else:
            return self.get_string_descriptor(num)

    @mutable('hub_descriptor')
    def handle_get_hub_descriptor_request(self, num):
        bLength = 9
        bDescriptorType = 0x29
        bNbrPorts = 4
        wHubCharacteristics = 0xe000
        bPwrOn2PwrGood = 0x32
        bHubContrCurrent = 0x64
        DeviceRemovable = 0
        PortPwrCtrlMask = 0xff

        hub_descriptor = struct.pack(
            '<BBBHBBBB',
            bLength,              # length of descriptor in bytes
            bDescriptorType,      # descriptor type 0x29 == hub
            bNbrPorts,            # number of physical ports
            wHubCharacteristics,  # hub characteristics
            bPwrOn2PwrGood,       # time from power on til power good
            bHubContrCurrent,     # max current required by hub controller
            DeviceRemovable,
            PortPwrCtrlMask
        )

        return hub_descriptor

    # USB 2.0 specification, section 9.4.8 (p 285 of pdf)
    def handle_set_descriptor_request(self, req):
        self.debug('Received SET_DESCRIPTOR request: %s' % (req)

    # USB 2.0 specification, section 9.4.2 (p 281 of pdf)
    def handle_get_configuration_request(self, req):
        self.debug('Received GET_CONFIGURATION request: %s' % (req)
        self.phy.send_on_endpoint(0, b'\x01')  # HACK - once configuration supported

    # USB 2.0 specification, section 9.4.7 (p 285 of pdf)
    def handle_set_configuration_request(self, req):
        self.debug('Received SET_CONFIGURATION request: %s' % (req))
        self.supported_device_class_trigger = True

        # configs are one-based
        if (req.value) > len(self.configurations):
            self.error('Host tries to set invalid configuration: %#x' % (req.value - 1))
            self.config_num = 0
        else:
            self.config_num = req.value - 1
        self.info('Setting configuration: %#x' % self.config_num)
        self.configuration = self.configurations[self.config_num]
        self.state = State.configured

        # collate endpoint numbers
        for i in self.configuration.interfaces:
            for e in i.endpoints:
                self.endpoints[e.number] = e

        # HACK: blindly acknowledge request
        self.ack_status_stage()

    # USB 2.0 specification, section 9.4.4 (p 282 of pdf)
    def handle_get_interface_request(self, req):
        self.debug('Received GET_INTERFACE request: %s' % (req)
        if req.index == 0:
            # HACK: currently only support one interface
            self.phy.send_on_endpoint(0, b'\x00')
        else:
            self.phy.stall_ep0()

    # USB 2.0 specification, section 9.4.10 (p 288 of pdf)
    def handle_set_interface_request(self, req):
        self.phy.send_on_endpoint(0, b'')
        self.debug('Received SET_INTERFACE request: %s' % (req)

    # USB 2.0 specification, section 9.4.11 (p 288 of pdf)
    def handle_synch_frame_request(self, req):
        self.debug('Received SYNCH_FRAME request: %s' % (req)

    # Android Open Accesories
    def handle_aoa_get_protocol_request(self, req):
        """
        Handle AOA Get Protocol request.
        We return 0, signaling that we don't support any version of AOA
        :param req:
        :return:
        """
        self.phy.send_on_endpoint(0, b'\x00\x00')
        self.debug('Received AOA Get Protocol request, returning 0')


class USBDeviceRequest(BaseUSBDeviceRequest):
    def __init__(self, obj):
        """Expects raw 8-byte setup data request packet or a USB request object"""
        if isinstance(obj, bytes):
            raw_bytes = obj
        else:
            raw_bytes = struct.pack('<BBHHH',
                obj.request_type,
                obj.request,
                obj.value,
                obj.index,
                obj.length
            )
            raw_bytes += obj.data

        super(USBDeviceRequest, self).__init__(raw_bytes)
        self.raw_bytes = raw_bytes
