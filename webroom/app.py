# !/usr/bin/env python
# coding=utf-8

import sys
import os.path
from collections import deque

sys.path.append(os.path.join(os.path.dirname(__file__)))

import log


def v2ex_spiders_crawl():
    from v2ex_area import spiders
    spiders.run()

def trip_spiders_crawl():
    from tripadvisor_area import spiders
    spiders.run()

if __name__ == '__main__':
    # v2ex_spiders_crawl()
    trip_spiders_crawl()