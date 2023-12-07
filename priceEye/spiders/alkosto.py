import scrapy
from scrapy.http import HtmlResponse
from scrapy_playwright.page import PageMethod
from priceEye.items import Producto
import yaml

class AlkostoSpider(scrapy.Spider):
    name = "alkosto"
    allowed_domains = ["alkosto.com"]
    start_urls = ["https://alkosto.com"]

    def start_requests(self):
        # Load config YALM file
        with open('./priceEye/spiders/config/alkosto.yaml', 'r') as f:
            config = yaml.safe_load(f)

        for tarjet in config['tarjets']:
                
            tags = tarjet['tags']
            max_pages = tarjet['max_pages']

            yield scrapy.Request(
                    tarjet['url'],
                    callback=self.parse, 
                    meta=dict(
                        playwright = True,
                        playwright_include_page = True, 
                        playwright_page_methods =[
                            PageMethod("wait_for_selector", "div.product__item__information"),
                        ],
                        tags = tags,
                        )
                    )

    async def parse(self, response):
        #page = response.meta["playwright_page"]
        #screenshot = await page.screenshot(path="page.png", full_page=True)
        # load more products
        page = response.meta["playwright_page"]
        tags = response.meta["tags"]
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
            item["tags"] = tags + [item["brand"]]
            item["description"] = ""
            item["website"] = "alkosto.com"
            yield item

        await page.close()
              