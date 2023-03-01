import time

import requests
from bs4 import BeautifulSoup
from discord_webhook import DiscordWebhook, DiscordEmbed
from selenium import webdriver
from selenium.common import TimeoutException

from config import WEBHOOK_DAY, TRACKED_CLAN_NAME, LB_URLS, EMOJI, CLAN_URL
from database import Database

# Selenium options
options = webdriver.ChromeOptions()
options.add_argument("--headless")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--no-sandbox")
options.add_argument("--disable-logging")


class Clan:
    """
    Used to represent a Clan.
    Process data from the Clan page.
    Fetch changes from database
    """
    emoji = EMOJI

    def __init__(self, rank: int, name: str, points: int, k_d: float, players: int):
        self.rank = rank
        self.name = name
        self.points = points
        self.k_d = k_d
        self.players = players
        self.changes = None

    def get_title(self) -> str:
        msg_emoji = self.emoji['track_clan'] if self.name == TRACKED_CLAN_NAME else EMOJI['all_clans']
        return f"{msg_emoji}          __{self.name}__"

    def get_stats_changes(self):
        """
        Format message to send to Discord.
        """
        data = [self.rank, self.points, self.k_d, self.players]
        if self.changes is not None:
            for i in range(0, 4):
                if self.changes[i] > 0:
                    data[i] = f"{data[i]} {self.emoji['increase']} (+{self.changes[i]})"
                elif self.changes[i] < 0:
                    data[i] = f"{data[i]} {self.emoji['decrease']} ({self.changes[i]})"
        message = f"""
                                        **Місце**: {data[0]}
                                        **Очки**: {data[1]}
                                        **K\\D**: {data[2]}
                                        **Члени**: {data[3]}
                                        """
        return message


class ClansLeaderboardUpdater:
    """
    Class used to update Clans Leaderboard.
    """

    def __init__(self, webhook_url: str, table_name: str, initial: bool = False):
        self.webhook_url = webhook_url
        self.table_name = table_name
        self.initial = initial
        self.embeds = EmbedsBuilder(self.table_name)
        self.process_leaderboard_pages()
        DiscordWebhookNotification(self.webhook_url, self.embeds)

    def process_leaderboard_pages(self):
        """
        Extract links from leaderboard pages.
        """
        rank = 0
        # Get all clan urls from leaderboard pages
        with webdriver.Chrome(executable_path='chromedriver', options=options) as driver:
            driver.set_page_load_timeout(10)
            for leaderboard_page in LB_URLS:
                try:
                    driver.get(leaderboard_page)
                except TimeoutException:
                    driver.execute_script("window.stop();")
                links = driver.find_elements('tag name', "a")
                for link in links:
                    url = link.get_attribute('href')
                    if url[0:45] != 'https://warthunder.com/en/community/claninfo/':
                        continue
                    # Process clan page
                    rank += 1
                    clan = ClanScraper(url, rank).fetch_clan()
                    with ClanDatabase(self.table_name, clan) as clan_db:
                        if not self.initial:
                            clan.changes = clan_db.retrieve_clan_changes()
                        clan_db.update_clan_data()
                        if clan.rank > 30:
                            if clan.name == TRACKED_CLAN_NAME:
                                self.plan_b(clan)
                            continue
                        self.embeds.add_clan_data(clan)

    def plan_b(self, clan: Clan):
        print("init Plan B")
        webhook = DiscordWebhook(url=self.webhook_url)
        webhook.remove_embeds()
        embed = DiscordEmbed(url=CLAN_URL)
        embed.add_embed_field(name=clan.get_title(),
                              value=clan.get_stats_changes())
        webhook.add_embed(embed)
        webhook.execute(remove_embeds=True)


class EmbedsBuilder:
    embed_color = 'ff0000'

    def __init__(self, table_name: str):
        self.table_name = table_name
        self.additional_embed = None
        self.embed = self.set_player_schema() if 'players' in table_name else self.set_clan_schema()

    def set_player_schema(self):

        title = "Активні гравці" if self.table_name == 'players' else "Результати за день"
        self.additional_embed = DiscordEmbed(
            title=title + ' (Продовження)', color=self.embed_color, url=CLAN_URL)
        return DiscordEmbed(
            title=title, color=self.embed_color, url=CLAN_URL)

    def set_clan_schema(self):
        title = "Таблиця лідерів" if self.table_name == 'squadrons' else "Результати за день"
        self.additional_embed = DiscordEmbed(
            title=title + ' (Продовження)', color=self.embed_color, url=LB_URLS[1])
        return DiscordEmbed(
            title=title, color=self.embed_color, url=LB_URLS[0])

    def add_clan_data(self, clan: Clan):
        if 15 < clan.rank < 31:
            self.additional_embed.add_embed_field(name=clan.get_title(),
                                                  value=clan.get_stats_changes())
        else:
            self.embed.add_embed_field(name=clan.get_title(),
                                       value=clan.get_stats_changes())

    def add_player_data(self, active_players: int, player):
        if active_players >= 25:
            self.additional_embed.add_embed_field(name=player.get_title(),
                                                  value=player.get_stats_changes())
        else:
            self.embed.add_embed_field(name=player.get_title(),
                                       value=player.get_stats_changes())


