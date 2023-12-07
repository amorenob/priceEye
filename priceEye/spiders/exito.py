# -*- coding: utf-8 -*-

import scrapy
from scrapy.http import HtmlResponse
from scrapy_playwright.page import PageMethod
from priceEye.items import Producto
import re
import yaml

class ExitoSpider(scrapy.Spider):
    name = "exito"
    allowed_domains = ["www.exito.com"]

    def start_requests(self):
        # Load config YALM file
        with open('./priceEye/spiders/config/exito.yaml', 'r') as f:
            config = yaml.safe_load(f)

        for tarjet in config['tarjets']:
            
            category = tarjet['category']
            max_pages = tarjet['max_pages']

            for page_number in range(1, max_pages + 1):
                url = tarjet['url'] + '?page=' + str(page_number)
                yield scrapy.Request(
                        url,
                        callback=self.parse, 
                        meta=dict(
                            playwright = True,
                            playwright_include_page = True, 
                            playwright_page_methods =[
                                PageMethod("wait_for_selector", "//a[contains(@class,'productDefaultDescription')]"),
                                PageMethod("wait_for_timeout", 2000),
                                ],
                            base_url = url,
                            category = category,
                            )
                        )


    
    async def parse(self, response):
        page = response.meta["playwright_page"]


        # Scroll to the bottom of the page
        await page.evaluate("""
            new Promise((resolve) => {
                var totalHeight = 0;
                var distance = 100;
                var timer = setInterval(() => {
                    window.scrollBy(0, distance);
                    totalHeight += distance;

                    if (totalHeight >= document.body.scrollHeight){
                        clearInterval(timer);
                        resolve();
                    }
                }, 100);
            })
        """)
        await page.wait_for_timeout(2000)

        # Get the updated HTML content
        html_content = await page.content()

        # Create a new response object with the updated HTML
        response = HtmlResponse(url=response.url, body=html_content, encoding='utf-8')

        # Get all products
        products = response.xpath("//a[contains(@class,'productDefaultDescription')]")

        for product in products:
            item = Producto()
            item["name"] = product.xpath(".//h3[contains(@class,'productNameContainer')]/span/text()").get()
            item["url"] = "https://www.exito.com" + product.xpath(".//@href").get()
            item["price"] = product.xpath(".//div[contains(@class,'PricePDP')]/span/text()").get()
            item["fake_price"] = product.xpath(".//div[contains(@class,'list-price')]/span/text()").get()
            match = re.search(r'-(\d+)(/p|-mp/p)', item["url"] )
            if match:
                item['sku'] = match.group(1)
            else:
                item['sku'] = ""
            item['brand'] = product.xpath(".//span[contains(@class,'productBrandName')]/text()").get()
            item["category"] = 1
            item["description"] = ""
            item["website"] = "exito.com"
            yield item

        await page.close()



