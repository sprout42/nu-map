# USBDevice.py
#
# Contains class definitions for USBDevice and USBDeviceRequest.

# TODO: replace with FaceDancer

import traceback
import struct
from numap.core.usb import DescriptorType, State, Request
from numap.core.usb_base import USBBaseActor
from numap.fuzz.helpers import mutable

from facedancer.USBDevice import USBDevice as BaseUSBDevice

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

        if configurations is None:
            configurations = []
        if descriptors is None:
            descriptors = {}

        USBBaseActor.__init__(self, app, phy)
        BaseUSBDevice.__init__(self, phy, usb_class, device_subclass, protocol_rel_num, max_packet_size_ep0,
            vendor_id, product_id, device_rev, manufacturer_string, product_string, serial_number_string, configurations, 
            descriptors)

        self.supported_device_class_trigger = False
        self.supported_device_class_count = 0

        self.strings = []

        self.usb_spec_version = 0x0002
        self._device_class = device_class
        self.device_subclass = device_subclass
        self.protocol_rel_num = protocol_rel_num
        self.max_packet_size_ep0 = max_packet_size_ep0
        self.vendor_id = vendor_id
        self.product_id = product_id
        self.device_rev = device_rev

        self.manufacturer_string_id = self.get_string_id(manufacturer_string)
        self.product_string_id = self.get_string_id(product_string)
        self.serial_number_string_id = self.get_string_id(serial_number_string)

        # maps from USB.desc_type_* to bytearray OR callable
        self.descriptors = {
            DescriptorType.device: self.get_descriptor,
            DescriptorType.configuration: self.get_configuration_descriptor,
            DescriptorType.other_speed_configuration: self.get_other_speed_configuration_descriptor,
            DescriptorType.string: self.handle_get_string_descriptor_request,
            DescriptorType.hub: self.handle_get_hub_descriptor_request,
            DescriptorType.device_qualifier: self.get_device_qualifier_descriptor,
            DescriptorType.bos: self.get_bos_descriptor,
        }
        self.descriptors.update(descriptors)

        self.config_num = -1
        self.configuration = None
        self.configurations = configurations

        self.usb_class = usb_class
        self.usb_vendor = usb_vendor

        self.bos = bos

        for c in self.configurations:

            if c.configuration_string:
                csi = self.get_string_id(c.configuration_string)
                c.configuration_string_index = 0

            c.set_device(self)

            # this is fool-proof against weird drivers
            #if self.usb_class is None:
            #    self.usb_class = c.usb_class
            #if self.usb_vendor is None:
            #    self.usb_vendor = c.usb_vendor

        if self.usb_vendor:
            self.usb_vendor.device = self
        if self.usb_class:
            self.usb_class.device = self

        self.state = State.detached
        self.ready = False

        self.address = 0
        self.endpoints = {}

    def get_string_id(self, s):
        try:
            i = self.strings.index(s)
        except ValueError:
            # string descriptors start at index 1
            self.strings.append(s)
            i = len(self.strings)
        return i

    def setup_request_handlers(self):
        # see table 9-4 of USB 2.0 spec, page 279
        self.request_handlers = {
            0: self.handle_get_status_request,
            1: self.handle_clear_feature_request,
            3: self.handle_set_feature_request,
            5: self.handle_set_address_request,
            6: self.handle_get_descriptor_request,
            7: self.handle_set_descriptor_request,
            8: self.handle_get_configuration_request,
            9: self.handle_set_configuration_request,
            10: self.handle_get_interface_request,
            11: self.handle_set_interface_request,
            12: self.handle_synch_frame_request,
            51: self.handle_aoa_get_protocol_request,
        }

    def connect(self):
        self.phy.connect(self)
        # skipping USB.state_attached may not be strictly correct (9.1.1.{1,2})
        self.state = State.powered

    def disconnect(self):
        self.phy.disconnect()
        self.state = State.detached

    def ack_status_stage(self):
        self.phy.ack_status_stage()

    @mutable('device_descriptor')
    def get_descriptor(self, index=0, valid=False):
        bLength = 18
        bDescriptorType = 1
        bMaxPacketSize0 = self.max_packet_size_ep0
        d = struct.pack(
            '<BBHBBBBHHHBBBB',
            bLength,
            bDescriptorType,
            self.usb_spec_version,
            self._device_class,
            self.device_subclass,
            self.protocol_rel_num,
            bMaxPacketSize0,
            self.vendor_id,
            self.product_id,
            self.device_rev,
            self.manufacturer_string_id,
            self.product_string_id,
            self.serial_number_string_id,
            len(self.configurations)
        )
        return d

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
            self._device_class,
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
            self.usb_function_supported('data received on endpoint %#x' % (ep_num))
            endpoint = self.endpoints[ep_num]
            if callable(endpoint.handler):
                endpoint.handler(data)

    def handle_buffer_available(self, ep_num):
        if self.state == State.configured and ep_num in self.endpoints:
            endpoint = self.endpoints[ep_num]
            if callable(endpoint.handler):
                try:
                    endpoint.handler()
                except:
                    self.error(traceback.format_exc())
                    self.error(''.join(traceback.format_stack()))
                    raise

    # standard request handlers


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
        d = struct.pack(
            '<BBBB',
            4,      # length of descriptor in bytes
            3,      # descriptor type 3 == string
            9,      # language code 0, byte 0
            4       # language code 0, byte 1
        )
        return d

    @mutable('string_descriptor')
    def get_string_descriptor(self, num):
        self.debug('get_string_descriptor: %#x (%#x)' % (num, len(self.strings)))
        s = None
        if num <= len(self.strings):
            s = self.strings[num - 1].encode('utf-16')
        else:
            if self.configuration:
                s = self.configuration.get_string_by_id(num)
        if not s:
            s = self.strings[0].encode('utf-16')
        # Linux doesn't like the leading 2-byte Byte Order Mark (BOM);
        # FreeBSD is okay without it
        s = s[2:]

        d = struct.pack(
            '<BB',
            len(s) + 2,  # length of descriptor in bytes
            3            # descriptor type 3 == string
        )
        return d + s

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
        self.debug('Received SET_DESCRIPTOR request')

    # USB 2.0 specification, section 9.4.2 (p 281 of pdf)
    def handle_get_configuration_request(self, req):
        self.debug('Received GET_CONFIGURATION request')
        self.phy.send_on_endpoint(0, b'\x01')  # HACK - once configuration supported

    # USB 2.0 specification, section 9.4.7 (p 285 of pdf)
    def handle_set_configuration_request(self, req):
        self.debug('Received SET_CONFIGURATION request')
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
        self.debug('Received GET_INTERFACE request')
        if req.index == 0:
            # HACK: currently only support one interface
            self.phy.send_on_endpoint(0, b'\x00')
        else:
            self.phy.stall_ep0()

    # USB 2.0 specification, section 9.4.10 (p 288 of pdf)
    def handle_set_interface_request(self, req):
        self.phy.send_on_endpoint(0, b'')
        self.debug('Received SET_INTERFACE request')

    # USB 2.0 specification, section 9.4.11 (p 288 of pdf)
    def handle_synch_frame_request(self, req):
        self.debug('Received SYNCH_FRAME request')

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


