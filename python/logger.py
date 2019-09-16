#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging


def return_logger(name, loglevel, logfile=None, logfile_level='DEBUG'):
    """ Creates logging instance with specified levels and destinations
    https://docs.python.org/3.6/howto/logging-cookbook.html#multiple-handlers-and-formatters
    Args:
        name (str): the name of the logger
        loglevel (str): e.g. 'INFO'; the level at which to log
        logfile (str): file to write separate stream to
        logfile_level (str): logging level that is written to logfile
    Returns:
        (logging.logger) instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    console = logging.StreamHandler()
    console.setLevel(logging.getLevelName(loglevel))
    console.setFormatter(
        logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
    )
    logger.addHandler(console)
    if logfile is not None:
        fh = logging.FileHandler(logfile)
        fh.setLevel(logging.getLevelName(logfile_level))
        fh.setFormatter(logging.Formatter(
            '[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)-8s %(message)s'
        ))
        logger.addHandler(fh)

    return logger
