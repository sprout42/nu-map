'''
Class-Specific endpoint (used in USB Audio)
'''
import struct
from numap.core.usb import DescriptorType
from numap.core.usb_base import USBBaseActor
from numap.fuzz.helpers import mutable


class USBCSEndpoint(USBBaseActor):

    name = 'CSEndpoint'

    def __init__(self, name, app, phy, cs_config):
        '''
        :param name: Name of the endpoint
        :param app: nümap application
        :param phy: Physical connection
        :param cs_config: Containing class specific config
        '''
        super().__init__(app, phy)
        self.name = name
        self.cs_config = cs_config
        self.interface = None
        self.usb_class = None
        self.request_handlers = {
            1: self.handle_clear_feature_request
        }

    def handle_clear_feature_request(self, req):
        self.interface.phy.send_on_endpoint(0, b'')

    def default_handler(self, req):
        self.interface.phy.send_on_endpoint(0, b'')
        self.debug('Received an unknown CSEndpoint request: %s, returned an empty response' % req)

    def set_interface(self, interface):
        self.interface = interface

    # see Table 9-13 of USB 2.0 spec (pdf page 297)
    @mutable('usbcsendpoint_descriptor')
    def get_descriptor(self, usb_type='fullspeed', valid=False):
        descriptor_type = DescriptorType.cs_endpoint
        length = len(self.cs_config) + 2
        response = struct.pack('BB', length & 0xff, descriptor_type) + self.cs_config
        return response