class ClanScraper:
    CSS = {
        'Kill_Ground': "body#bodyRoot div.squadrons-profile__header-stat.squadrons-stat > ul:nth-child(2) > li:nth-child(3)",
        'kill_air': "body#bodyRoot div.squadrons-profile__header-stat.squadrons-stat > ul:nth-child(2) > li:nth-child(2)",
        'death': "body#bodyRoot div.squadrons-profile__header-stat.squadrons-stat > ul:nth-child(2) > li:nth-child(4)",
        'players_count': "div#squadronsInfoRoot div.squadrons-info__content-wrapper > div:nth-child(2)"
    }

    def __init__(self, url: str, rank: int):
        self.url = url
        self.rank = rank
        self.soup = self._get_soup()

    def _get_soup(self) -> BeautifulSoup:
        response = requests.get(self.url, timeout=10)
        response.raise_for_status()
        return BeautifulSoup(response.text, "lxml")

    def _extract_clan_data(self):
        title = self.soup.find(class_="squadrons-info__title").text
        name = str(title.split('[')[1].split(']')[0])[1:-1]
        if len(name) == 0:
            name = title.split()[0][2:-2]
        points = int(self.soup.find(class_="squadrons-counter__value").text)
        killed_air = int(self.soup.select_one(self.CSS['kill_air']).text)
        killed_ground = int(self.soup.select_one(self.CSS['Kill_Ground']).text)
        kills = killed_air + killed_ground
        deaths = int(self.soup.select_one(self.CSS['death']).text)
        players = int(self.soup.select_one(self.CSS['players_count']).text.split()[-1])
        return name, points, kills, deaths, players

    def fetch_clan(self) -> Clan:
        name, points, kills, deaths, players = self._extract_clan_data()
        try:
            k_d = round(float(kills / deaths), 2)
        except ZeroDivisionError:
            k_d = 0.0
        return Clan(self.rank, name, points, k_d, players)


class ClanDatabase(Database):
    clan_tables = "squadrons", "period_squadrons"

    def __init__(self, table_name: str, clan: Clan):
        super().__init__()
        self.table_name = table_name
        self.clan = clan

    def retrieve_clan_changes(self):
        try:
            rank_change = int(self.query(
                f"SELECT rank FROM {self.table_name} WHERE name = '{self.clan.name}'")[0][0]) - self.clan.rank
            points_change = self.clan.points - int(self.query(
                f"SELECT points FROM {self.table_name} WHERE name = '{self.clan.name}'")[0][0])
            old_k_d = float(self.query(
                f"SELECT k_d FROM {self.table_name} WHERE name = '{self.clan.name}'")[0][0])
            k_d_change = round(round(float(self.clan.k_d), 2) - old_k_d, 2)
            players_change = self.clan.players - int(self.query(
                f"SELECT players FROM {self.table_name} WHERE name = '{self.clan.name}'")[0][0])
            return [rank_change, points_change, k_d_change, players_change]
        except IndexError:
            return [0, 0, 0, 0]

    def update_clan_data(self):
        self.execute(f"SELECT * FROM {self.table_name} WHERE name = '{self.clan.name}'")
        if self.fetchone() is None:
            sql_query = f"INSERT INTO {self.table_name} VALUES (?, ?, ?, ?, ?)"
            sql_values = (self.clan.name, self.clan.rank, self.clan.points, self.clan.k_d, self.clan.players)
            self.execute(sql_query, sql_values)
        else:
            sql_query = f'''UPDATE {self.table_name}
                             SET rank = ?,
                                 points = ?,
                                 k_d = ?,
                                 players = ?
                             WHERE name = ?'''
            sql_values = self.clan.rank, self.clan.points, self.clan.k_d, self.clan.players, self.clan.name
            self.execute(sql_query, sql_values)
        self.commit()


class DiscordWebhookNotification:
    def __init__(self, webhook_url: str, embeds: EmbedsBuilder, active_players=25):
        self.active_players = active_players
        self.webhook = DiscordWebhook(url=webhook_url)
        self.webhook.remove_embeds()
        self.embeds = embeds
        self.send_message_to_webhook()

    def send_message_to_webhook(self):
        """
        Send message to Discord webhook.
        """
        if self.active_players >= 1:
            self.webhook.add_embed(self.embeds.embed)
            self.webhook.execute(remove_embeds=True)
        if self.active_players >= 25:
            self.webhook.add_embed(self.embeds.additional_embed)
            self.webhook.execute(remove_embeds=True)


if __name__ == '__main__':
    with Database('squadrons') as test_conn:
        NICKS = ['SOFUA']
        for count, nick in enumerate(NICKS, 15):
            test_conn.execute(
                "UPDATE squadrons SET points = ?, rank =? WHERE name = ?",
                (1200, count, nick))
            test_conn.commit()
    start = time.time()
    ClansLeaderboardUpdater(WEBHOOK_DAY, "squadrons", initial=False)
    print(time.time() - start)
