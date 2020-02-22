'''
Scan device support in USB host

Usage:
    numapscan [-P=PHY_INFO] [-a=PHY_ARG ...]  [-q] [-v ...]

Options:
    -P --phy PHY_INFO           physical layer info, see list below
    -v --verbose                verbosity level
    -q --quiet                  quiet mode. only print warning/error messages
    -a --phy-args PHY_ARG       optional phy arguments
    -t --timeout TIMEOUT        timeout (seconds) for each device (default: 5)
    -w --wait-for-timeout       Keep each USB device active until the timeout
                                is reached. The default is to stop as soon as
                                the device is detected as supported

Physical layer:
    fd:<serial_port>        use facedancer connected to given serial port
    gadgetfs                use gadgetfs (requires mounting of gadgetfs beforehand)

Example:
    numapscan -P fd:/dev/ttyUSB0 -q
'''
import time
import traceback
from numap.apps.base import NumapApp


class NumapScanApp(NumapApp):

    def __init__(self, options):
        super().__init__(options)
        self.current_usb_function_supported = False
        self.start_time = 0

        self._timeout = self.options.get('--timeout', 5) 
        self._wait_for_timeout = self.options.get('--wait-for-timeout', False)

    def usb_function_supported(self, reason=None):
        '''
        Callback from a USB device, notifying that the current USB device
        is supported by the host.

        :param reason: reason why we decided it is supported (default: None)
        '''
        self.current_usb_function_supported = True

    def run(self):
        self.logger.always('Scanning host for supported devices')
        phy = self.load_phy()
        supported = []
        for device_name in self.umap_classes:
            self.logger.always('Testing support: %s' % (device_name))
            try:
                self.start_time = time.time()
                device = self.load_device(device_name, phy)
                device.connect()
                device.run()
                device.disconnect()
            except:
                self.logger.error(traceback.format_exc())
            phy.disconnect()
            if self.current_usb_function_supported:
                self.logger.always('Device is SUPPORTED')
                supported.append(device_name)
            self.current_usb_function_supported = False
            time.sleep(2)
        if len(supported):
            self.logger.always('---------------------------------')
            self.logger.always('Found %s supported device(s):' % (len(supported)))
            for i, device_name in enumerate(supported):
                self.logger.always('%d. %s' % (i + 1, device_name))

    def should_stop_phy(self):
        time_elapsed = int(time.time() - self.start_time)

        if time_elapsed > self._timeout:
            # If the timeout has been reached, stop no matter what
            self.logger.info('have been waiting long enough (over %d secs.), disconnect' % (time_elapsed))
            return True

        if not self._wait_for_timeout:
            # If the timeout has not been reached, we already know the device is 
            # supported, and "wait-for-timeout" is not set, stop this device
            if self.current_usb_function_supported:
                self.logger.debug('Current USB device is supported, stopping phy')
                return True

        return False


def main():
    app = NumapScanApp(__doc__)
    app.run()


if __name__ == '__main__':
    main()
