# -*- coding: utf-8 -*-
import re
import scrapy
from scrapy.http import HtmlResponse
from scrapy_playwright.page import PageMethod
from priceEye.items import Producto

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
        url ='https://www.exito.com/tecnologia/televisores'

         # GET request
        yield scrapy.Request(
                url,
                callback=self.parse, 
                meta=dict(
                    playwright = True,
                    playwright_include_page = True, 
                    playwright_page_methods =[
                        PageMethod("wait_for_selector", "//a[contains(@class,'productDefaultDescription')]"),
                        PageMethod("evaluate", """
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
                        """),
                        PageMethod("wait_for_timeout", 2000),
                        ],
                    page_number = 1,
                    base_url = url,
                    )
                )
        
    async def parse(self, response):
        page = response.meta["playwright_page"]
        screenshot = await page.screenshot(path="page.png", full_page=True)
        # wait for mostrar mas button
        

        # get all products
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

        # check for mostrar mas button
        if response.xpath("//div[contains(text(),'Mostrar más')]").get():
            # get next page, 
            page_number = response.meta["page_number"]
            base_url = response.meta["base_url"]
            next_page_number = page_number + 1
            next_page = base_url + '?page=' + str(next_page_number)

            if next_page:
                # GET request
                yield scrapy.Request(
                        next_page,
                        callback=self.parse, 
                        meta=dict(
                            playwright = True,
                            playwright_include_page = True, 
                            playwright_page_methods =[
                                PageMethod("wait_for_selector", "//a[contains(@class,'productDefaultDescription')]"),
                                PageMethod("evaluate", """
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
                                """),
                                PageMethod("wait_for_timeout", 2000),
                                ],
                            page_number = next_page_number,
                            base_url = base_url,
                            )
                        )

