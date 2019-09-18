from .credits import proxy
import scrapy
import json
import pandas as pd
import re


class InstagramSpider(scrapy.Spider):
    name = "hashtag"

    def __init__(self, hashtag='', start_index='', end_index=''):
        self.hashtag = hashtag
        try:
            self.start_index = int(start_index)
            self.end_index = int(end_index)
        except:
            self.start_index = int(input("Start index? "))
            self.end_index = int(input("End index? "))
        if hashtag == '':
            self.hashtag = input("Name of the hashtag? ")
        self.start_urls = list(pd.read_csv('htag_end_cursor.csv', sep=',').url)[self.start_index:self.end_index + 1]

    def parse(self, response):
        return self.parse_htag(response)

    def parse_htag(self, response):
        graphql = json.loads(response.text)
        has_next = graphql['graphql']['hashtag']['edge_hashtag_to_media']['page_info']['has_next_page']
        edges = graphql['graphql']['hashtag']['edge_hashtag_to_media']['edges']

        for edge in edges:
            node = edge['node']
            shortcode = node['shortcode']
            yield scrapy.Request("https://www.instagram.com/p/" + shortcode + "/?__a=1",
                                 callback=self.parse_post,
                                 meta={'proxy': proxy})
           
    def parse_post(self, response):
        graphql = json.loads(response.text)
        edges = graphql['graphql']['shortcode_media']['edge_media_to_tagged_user']['edges']
        post_url = "{0}{1}{2}".format('www.instagram.com/p/', graphql['graphql']['shortcode_media']['shortcode'], '/')
        for edge in edges:
          name = edge['node']['user']['username']
          url = '{0}{1}{2}'.format('www.instagram.com/', name, '/')
          yield scrapy.Request("https://" + url,
                               callback=self.parse_item,
                               meta={'proxy': proxy,
                                     'name':name,
                                     'url':url,
                                     'post_url':post_url})

    def parse_item(self, response):
        text = response.selector.xpath('//script[@type="application/ld+json"]').extract_first()
        if text:
            email = re.search('"email":"(?P<email>[a-zA-Z0-9\@\.\-\_]*)', text)
            phone = re.search('"telephone":"(?P<phone>[\\+0-9]*)', text)
            if email:
                email = email.group('email')
            else:
                email = ''
            if phone:
                phone = phone.group('phone')
            else:
                phone = ''
        else:
            email = ''
            phone = ''
        yield {'name':response.meta['name'],
               'url':response.meta['url'],
               'post_url':response.meta['post_url'],
               'email':email,
               'phone':phone}
