# !/usr/etc/env python
# coding=utf-8

import threading
import logging
import base64
from multiprocessing.dummy import Pool as ThreadPool

import requests


"""
http://www.36dsj.com/archives/40809

反爬虫：（用户请求的Headers，用户行为，网站目录和数据加载方式）
1、用户请求的Headers（User-Agent、Referer）
   --措施：添加User-Agent、Referer
2、检测用户行为：同一IP短时间内多次访问同一页面，或者同一账户短时间内多次进行相同操作
   --措施：使用代理、请求隔几秒
3、动态页面的反爬虫：数据是通过ajax请求得到，或者通过JavaScript生成的
   --措施：selenium+phantomJS框架，利用phantomJS执行js来模拟人为操作
"""

def send_crawl_requset(url, **kwargs):
    r = requests.get(url, **kwargs)
    return r.status_code, r.content

_TO_UNICODE_TYPES = (unicode, type(None))

def to_unicode(value):
    """Only support py2"""
    if isinstance(value, _TO_UNICODE_TYPES):
        return value
    if not isinstance(value, bytes):
        raise TypeError(
            "Expected bytes, unicode, or None; got %r" % type(value)
        )
    return value.decode("utf-8")


class CrawlThread(threading.Thread):

    def __init__(self, name, headers=None):
        super(CrawlThread, self).__init__(name=name)
        self._headers = headers or ""

    def run(self):
        logging.info("{} run...".format(self.name))
        self.crawl()

    def crawl(self):
        raise NotImplementedError()


class Proxy(object):

    """prepare and store proxies in db so that choose proxy to switch"""

    def __init__(self, max_page=1):
        self.max_page = max_page
        self.proxies = []
        self.checked_proxies = []
        self.headers = {
            'Host': 'proxy.peuland.com',
            'Origin': 'https://proxy.peuland.com',
            'Referer': 'https://proxy.peuland.com/proxy_list_by_category.htm',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2692.0 Safari/537.36',
            'X-Requested-With': 'XMLHttpRequest',
            'Cookie': 'peuland_id=35fefe23fedc52da9283ac5ed131cbab;PHPSESSID=pkm7b65es5ojb8oerc7a9i0q31; peuland_md5=ca1f57155f5638ade3c28a900fbdbd55;w_h=800; w_w=1280; w_cd=24; w_a_h=773; w_a_w=1280; php_id=1792520643'
        }
        self.url = 'https://proxy.peuland.com/proxy/search_proxy.php'

    def _parse_proxy(self):
        for i in range(1, self.max_page+1):
            req_data = {
                "type":"",
                "country_code":"",
                "is_clusters": "",
                "is_https": "",
                "level_type": "anonymous",
                "search_type": "all",
                "page": str(i),
            }
            r = requests.post(self.url, data=req_data, headers=self.headers)
            resp_data = r.json()['data']
            for line in resp_data:
                rate = int(base64.b64decode(line['time_downloadspeed']))
                if rate <= 7:
                    continue
                proxy_type = base64.b64decode(line['type'])
                ip = base64.b64decode(line['ip'])
                port = base64.b64decode(line['port'])
                self.proxies.append({proxy_type: ip + ':' + port})

    def _check_proxy(self, proxy, anonymous=False):
        pass
        # try:
        #     r = requests.get('http://httpbin.org/ip', proxies=proxy, timeout=10)
        #     data = r.json()
        #     # 高匿检测
        #     if anonymous:
        #         if data['origin'] == proxy.values()[0].split(':')[0]:
        #             self.checked_proxies.append(proxy)
        #     self.checked_proxies.append(proxy)
        # except Exception as e:
        #     print e

    def get_proxy(self):
        self._parse_proxy()
        # pool = ThreadPool(8)
        # pool.map(self._check_proxy, self.proxies)
        # pool.close()
        # pool.join()
        # return self.checked_proxies
        return self.proxies


if __name__ == '__main__':
    proxy = Proxy(max_page=12)
    print proxy.get_proxy()
