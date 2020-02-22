# USBEndpoint.py
#
# Contains class definition for USBEndpoint.
import struct
from numap.core.usb import update_table_for_empty_keys
from numap.core.usb_base import USBBaseActor
from numap.fuzz.helpers import mutable
from numap.core.phy import BaseUSBEndpoint


class USBEndpoint(USBBaseActor, BaseUSBEndpoint):
    name = 'Endpoint'

    def __init__(
            self, app, phy, number, direction, transfer_type, sync_type,
            usage_type, max_packet_size, interval, handler, cs_endpoints=None,
            usb_class=None, usb_vendor=None):
        '''
        :param app: numap application
        :param phy: physical connection
        :param number: endpoint number
        :param direction: endpoint direction (direction_in/direction_out)
        :param transfer_type: one of USBEndpoint.transfer_type\*
        :param sync_type: one of USBEndpoint.sync_type\*
        :param usage_type: on of USBEndpoint.usage_type\*
        :param max_packet_size: maximum size of a packet
        :param interval: TODO
        :type handler:
            func(data) -> None if direction is out,
            func() -> None if direction is IN
        :param handler: interrupt handler for the endpoint
        :param cs_endpoints: list of class-specific endpoints (default: None)
        :param usb_class: USBClass instance (default: None)
        :param usb_vendor: USB device vendor (default: None)

        .. note:: OUT endpoint is 1, IN endpoint is either 2 or 3
        '''
        USBBaseActor.__init__(self, app, phy)
        BaseUSBEndpoint.__init__(self, number, direction, transfer_type,
                sync_type, usage_type, max_packet_size, interval, handler)

        # attributes not set by the base facedancer.USBEndpoint class
        self.cs_endpoints = [] if cs_endpoints is None else cs_endpoints
        self.address = (self.number & 0x0f) | (self.direction << 7)

        default_numap_usbendpoint_request_handlers = { 
            0: self.handle_get_status
        }
        update_table_for_empty_keys(self.request_handlers,
                default_numap_usbendpoint_request_handlers)

        self.usb_class = usb_class
        self.usb_vendor = usb_vendor

    def handle_get_status(self, req):
        self.info('in GET_STATUS of endpoint %d' % self.number)
        self.phy.send_on_endpoint(0, b'\x00\x00')

    def default_handler(self, req):
        self.phy.send_on_endpoint(0, b'')
        self.debug('Received an unknown USBEndpoint request: %s, returned an empty response' % req)

    def send(self, data):
        self.phy.send_on_endpoint(self.number, data)

    # see Table 9-13 of USB 2.0 spec (pdf page 297)
    @mutable('endpoint_descriptor')
    def get_descriptor(self, usb_type='fullspeed', valid=False):
        d = BaseUSBEndpoint.get_descriptor(self, )

        # the base facedancer.USBEndpoint class does not support cs_endpoints
        for cs in self.cs_endpoints:
            d += cs.get_descriptor()
        return d

    def _get_max_packet_size(self, usb_type):
        if usb_type == 'highspeed':
            return 512
        return self.max_packet_size
