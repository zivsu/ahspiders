# !/usr/bin/env python
# coding=utf-8

import re
import json
import urllib

import requests

def get_live_room_info(url):
    partern_str = r"var \$ROOM = (.*?)\$ROOM\.args = (.*?)\$ROOM\.share"
    room_partern = re.compile(partern_str, flags=re.DOTALL)
    headers = {
        "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Connection":"keep-alive",
        "Host":"www.douyu.com",
        "User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36"
    }
    r = requests.get(url, headers=headers)
    content = r.content

    room_info = None
    room_ext = None
    match = room_partern.search(content)
    if match:
        # Get room info.
        target = match.group(1).strip()
        room_info_str = r"{}".format(target[:-1])
        room_info = json.loads(room_info_str)

        # Get room ext args
        target = match.group(2).strip()
        room_ext_str = r"{}".format(target[:-1])
        room_ext = json.loads(room_ext_str)
    return room_info, room_ext

def str_unquote(quote_str):
    if not isinstance(quote_str, basestring):
        return None
    return urllib.unquote(quote_str)

def make_wireshark_filter_str(server_list):
    """Conver server list to wireshark(capture packet tool) filter condition

    `server_list` as [{"ip":"119.90.49.93","port":"8062"}]
    """
    if not isinstance(server_list, list):
        return None
    # filters = (server["port"] for server  in server_list)
    # filter_str = "tcp.port in {{{}}}".format(" ".join(filters))
    filters = ("ip.addr=={}".format(server["ip"]) for server  in server_list)
    filter_str = "||".join(filters)
    return filter_str

if __name__ == '__main__':
    url = "http://www.douyu.com/32892"
    room_info, room_ext = get_live_room_info(url)
    server_config_str = room_ext.get("server_config", None)
    server_str = str_unquote(server_config_str)
    if server_str is not None:
        server_list = json.loads(server_str)
        print make_wireshark_filter_str(server_list)