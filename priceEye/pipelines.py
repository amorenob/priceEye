# -*- coding: utf-8 -*-
# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
import pymongo
import os
from datetime import datetime as dt
from scrapy.exceptions import DropItem

class PriceeyePipeline(object):
    def process_item(self, item, spider):
        return item

class JustOnePerDayPipeline(object):
    """Pipeline for keeping a daily cache file of seen items"""
    path = os.curdir + '/cache'
    
    def __init__(self):
        self.seen_item = set()
        self.fname = '_'.join(['seen', dt.today().strftime('%Y%m'), "d", str(dt.today().day)])
        self.file = None

    def open_spider(self, spider):
        """ Update seen items set from file
        """
        if not os.path.exists(self.path):
            os.makedirs(self.path)
        file_name =  '_'.join(['seen', dt.today().strftime('%Y%m'), "d", str(dt.today().day)])
        self.file = open(os.path.join(self.path, file_name), 'a+')
        self.file.seek(0)
        self.seen_item.update(x.rstrip() for x in self.file)

    def close_spider(self, spider):
        self.file.close()

    def process_item(self, item, spider):
        if item['sku'] in self.seen_item:
            raise DropItem("Duplicate item found: %s" % item)
        else:
            self.seen_item.add(item['sku'])
            self.file.write(item['sku'] + os.linesep)
            return item


class MongoPipeline(object):
    collection_name = 'exitoProducts'
    time_serie_collection_name = 'exitoPrices'

    def __init__(self, mongo_uri, mongo_db):
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db
        
    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_uri=crawler.settings.get('MONGO_URI'),
            mongo_db=crawler.settings.get('MONGO_DATABASE', 'items')
        )
    
    def open_spider(self, spider):
        self.client = pymongo.MongoClient(self.mongo_uri)
        self.db = self.client[self.mongo_db]
    

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):
        key = {'sku':item['sku']}
        price_info = {k: dict(item)[k] for k in ('prices', 'discount_rate', 'sku')}
        self.db[self.collection_name].update(key, item, upsert=True)
        self.db[self.time_serie_collection_name].insert_one(price_info)
        return item


