import logging
"""

It generated a log file which contains specifically errors, info and Exceptions occuring in the application,
used for detecting and fixing errors/bugs in the app.

Parameters:
-----------

> None

Returns:
--------

> None

"""

logging.basicConfig(filename='logs.log', filemode='a',
                    format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S',
                    level=logging.INFO)

logger = logging.getLogger()

if __name__ == '__main__':
    logger.debug('This is a debug message:')
    logger.info('This is an info message:')
    logger.warning('This is an warning message:')
    logger.error('This is an error message:')
    logger.critical('This is a critical message:')
