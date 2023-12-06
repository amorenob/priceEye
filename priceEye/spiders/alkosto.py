import scrapy
from scrapy.http import HtmlResponse
from scrapy_playwright.page import PageMethod
from priceEye.items import Producto
from PIL import Image
from io import StringIO
import logging
import time

class AlkostoSpider(scrapy.Spider):
    name = "alkosto"
    allowed_domains = ["alkosto.com"]
    start_urls = ["https://alkosto.com"]

    def start_requests(self):
        url = "https://www.alkosto.com/tv/smart-tv/c/BI_120_ALKOS"
        yield scrapy.Request(
                url,
                callback=self.parse, 
                meta=dict(
                    playwright = True,
                    playwright_include_page = True, 
                    playwright_page_methods =[
                        PageMethod("wait_for_selector", "div.product__item__information"),
                    ])
                )

    async def parse(self, response):
        #page = response.meta["playwright_page"]
        #screenshot = await page.screenshot(path="page.png", full_page=True)
        # load more products
        page = response.meta["playwright_page"]
        
        try:
            while button := page.locator("//button[contains(@class,'InfiniteHits')]"):
                await button.scroll_into_view_if_needed()
                await button.click()
                await page.wait_for_timeout(1000)
        except:
            pass

        # Get the updated HTML content
        html_content = await page.content()

        # Create a new response object with the updated HTML
        response = HtmlResponse(url=response.url, body=html_content, encoding='utf-8')

        # get all div.product__item__information
        products = response.css("div.product__item__information")

        for product in products:
            item = Producto()
            item["name"] = product.css("a::attr(title)").get()
            item["url"] = product.css("a::attr(href)").get()
            item["price"] = product.css("span.price::text").get()
            item["fake_price"] = product.xpath(".//p[contains(@class,'discounts__old')]/text()").get()
            item['sku'] = product.css('a::attr(data-id)').get()
            item['brand'] = product.css('div.product__item__information__brand::text').get()
            item["category"] = 1
            item["description"] = ""
            item["website"] = "alkosto.com"
            yield item
              