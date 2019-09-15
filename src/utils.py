import logging

from src.settings import LOG_LEVEL


def setup_logger():
    logger = logging.getLogger("main")
    logger.setLevel(LOG_LEVEL())
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s',
                                  datefmt='%d.%m.%y %H:%M')
    console = logging.StreamHandler()
    console.setFormatter(formatter)
    logger.addHandler(console)
