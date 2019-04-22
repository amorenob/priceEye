# -*- coding: utf-8 -*-
import scrapy
from priceEye.items import ExitoItem
import re

class ExitoSpider(scrapy.Spider):
    name = "exito"
    allowed_domains = ["www.exito.com"]
   # start_urls = ['https://www.exito.com/Tecnologia-TV_y_Video-Televisores/_/N-2csn?No=0&Nrpp=80']

    def start_requests(self):
        #update categories
        urls = [
            'https://www.exito.com/Tecnologia-TV_y_Video-Televisores/_/N-2csn?',
            'https://www.exito.com/Electrohogar-Grandes_Electrodomesticos-Neveras/_/N-2ai7?',
            'https://www.exito.com/Electrohogar-Grandes_Electrodomesticos-Lavadoras_y_Secadoras/_/N-2aie?',
            'https://www.exito.com/Electrohogar-Pequenos_Electrodomesticos-Aires_y_ventiladores/_/N-2ajl?',
            'https://www.exito.com/Electrohogar-Pequenos_Electrodomesticos-Preparacion_de_alimentos/_/N-2aj2?',
            'https://www.exito.com/Tecnologia-Celulares_y_accesorios-Smartphones/_/N-2b5t?'
        ]
        for wurl in urls:
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
