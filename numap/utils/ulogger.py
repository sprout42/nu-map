import logging

stdio_handler = None
numap_logger = None


def prepare_logging():
    global numap_logger
    global stdio_handler
    if numap_logger is None:
        def add_debug_level(num, name):
            def fn(self, message, *args, **kwargs):
                if self.isEnabledFor(num):
                    self._log(num, message, args, **kwargs)
            logging.addLevelName(num, name)
            setattr(logging, name, num)
            return fn

        logging.Logger.verbose = add_debug_level(5, 'VERBOSE')
        logging.Logger.always = add_debug_level(100, 'ALWAYS')

        FORMAT = '[%(levelname)-6s] %(message)s'
        stdio_handler = logging.StreamHandler()
        stdio_handler.setLevel(logging.INFO)
        formatter = logging.Formatter(FORMAT)
        stdio_handler.setFormatter(formatter)
        numap_logger = logging.getLogger('numap')
        numap_logger.addHandler(stdio_handler)
        numap_logger.setLevel(logging.VERBOSE)
    return numap_logger


def set_default_handler_level(level):
    global stdio_handler
    stdio_handler.setLevel(level)
