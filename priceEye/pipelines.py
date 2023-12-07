# -*- coding: utf-8 -*-
# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
import pymongo
import os
import pymysql
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

class CleanItemPipeline(object):
    """Pipeline for cleaning item fields"""
    def process_item(self, item, spider):

        # handle NoneType fields
        for key in item.keys():
            if item[key] is None:
                item[key] = ''

        item['name'] = item['name'].strip()
        item['brand'] = item['brand'].strip()
        item['description'] = item['description'].strip()
        item['price'] = item['price'].strip().replace('$', '').replace('.', '').replace(',', '').replace('\xa0', '')
        item['fake_price'] = item['fake_price'].strip().replace('$', '').replace('.', '').replace(',', '').replace('\xa0', '')

        # handle empty prices, replace with 0.0
        if item['price'] == '':
            item['price'] = '0.0'
        if item['fake_price'] == '':
            item['fake_price'] = '0.0'
            
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


class MySQLPipeline(object):

    def __init__(self, host, user, password, db):
        self.host = host
        self.user = user
        self.password= password
        self.db = db

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            host=crawler.settings.get('MYSQL_HOST'),
            user=crawler.settings.get('MYSQL_USER'),
            password=crawler.settings.get('MYSQL_PASSWORD'),
            db=crawler.settings.get('MYSQL_DATABASE'),
        )

    def open_spider(self, spider):
        self.conn = pymysql.connect(
            host=self.host,
            user=self.user,
            password=self.password,
            db=self.db,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        self.cursor = self.conn.cursor()

    def process_item(self, item, spider):
        try:
            self.conn.begin()

            # Insert product data
            self.cursor.execute("""
                INSERT INTO product (sku, name, description, price, brand, website, url)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                name = VALUES(name),
                description = VALUES(description),
                price = VALUES(price),
                brand = VALUES(brand),
                website = VALUES(website),
                url = VALUES(url)
                """,
                (item['sku'], item['name'], item['description'], item['price'], item['brand'], item['website'], item['url'])
            )

            # Get product ID
            self.cursor.execute("""
                SELECT id FROM product WHERE sku = %s
                """, (item['sku'],))
            product_id = self.cursor.fetchone()['id']

            # Update price table
            self.cursor.execute("""
                INSERT INTO price_history (product_id, price, fake_price)
                VALUES (%s, %s, %s)
                """,
                (product_id, item['price'], item['fake_price'])
            )

            # Insert product tags
            for tag in item['tags']:
                self.cursor.execute("""
                    INSERT IGNORE INTO tag (name) VALUES (%s)
                """, (tag,))

                self.cursor.execute("""
                    SELECT id FROM tag WHERE name = %s
                """, (tag,))
                tag_id = self.cursor.fetchone()['id']

                self.cursor.execute("""
                    INSERT IGNORE INTO product_tag (product_id, tag_id) VALUES (%s, %s)
                """, (product_id, tag_id))

            self.conn.commit()

            return item
    
        except pymysql.Error as e:
            self.conn.rollback()
            raise DropItem(f'Error inserting item: {e}')
        
    def close_spider(self, spider):
        self.conn.close()
    
    def get_items(self):
        self.cursor.execute("SELECT * FROM product")
        return self.cursor.fetchall()
