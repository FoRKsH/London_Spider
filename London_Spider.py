import re
import scrapy
from scrapy import Request
from scrapy.loader import ItemLoader

from itemloaders.processors import Join

page_count = 0

class Property(scrapy.Item):
    title = scrapy.Field(output_processor=Join())
    price = scrapy.Field(output_processor=Join())
    url = scrapy.Field(output_processor=Join())


class LondonrelocationSpider(scrapy.Spider):
    name = 'londonrelocation'
    allowed_domains = ['londonrelocation.com']
    start_urls = ['https://londonrelocation.com/properties-to-rent/']

    def parse(self, response):
        for start_url in self.start_urls:
            yield Request(start_url,
                          callback=self.parse_area)

    def parse_area(self, response):
        area_urls = response.xpath('.//div[contains(@class,"area-box-pdh")]//h4/a/@href').extract()
        for area_url in area_urls:
            yield Request(url=area_url,callback=self.parse_area_pages)

    def parse_area_pages(self, response):
        global page_count 
        titles = response.xpath("//div[@class= 'right-cont']/div/h4/a/text()").extract()
        prices = response.xpath("//div[@class= 'right-cont']/div[3]/h5/text()").extract()
        urls = response.xpath("//div[@class= 'right-cont']/div/h4/a/@href").extract()
        
        for (title,price,url) in zip(titles,prices,urls):
            
            factor = 4 if 'pw' in price else 1
            price = str(int(re.sub("[^0-9]","",price))*factor)

            property = ItemLoader(item=Property())
            property.add_value('title', title)
            property.add_value('price', price)
            property.add_value('url', 'londonrelocation.com'+url)
            yield property.load_item()

        # get first 2 pages only    
        page_count +=1
        if page_count>2:
            page_count =0
            return 

        pagination =response.xpath("//div[@class='pagination']/ul/li").extract()
        if len(pagination)>3:
            index = next(i for i,x in enumerate(pagination) if '<a' not in x) # first element with no children
            next_page = response.xpath("//div[@class='pagination']/ul/li/a/@href").extract()[index]
        
        if next_page:
            next_page = response.urljoin(next_page)
            yield scrapy.Request(next_page,callback=self.parse_area_pages)
        