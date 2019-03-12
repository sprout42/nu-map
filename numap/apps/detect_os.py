'''
Try to detect OS based on the USB traffic.
Not implemented yet.

Usage:
    numapdetect [-P=PHY_INFO] [-q] [-v ...]

Options:
    -P --phy PHY_INFO           physical layer info, see list below
    -v --verbose                verbosity level
    -q --quiet                  quiet mode. only print warning/error messages

Physical layer:
    fd:<serial_port>        use facedancer connected to given serial port
    gadgetfs                use gadgetfs (requires mounting of gadgetfs beforehand)

Example:
    numapdetect -P fd:/dev/ttyUSB0 -q
'''
from numap.apps.base import NumapApp


class NumapDetectOSApp(NumapApp):

    def run(self):
        self.logger.error('OS detection is not implemented yet')


def main():
    app = NumapDetectOSApp(__doc__)
    app.run()


if __name__ == '__main__':
    main()
