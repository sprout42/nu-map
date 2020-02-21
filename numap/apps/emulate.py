#!/usr/bin/env python
'''
Emulate a USB device

Usage:
    numapemulate -C=DEVICE_CLASS [-P=PHY_INFO] [-q] [--vid=VID] [--pid=PID] [-v ...]

Options:
    -P --phy PHY_INFO           physical layer info, see list below [default: auto]
    -C --class DEVICE_CLASS     class of the device or path to python file with device class
    -v --verbose                verbosity level
    -q --quiet                  quiet mode. only print warning/error messages
    --vid VID                   override vendor ID
    --pid PID                   override product ID

Physical layer:
    fd:<serial_port>        use facedancer connected to given serial port
    gadgetfs                use gadgetfs (requires mounting of gadgetfs beforehand)
    auto                    automatically detect how we should connect

Examples:
    emulate keyboard:
        numapemulate -P fd:/dev/ttyUSB1 -C keyboard
    emulate your own device:
        numapemulate -P fd:/dev/ttyUSB1 -C my_usb_device.py
'''
import traceback

from numap.apps.base import NumapApp


class NumapEmulationApp(NumapApp):

    verbose = 0

    def run(self):
        self.fuzzer = self.get_fuzzer()
        self.phy = self.load_phy()
        self.dev = self.load_device(self.options['--class'], self.phy)
        try:
            self.dev.connect()
            self.dev.run()
        except KeyboardInterrupt:
            self.logger.info('user terminated the run')
        except:
            self.logger.error('Got exception while connecting/running device')
            self.logger.error(traceback.format_exc())
        self.dev.disconnect()

    def get_fuzzer(self):
        return None


def main():
    app = NumapEmulationApp(__doc__)
    app.run()


if __name__ == '__main__':
    main()
