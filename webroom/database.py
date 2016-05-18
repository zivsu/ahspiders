# !/usr/bin/env python
# coding=utf-8

from pymongo import MongoClient

def init(db_name="test"):
    client = MongoClient('localhost', 27017)
    return client[db_name]