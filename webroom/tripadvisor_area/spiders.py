# !/usr/bin/env python
# coding=utf-8

import logging
import random

from bs4 import BeautifulSoup

from utils import send_crawl_requset, CrawlThread
from database import init as db_init
from settings import user_agents

_HOST = "https://www.tripadvisor.cn"
_COLL_NAME = "trip_advisor_cn"


"""
crawl trip advisor comments of The Venetian Macao Resort Hotel
"""

class CrawlBubbleThread(CrawlThread):

    def __init__(self, name, init_route, db, host=_HOST, headers=None):
        """`CrawlBubbleThread` constructor.

        :arg name: The thread name
        :arg init_route: The thread crawl site start with the route
        """
        super(CrawlBubbleThread, self).__init__(name, headers=headers)
        self._init_route = init_route
        self._host = host
        self._db = db

    def crawl(self):
        import requests
        route = self._init_route
        while route:
            # Crawl content in current page.
            crawl_url = self._host + route
            kwargs = {"headers":self._headers}
            status_code, content = send_crawl_requset(crawl_url, **kwargs)

            soup = BeautifulSoup(content, 'html.parser')

            bubble_tags = soup.find_all("div", class_="innerBubble")
            logging.info("current url:{}".format(crawl_url))
            logging.info("current page has {} bubbles".format(len(bubble_tags)))
            for bubble_tag in bubble_tags:
                # Get related tags.
                rank_img_tag = bubble_tag.find("img", class_="rating_s_fill")
                comment_tag = bubble_tag.find("p", class_="partial_entry")
                rating_date_tag = bubble_tag.find("span", class_="ratingDate")
                quote_tag = bubble_tag.find("span", class_="noQuotes")

                if rank_img_tag is not None:
                    score = rank_img_tag.attrs["class"][2]
                    spec_doc = {
                        "url":crawl_url,
                        "score":score,
                        "comment":comment_tag.string,
                        "quote":quote_tag.string,
                        "rating_date":rating_date_tag.string
                    }
                    self._db[_COLL_NAME].insert(spec_doc, w=1)

            next_page_tag = soup.find("a", class_="nav next rndBtn ui_button primary taLnk")
            if next_page_tag is not None:
                route = next_page_tag.attrs["href"]
                logging.info("has next route and continue...")
            else:
                # print content
                # print bubble_tags
                break

db = db_init(db_name="spider")

def run():
    logging.info("spiders start work...")
    user_agent = random.choice(user_agents)
    headers = {
        "User-agent":user_agent,
        "Referer":"https://www.tripadvisor.cn",
        "accept":"*/*",
        "Host":"www.tripadvisor.cn",
    }
    headers = {}
    def prepare_thread():
        name = "crawl_thread1"
        # init_route = "/Hotel_Review-g664891-d657141-Reviews-The_Venetian_Macao_Resort_Hotel-Macau.html"
        init_route = "/Hotel_Review-g664891-d657141-Reviews-or1510-The_Venetian_Macao_Resort_Hotel-Macau.html#REVIEWS"

        crawl_thread = CrawlBubbleThread(name, init_route, db, headers=headers)
        crawl_thread.start()
        return crawl_thread

    crawl_thread = prepare_thread()
    # Wait until the thread terminates.
    crawl_thread.join()

    logging.info("spiders stop work...")