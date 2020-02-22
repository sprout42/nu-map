# USBCSInterface.py
#
# Contains class definition for USBCSInterface.
import struct
from numap.core.usb import DescriptorType
from numap.core.usb_base import USBBaseActor


class USBCSInterface(USBBaseActor):
    name = 'CSInterface'

    def __init__(self, name, app, phy, cs_config):
        '''
        :param app: numap application
        :param phy: physical connection
        :param cs_config: class specific configuration
        '''
        super().__init__(app, phy)
        self.name = name
        self.cs_config = cs_config

        self.descriptors = {
            DescriptorType.cs_interface: self.get_descriptor,
        }
        self.request_handlers = {
            0x06: self.handle_get_descriptor_request,
            0x0b: self.handle_set_interface_request
        }

    # USB 2.0 specification, section 9.4.3 (p 281 of pdf)
    # HACK: blatant copypasta from USBDevice pains me deeply
    def handle_get_descriptor_request(self, req):
        dtype = (req.value >> 8) & 0xff
        dindex = req.value & 0xff
        lang = req.index
        n = req.length

        response = None

        self.info((
            'Received GET_DESCRIPTOR req %d, index %d, language 0x%04x, length %d'
        ) % (dtype, dindex, lang, n))

        # TODO: handle KeyError
        response = self.descriptors[dtype]
        if callable(response):
            response = response(dindex)

        if response:
            n = min(n, len(response))
            self.phy.send_on_endpoint(0, response[:n])
            self.log_verbose('sent %d bytes in response' % (n))

    def handle_set_interface_request(self, req):
        self.phy.stall_ep0()
        self.info('Received SET_INTERFACE request: %s' % (req))

    def default_handler(self, req):
        self.phy.send_on_endpoint(0, b'')
        self.debug('Received an unknown USBCSInterface request: %s, returned an empty response' % req)

    def get_descriptor(self, usb_type='fullspeed', valid=False):
        descriptor_type = DescriptorType.cs_interface
        length = len(self.cs_config) + 2
        response = struct.pack('BB', length & 0xff, descriptor_type) + self.cs_config
        return response
