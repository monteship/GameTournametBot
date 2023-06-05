import datetime

import scrapy

from ..items import PlayerItem
from ..settings import CLAN_URL


class PlayerStatsSpider(scrapy.Spider):
    name = "PlayerStats"
    start_url = CLAN_URL
    custom_settings = {
        'ITEM_PIPELINES': {
            "wt_stats_scraper.pipelines.PlayersWTPipeline": 300,
        }
    }

    def __init__(self, table_name, **kwargs):
        super().__init__(**kwargs)
        self.table_name = table_name

    def start_requests(self):
        yield scrapy.Request(
            self.start_url,
        )

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
