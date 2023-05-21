import datetime

import scrapy

from ..items import ClanItem


def get_timestamp():
    current_time = datetime.datetime.utcnow()
    future_time = current_time + datetime.timedelta(hours=3)
    timestamp = future_time.timestamp() * 1000
    return "{:.0f}".format(timestamp)


class LeaderBoardStatsSpider(scrapy.Spider):
    name = "LeaderBoardStats"
    start_url = "https://warthunder.com/en/community/getclansleaderboard/dif/_hist/page/{page}/sort/dr_era5?_={time}"

    def __init__(self, table='squadrons_test', **kwargs):
        super().__init__(**kwargs)
        self.table = table

    def start_requests(self):
        timestamp = get_timestamp()
        for page in range(1, 4):
            yield scrapy.Request(self.start_url.format(page=page, time=timestamp))

    def parse(self, response):
        for quote in response.json()['data']:
            yield ClanItem(
                rank=quote['pos'] + 1,

                tag=quote['tagl'],

                name=quote['lastPaidTag'],

                members=quote['members_cnt'],

                rating=quote['dr_era5_hist'],

                kills_to_death=round(
                    (quote['astat']['akills_hist'] + quote['astat']['gkills_hist']) / quote['astat']['deaths_hist'], 2),

            )