class USBDeviceRequest(object):

    setup_request_types = {
        Request.type_standard: 'standard',
        Request.type_class: 'class',
        Request.type_vendor: 'vendor',
    }
    setup_request_receipients = {
        Request.recipient_device: 'device',
        Request.recipient_interface: 'interface',
        Request.recipient_endpoint: 'endpoint',
        Request.recipient_other: 'other',
    }

    def __init__(self, raw_bytes):
        '''Expects raw 8-byte setup data request packet'''

        print(raw_bytes)

        (
            self.request_type,
            self.request,
            self.value,
            self.index,
            self.length
        ) = struct.unpack('<BBHHH', raw_bytes[:8])
        self.data = raw_bytes[8:]
        self.raw_bytes = raw_bytes

    def __str__(self):
        s = 'dir=%#x (%s), type=%#x (%s), rec=%#x (%s), req=%#x, val=%#x, idx=%#x, len=%#x' % (
            self.get_direction(),
            'in' if self.get_direction() else 'out',
            self.get_type(),
            self.setup_request_types.get(self.get_type(), 'unknown'),
            self.get_recipient(),
            self.setup_request_receipients.get(self.get_recipient(), 'unknown'),
            self.request,
            self.value,
            self.get_index(),
            self.length
        )
        return s

    def raw(self):
        '''returns request as bytes'''
        b = struct.pack(
            '<BBHHH',
            self.request_type,
            self.request,
            self.value >> 8,
            self.index >> 8,
            self.length >> 8,
        )
        return b

    def get_direction(self):
        return (self.request_type >> 7) & 0x01

    def get_type(self):
        return (self.request_type >> 5) & 0x03

    def get_recipient(self):
        return self.request_type & 0x1f

    # meaning of bits in wIndex changes whether we're talking about an
    # interface or an endpoint (see USB 2.0 spec section 9.3.4)
    def get_index(self):
        rec = self.get_recipient()
        if rec == 1:                # interface
            return self.index
        elif rec == 2:              # endpoint
            return self.index & 0xf
        else:
            return self.index
