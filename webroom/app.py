# !/usr/bin/env python
# coding=utf-8

import sys
import os.path
from collections import deque
import json
import logging

sys.path.append(os.path.join(os.path.dirname(__file__)))

import log


def v2ex_spiders_crawl():
    from v2ex_area import spiders
    spiders.run()

def trip_spiders_crawl():
    from tripadvisor_area import spiders
    spiders.run()

def douyu_danmu():
    from douyu_area.douyu_utils import get_live_room_info, str_unquote
    from douyu_area.danmu_client import DanmuClient

    url = "http://www.douyu.com/32892"
    room_info, room_ext = get_live_room_info(url)
    server_config_str = room_ext.get("server_config", None)
    server_str = str_unquote(server_config_str)
    if server_str is not None:
        server_list = json.loads(server_str)
        room = {"id":room_info["room_id"]}
        auth_dst_ip = server_list[0]["ip"]
        auth_dst_port  = int(server_list[0]["port"])
        client = DanmuClient(room, auth_dst_ip, auth_dst_port)
        client.start()
    else:
        logging.info("some error occur, please try later!")



if __name__ == '__main__':
    # v2ex_spiders_crawl()
    # trip_spiders_crawl()
    douyu_danmu()