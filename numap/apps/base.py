'''
nümap applications should subclass the NumapApp.
'''
import sys
import os
import importlib
import logging
import docopt

# TODO: replace FaceDancerPhy with just FaceDancerApp
from numap.core.phy import Phy
from numap.utils.ulogger import set_default_handler_level


class NumapApp(object):

    def __init__(self, docstring=None):
        # TODO: Move arg parsing over to argparse, I like it because it's more 
        # standardized, but also it would make passing args to the phy less 
        # nasty
        if docstring is not None:
            self.options = docopt.docopt(docstring)

            # HACK HACK HACK
            # I wish there was a better way (perhaps with argparse)
            if '--phy-args' in self.options:
                phy_args = {}
                for arg in self.options['--phy-args']:
                    args = arg.split('=', maxsplit=1)
                    if len(args) == 1:
                        phy_args[args[0]] = 1
                    else:
                        # TODO: don't use eval
                        phy_args[args[0]] = eval(args[1])
                self.options['--phy-args'] = phy_args
            else:
                self.options['--phy-args'] = {}
        else:
            self.options = {}

        self.umap_class_dict = {
            'audio': ('audio', 'Headset'),
            'billboard': ('billboard', 'A billboard, requires USB 2.1 and higher'),
            'cdc_acm': ('cdc_acm', 'Abstract Control Model device (like serial modem)'),
            'cdc_dl': ('cdc_dl', 'Direct Line Control device (like modem)'),
            'ftdi': ('ftdi', 'USB<->RS232 FTDI chip'),
            'hub': ('hub', 'USB hub'),
            'keyboard': ('keyboard', 'Keyboard'),
            'mass_storage': ('mass_storage', 'Disk on key'),
            'mtp': ('mtp', 'Android phone'),
            'printer': ('printer', 'Printer'),
            'smartcard': ('smartcard', 'USB<->smart card interface'),
        }
        self.umap_classes = sorted(self.umap_class_dict.keys())
        self.logger = self.get_logger()
        self.num_processed = 0
        self.fuzzer = None
        self.setup_packet_received = False

        self.get_backend()

    def get_backend(self):
        self.backend = Phy(
                setup_pkt_recvd=self.signal_setup_packet_received)

    def get_logger(self):
        levels = {
            0: logging.INFO,
            1: logging.DEBUG,
            # verbose is added by numap.__init__ module
            2: logging.VERBOSE,
        }
        verbose = self.options.get('--verbose', 0)
        logger = logging.getLogger('numap')
        if verbose in levels:
            set_default_handler_level(levels[verbose])
        else:
            set_default_handler_level(logging.VERBOSE)
        if self.options.get('--quiet', False):
            set_default_handler_level(logging.WARNING)
        return logger

    def load_phy(self, *args, **kwargs):
        # TODO: support options; bring GadgetFS into FaceDancer2?

        # get phy arguments
        phy_args = self.options['--phy-args']
        return self.backend.get_phy(*args, **kwargs, **phy_args)

    def load_device(self, dev_name, phy):
        if dev_name in self.umap_classes:
            self.logger.info('Loading USB device %s' % dev_name)
            module_name = self.umap_class_dict[dev_name][0]
            module = importlib.import_module('numap.dev.%s' % module_name)
        else:
            self.logger.info('Loading custom USB device from file: %s' % dev_name)
            dirpath, filename = os.path.split(dev_name)
            modulename = filename[:-3]
            if dirpath in sys.path:
                sys.path.remove(dirpath)
            sys.path.insert(0, dirpath)
            module = __import__(modulename, globals(), locals(), [], -1)
        usb_device = module.usb_device
        kwargs = self.get_user_device_kwargs()
        dev = usb_device(self, phy, **kwargs)
        return dev

    def get_user_device_kwargs(self):
        '''
        if user provides values for the device, get them here
        '''
        kwargs = {}
        self.update_from_user_param('--vid', 'vid', kwargs, 'int')
        self.update_from_user_param('--pid', 'pid', kwargs, 'int')
        return kwargs

    def update_from_user_param(self, flag, arg_name, kwargs, type):
        val = self.options.get(flag, None)
        if val is not None:
            if type == 'int':
                kwargs[arg_name] = int(val, 0)
                self.logger.info('Setting user-supplied %s: %#x' % (arg_name, kwargs[arg_name]))
            else:
                raise Exception('arg type not supported!!')

    def signal_setup_packet_received(self):
        '''
        Signal that we received a setup packet from the host (host is alive)
        '''
        self.setup_packet_received = True

    def should_stop_phy(self):
        '''
        :return: whether phy should stop serving.
        '''
        return False

    def usb_function_supported(self, reason=None):
        '''
        Callback from a USB device, notifying that the current USB device
        is supported by the host.
        By default, do nothing with this information

        :param reason: reason why we decided it is supported (default: None)
        '''
        pass

    def get_mutation(self, stage, data=None):
        '''
        mutation is only needed when fuzzing
        '''
        return None
