#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging


def return_logger(name, loglevel, logfile=None, logfile_level='DEBUG'):
    """ Creates logging instance with specified levels and destinations

    Args:
        name (str): the name of the logger
        loglevel (str): e.g. 'INFO'; the level at which to log
        logfile (str): file to write separate stream to
        logfile_level (str): logging level that is written to logfile
    Returns:
        (logging.logger) instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.getLevelName(loglevel))
    sh = logging.StreamHandler()
    sh.setLevel(logging.getLevelName(loglevel))
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s: %(message)s'
    )
    sh.setFormatter(formatter)
    logger.addHandler(sh)
    if logfile is not None:
        fh = logging.FileHandler(logfile)
        fh.setLevel(logging.getLevelName(logfile_level))
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    return logger


if __name__ == "__main__":
    l = return_logger(__name__, 'INFO', 'test.log', 'DEBUG')
    l.info('This should show up in the file and on screen')
    l.debug('This should only show up in the file')
    l.warning('This is a warning for everybody')
