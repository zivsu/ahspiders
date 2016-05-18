#coding:utf8

import logging
import sys

try:
    import curses
except ImportError:
    curses = None

RESET_SEQ = "\033[0m"
COLOR_SEQ = "\033[1;%dm"
BOLD_SEQ = "\033[1m"

BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = range(8)

def _stderr_supports_color():
    color = False
    if curses and hasattr(sys.stderr, 'isatty') and sys.stderr.isatty():
        try:
            curses.setupterm()
            if curses.tigetnum("colors") > 0:
                color = True
        except Exception:
            pass
    return color

class ColoredFormatter(logging.Formatter):

    DEFAULT_FORMAT = "%(color_seq)s[ %(asctime)s %(module)s:%(lineno)d]%(reset_seq)s %(levelname)s:%(message)s"
    DEFAULT_FMT = '%Y%m%d %H:%M:%S'
    DEFAULT_COLORS = {
        'WARNING':YELLOW,
        'INFO':GREEN,
        'DEBUG':BLUE,
        'ERROR':RED
    }

    def __init__(self, use_color=True, fmt=DEFAULT_FORMAT, datefmt=DEFAULT_FMT):
        logging.Formatter.__init__(self, datefmt=datefmt)
        self._fmt = fmt
        self._use_color = use_color

    def format(self, record):
        levelname = record.levelname
        if self._use_color and _stderr_supports_color() and (levelname in self.DEFAULT_COLORS):
            record.color_seq = COLOR_SEQ % (30 + self.DEFAULT_COLORS[levelname])
            record.reset_seq = RESET_SEQ
            record.bold_seq = BOLD_SEQ
        return super(ColoredFormatter, self).format(record)


def init():
    #root logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    formatter = ColoredFormatter()
    sh = logging.StreamHandler()
    sh.setFormatter(formatter)
    logger.addHandler(sh)
    return logger

init()
