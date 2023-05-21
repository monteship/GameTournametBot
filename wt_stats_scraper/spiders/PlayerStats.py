import datetime

import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from ..items import PlayerItem
from ..settings import CLAN_URL


class PlayerStatsSpider(scrapy.Spider):
    name = "PlayerStats"
    table_name = None
    start_urls = [CLAN_URL]

    def __init__(self, table_name, **kwargs):
        super().__init__(**kwargs)
        self.table_name = table_name

    def parse(self, response):
        grid = response.css('.squadrons-members__grid-item')
        for i in range(7, len(grid), 6):
            yield PlayerItem(
                nick=grid[i].css('a::attr(href)').re_first(r'nick=(.*)'),
                rating=grid[i + 1].css('::text').re_first(r'\d+'),
                activity=grid[i + 2].css('::text').re_first(r'\d+'),
                role=grid[i + 3].css('::text').re_first(r'\w+'),
                date_joined=datetime.datetime.strptime(
                    grid[i + 4].css('::text').re_first(r'\d+.\d+.\d+'), "%d.%m.%Y").date()
            )
