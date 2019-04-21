# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class ExitoItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    sku = scrapy.Field()
    cat = scrapy.Field()
    name = scrapy.Field()
    brand = scrapy.Field()
    prices = scrapy.Field()
    discount_rate = scrapy.Field()
    pass
