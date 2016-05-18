# !/usr/bin/env python
# coding=utf-8

import re
import time
import logging
import random
from collections import deque

from utils import send_crawl_requset, CrawlThread
from database import init as db_init
from settings import user_agents

_HOST = "https://www.v2ex.com"
_END_SINGLE = "EOF"
_COLL_NAME = "v2ex_job"

class CrawlURLThread(CrawlThread):

    def __init__(self, name, job_routes, init_route, host=_HOST, headers=None, delay=3):
        """`CrawlURLThread` constructor.

        :arg name: The thread name
        :arg job_routes: Store job site routes
        :arg init_route: The thread crawl site start with the route
        """
        assert isinstance(job_routes, deque)
        super(CrawlURLThread, self).__init__(name, headers=headers)
        self._init_route = init_route
        self._job_routes = job_routes
        self._host = host
        self._delay = delay

    def crawl(self):
        route = self._init_route

        # re compile pattern
        next_page_pattern = re.compile("normal_page_right.*?href='(.*?)';")
        job_route_pattern = re.compile('item_title"><a href="(.*?)#reply')

        while route:
            # Crawl content in current page.
            crawl_url = self._host + route
            kwargs = {"headers":self._headers}
            status_code, content = send_crawl_requset(crawl_url, **kwargs)

            # Find all jobs routes.
            ext_routes = re.findall(job_route_pattern, content)
            self._job_routes.extend(ext_routes)

            # Find next article page to continue crawl articles route
            match = re.search(next_page_pattern, content)
            route = match.group(1) if match else None

            # Set time delay to avoid limit IP
            time.sleep(self._delay)

        self._job_routes.append(_END_SINGLE)

class CrawlJobThread(CrawlThread):

    def __init__(self, name, routes, db, host=_HOST, headers=None, req_timeout=30, delay=5):
        """`CrawlJobThread` constructor.

        :arg name: The thread name
        :arg routes: Crawl job content from site routes
        """
        assert isinstance(routes, deque)
        super(CrawlJobThread, self).__init__(name, headers=headers)
        self._routes = routes
        self._db = db
        self._host = host
        self._req_timeout = req_timeout
        self._delay = delay

    def crawl(self):
        pattern_str1 = 'topic_content">(.*?)<div>'
        pattern_str2 = 'markdown_body">(.*?)</div>'
        pattern1 = re.compile(pattern_str1, flags=re.DOTALL)
        pattern2 = re.compile(pattern_str2, flags=re.DOTALL)
        while True:
            try:
                job_route = self._routes.popleft()
            except IndexError:
                logging.info("{} sleep...".format(self.name))
                time.sleep(0.5)
                continue

            if job_route == _END_SINGLE:
                # No route to crawl, then should exit.
                self._routes.append(job_route)
                break

            # Crawl content in current page.
            crawl_url = self._host + job_route
            kwargs = {"headers":self._headers, "timeout":self._req_timeout}
            status_code, content = send_crawl_requset(crawl_url, **kwargs)

            # Find next article page to continue crawl job content route.
            match = pattern2.search(content) or pattern1.search(content)
            if match:
                # Get target content and filter html tag.
                # target_content = to_unicode(_HTML_PATTERN.sub("", match.group(0)))
                main_content = match.group(0)

                # Get current reply number.
                reply_num_pattern = re.compile(r'<span class="gray">(\d+)')
                reply_num_match = reply_num_pattern.search(content)
                reply_num = reply_num_match.group(1) if reply_num_match else 0

                # Get visit amount and publish time.
                ext_pattern = re.compile('class="gray">.*?/member/.*?</a>(.*?)</small>')
                ext_match = ext_pattern.search(content)
                ext_info = ext_match.group(1) if ext_match else ""

                spec_doc = {
                    "url":crawl_url,
                    "content":main_content,
                    "ext":ext_info,
                    "reply_num":reply_num
                }
                self._db[_COLL_NAME].insert(spec_doc, w=1)

            # Set time delay to avoid limit IP
            time.sleep(self._delay)


db = db_init(db_name="spider")

def run():
    logging.info("spiders start work...")
    user_agent = random.choice(user_agents)
    headers = {
        "User-agent":user_agent,
        "Referer":"https://www.v2ex.com",
        "accept":"text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Host":"www.v2ex.com",
    }
    def prepare_threads():
        thread_list = []
        name = "crawl_url_thread1"
        job_routes = deque()
        init_route = "/go/jobs"

        crawl_url_thread = CrawlURLThread(name, job_routes, init_route,
                                          headers=headers)
        crawl_url_thread.start()
        thread_list.append(crawl_url_thread)

        for i in range(1,3):
            name = "crawl_job_thread{}".format(i)
            crawl_job_thread = CrawlJobThread(name, job_routes, db)
            crawl_job_thread.start()
            thread_list.append(crawl_job_thread)
        return thread_list

    threads = prepare_threads()
    # Wait until the thread terminates.
    for thread in threads:
        thread.join()
    logging.info("spiders stop work...")