import datetime

import scrapy
from scrapy.http import TextResponse

from ..items import ClanItem


def get_timestamp():
    current_time = datetime.datetime.utcnow()
    future_time = current_time + datetime.timedelta(hours=3)
    timestamp = future_time.timestamp() * 1000
    return "{:.0f}".format(timestamp)


class LeaderBoardStatsSpider(scrapy.Spider):
    name = "LeaderBoardStats"
    start_url = "https://warthunder.com/en/community/getclansleaderboard/dif/_hist/page/{page}/sort/dr_era5?_={time}"
    custom_settings = {
        "ITEM_PIPELINES": {
            "wt_stats_scraper.pipelines.ClansWTPipeline": 300,
        }
    }

    def start_requests(self):
        timestamp = get_timestamp()
        for page in range(1, 4):
            yield scrapy.Request(self.start_url.format(page=page, time=timestamp))

    def __init__(self, table_name, **kwargs):
        super().__init__(**kwargs)
        self.table_name = table_name

    def parse(self, response: TextResponse, **kwargs):
        clans = response.jmespath("data")
        for clan in clans:
            rank = int(clan.jmespath("pos").get("0")) + 1
            tag = clan.jmespath("tagl").get()
            name = clan.jmespath("lastPaidTag").get()
            members = int(clan.jmespath("members_cnt").get("0"))
            rating = int(clan.jmespath("astat.dr_era5_hist").get("0"))
            kills = sum(
                [
                    int(k)
                    for k in clan.jmespath("astat.[akills_hist, gkills_hist]").getall()
                ]
            )
            deaths = int(clan.jmespath("astat.deaths_hist").get("0"))
            kills_to_death = round(kills / deaths, 2)
            yield ClanItem(
                rank=rank,
                tag=tag,
                name=name,
                members=members,
                rating=rating,
                kills_to_death=kills_to_death,
            )
