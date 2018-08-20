#!/usr/bin/env python3

import logging
import sys


def getLogger(name):
    # Logging configuration
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    # Log formatter
    formatter = logging.Formatter("[%(asctime)s] %(levelname)-8s %(message)s")
    # Log File handler
    handler = logging.FileHandler("../log/%s.log" % name)
    handler.setLevel(logging.INFO)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    # Screen handler
    screenHandler = logging.StreamHandler(stream=sys.stdout)
    screenHandler.setLevel(logging.INFO)
    screenHandler.setFormatter(formatter)
    logger.addHandler(screenHandler)
    return logger


if __name__ == '__main__':
    getLogger("test")
