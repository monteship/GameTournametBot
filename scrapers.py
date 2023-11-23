import datetime

import parsel
import pydantic
import requests

from settings import ClanCredentials, CLANS


class ScrapedClanItem(pydantic.BaseModel):
    rank: int
    name: str
    tag: str
    members: int
    rating: int
    kills_to_death: float


class GlobalLeaderboardItem(pydantic.BaseModel):
    clans: list[ScrapedClanItem]


def get_timestamp():
    current_time = datetime.datetime.utcnow()
    future_time = current_time + datetime.timedelta(hours=3)
    timestamp = future_time.timestamp() * 1000
    return "{:.0f}".format(timestamp)


class ClansLeaderboardScraper:
    url = "https://warthunder.com/en/community/getclansleaderboard/dif/_hist/page/{page}/sort/dr_era5?_={time}"

    def __init__(self):
        self._leaderboard = GlobalLeaderboardItem(clans=[])
        timestamp = get_timestamp()
        for page in range(1, 4):
            page = requests.get(self.url.format(page=page, time=timestamp))
            if page.status_code != 200:
                continue
            self.parse_leaderboard(page)

    @property
    def get_leaderboard(self) -> GlobalLeaderboardItem:
        return self._leaderboard

    def parse_leaderboard(self, page):
        for quote in page.json()["data"]:
            stats = quote["astat"]
            self._leaderboard.clans.append(
                ScrapedClanItem(
                    rank=quote["pos"] + 1,
                    tag=quote["tagl"],
                    name=quote["lastPaidTag"],
                    members=quote["members_cnt"],
                    rating=stats["dr_era5_hist"],
                    kills_to_death=round(
                        (stats["akills_hist"] + stats["gkills_hist"])
                        / stats["deaths_hist"],
                        2,
                    ),
                )
            )


class ScrapedPlayerItem(pydantic.BaseModel):
    nick: str
    rating: int
    activity: int
    role: str
    date_joined: datetime.date
    clan: str


class ClanLeaderboardItem(pydantic.BaseModel):
    players: list[ScrapedPlayerItem]


class PlayersLeaderboardScraper:
    def __init__(self, clans: [ClanCredentials]):
        self._leaderboard = ClanLeaderboardItem(players=[])
        for clan in clans:
            page = requests.get(clan.url)
            if page.status_code != 200:
                return
            self.parse_leaderboard(parsel.Selector(text=page.text), clan.tag)

    @property
    def get_leaderboard(self) -> ClanLeaderboardItem:
        return self._leaderboard

    def parse_leaderboard(self, page: parsel.Selector, clan_tag: str):
        grid = page.css(".squadrons-members__grid-item")
        for i in range(7, len(grid), 6):
            self._leaderboard.players.append(
                ScrapedPlayerItem(
                    nick=grid[i].css("a::attr(href)").re_first(r"nick=(.*)"),
                    rating=grid[i + 1].css("::text").re_first(r"\d+"),
                    activity=grid[i + 2].css("::text").re_first(r"\d+"),
                    role=grid[i + 3].css("::text").re_first(r"\w+"),
                    date_joined=datetime.datetime.strptime(
                        grid[i + 4].css("::text").re_first(r"\d+.\d+.\d+"), "%d.%m.%Y"
                    ).date(),
                    clan=clan_tag,
                )
            )


if __name__ == "__main__":
    scraper = ClansLeaderboardScraper()
    leaders = scraper.get_leaderboard
    print(leaders)
    for _clan in CLANS:
        scraper = PlayersLeaderboardScraper(_clan)
        leaders = scraper.get_leaderboard
        print(leaders)
