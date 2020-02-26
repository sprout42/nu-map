# USBVendor.py
#
# Contains class definition for USBVendor, intended as a base class (in the OO
# sense) for implementing device vendors.
from numap.core.usb_base import USBBaseActor
from numap.core.phy import BaseUSBVendor


class USBVendor(USBBaseActor, BaseUSBVendor):
    name = 'DeviceVendor'

    def __init__(self, app, phy):
        '''
        :param app: numap application
        :param phy: physical connection
        '''
        USBBaseActor.__init__(self, app, phy)
        BaseUSBVendor.__init__(self)

        self.setup_local_handlers()

        self.interface = None
        self.endpoint = None

    def setup_local_handlers(self):
        self.local_handlers = {}

    def default_handler(self, req):
        handler = self.local_handlers[req.request]
        response = handler(req)
        if response is not None:
            self.phy.send_on_endpoint(0, response)
        self.usb_function_supported('vendor specific setup request received')
