# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class Producto(scrapy.Item):
    """Product item"""
    sku = scrapy.Field()
    name = scrapy.Field()
    url = scrapy.Field()
    tags = scrapy.Field()
    brand = scrapy.Field()
    price = scrapy.Field()
    fake_price = scrapy.Field()
    description = scrapy.Field()
    website = scrapy.Field()
    pass



