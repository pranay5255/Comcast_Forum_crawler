# -*- coding: utf-8 -*-
import scrapy
import re
import unicodedata
from scrapy.selector import Selector
from scrapy.utils.response import get_base_url
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor as sle
from scrapy.item import Item, Field

class comcastItem(Item):
    user = Field()
    rank = Field()
    header = Field()
    category = Field()
    link = Field()
    sub_category = Field()
    time = Field() 
    date = Field()
    comments = Field()
    answered = Field()    

class ComcastSpider(scrapy.Spider):
    
    name = 'comcast'
    allowed_domains = ['forums.xfinity.com']
    start_urls = ["https://forums.xfinity.com//",]
        
    rules = [
        Rule(sle(allow=("https://forums.xfinity.com//")), callback='parse',follow=True),
#         Rule(sle(allow=("/[^/]+$", )), follow=True),
#         Rule(sle(allow=("/$", )), follow=True),
    ]
        

    def parse(self, response):
        sel = response.css('ul.categories-list li.category-item')
        
        for div in sel:
            sub_urls = div.css('li.custom-board-list-item a::attr(href)').extract()
            main_cat = div.css('div.category-title-content::text').extract_first()
#         print len(urls)

            for i in range(len(sub_urls)):
            
                request = (scrapy.Request(url=sub_urls[i],callback=self.parse_lvl2))
                request.meta['mcat'] = main_cat
                yield request
        
    
    def parse_lvl2(self,response):
        main_cat=response.meta.get('mcat')
        lvl2_urls = response.css('h2.message-subject a::attr(href)').extract()
        format_lvl2_urls=[]
        url_cont_lvl2=list()
        for i in lvl2_urls:
            format_lvl2_urls.append(response.urljoin(i))
            
        for url in format_lvl2_urls:
            request = scrapy.Request(url=url,callback=self.parse_lvl3)
            request.meta['mcat'] = main_cat
            yield request
            
            
        next_page_lvl2_url= response.css('li.lia-paging-page-next.lia-component-next a::attr(href)').extract_first()
        if next_page_lvl2_url:
            request = scrapy.Request(url=str(next_page_lvl2_url),callback=self.parse_lvl2)
            request.meta['mcat'] = main_cat
            yield request

    
    def parse_post(self,response):
        span = response.css('div.lia-message-body-content span::text').extract()
        span=" ".join(span)
        main = response.css('div.lia-message-body-content::text').extract()
        main= " ".join(main)
        p = response.css('div.lia-message-body-content p::text').extract()
        p = " ".join(p)
        
        comm = span +'   '+ main +'   '+ p
        com = self.date_cleaner(comm)
        return self.cat_clean(com)


    def parse_lvl3(self,response):
        main_cat = response.meta.get('mcat')
        items=[]
        for post in response.css('div.lia-linear-display-message-view'):
            
            item = comcastItem()
            item['user']=post.css('span.login-bold::text').extract_first()
            item['rank']=post.css('div.lia-linear-display-message-view div.lia-message-author-rank.lia-component-author-rank::text').extract_first().strip('\t\n\r')
            item['header']=post.css('h5::text').extract_first()
            item['category']=self.cat_clean(main_cat)
            item['link']=response.url
            item['sub_category']=self.category_extract(response.url)
            item['time']=post.css('span.local-time::text').extract_first()
            item['date']=self.date_cleaner(post.css('span.local-date::text').extract_first())
            item['comments']=self.parse_post(post)
            item['answered']=self.checker(post.css('span.lia-thread-solved lia-component-solved-indicator'))
            
            
                
            items.append(item)
            
        return items
            
    
        
    def category_extract(self,url):
        category=re.findall(r'(t5)(\/.*?\/)(.*/)',url)
        cat=(re.sub(r'\W',' ',category[0][1]))
        return cat
    def date_cleaner(self,date):
        cl_dt=date.encode('ascii','ignore')
        return cl_dt
    def cat_clean(self,cat):
        cl_cat=re.findall(r'[^\s]\w+',cat)
        cl_cat=" ".join(cl_cat)
        return cl_cat
    def checker(self,string):
        if string:
            return True
        else:
            return False
        
     
            
        
        
