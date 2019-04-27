# -*- coding: utf-8 -*-
import scrapy
from priceEye.items import ExitoItem
import re
import os

class ExitoSpider(scrapy.Spider):
    name = "exito"
    allowed_domains = ["www.exito.com"]
    start_urls = []
    urls_path = './priceEye/spiders/urls/exito.txt'
    with open(urls_path, 'r') as urls_file:
        for url in urls_file:
            start_urls.append(url)

    def start_requests(self):
        #update categories
        for wurl in self.start_urls:
            for i in range(6):
                url = wurl + 'No='+ str(i*80) + '&Nrpp=80'
                yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        #get all products divss
        products = response.css('div.product')
        for product in products:
            item =  ExitoItem()

            item['sku'] = product.css('::attr(data-skuid)').extract_first()
            item['cat'] = product.css('::attr(data-prdtype)').extract_first()
            #re.sub... remove special charaters from name
            item['name']  = re.sub('[\t\r\n]', '', product.css('.name::text').extract_first())
            item['brand'] = product.css('.brand::text').extract_first()
            item['prices'] = dict(zip(
                #keys : class names - price, price-before...
                product.css('.col-price p::attr(class)').extract(),
                #values : actual price
                map(lambda x:int(x.replace(',','')), product.css('.col-price p .money::text').extract())
            ))
            #get discount rate, '0' in case of not found
            item['discount_rate'] = int((product.css('.discount-rate::text').extract_first() or '0').strip())

            yield item
