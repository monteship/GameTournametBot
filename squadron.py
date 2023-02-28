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
                    clan = ClanScraper(url, rank).fetch_clan_data()
                    with ClanDatabase(self.table_name, clan) as clan_db:
                        if not self.initial:
                            clan.changes = clan_db.retrieve_clan_changes()
                        clan_db.update_clan_data()
                        if clan.rank > 30:
                            return
                        message, title = clan.format_message()
                        self.embeds.add_clan_data(clan, title, message)
        DiscordWebhookNotification(self.webhook_url, self.embeds)


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

    def format_message(self):
        """
        Format message to send to Discord.
        """
        data = [self.rank, self.points, self.k_d, self.players]
        emoji = self.emoji['track_clan'] if self.name == TRACKED_CLAN_NAME else EMOJI['all_clans']
        if self.changes is not None:
            for i in range(0, 4):
                if self.changes[i] > 0:
                    data[i] = f"{data[i]} {self.emoji['increase']} (+{self.changes[i]})"
                elif self.changes[i] < 0:
                    data[i] = f"{data[i]} {self.emoji['decrease']} ({self.changes[i]})"
        title = f"{emoji}          __{self.name}__"
        message = f"""
                                        **Місце**: {data[0]}
                                        **Очки**: {data[1]}
                                        **K\\D**: {data[2]}
                                        **Члени**: {data[3]}
                                        """
        return message, title


class EmbedsBuilder:
    def __init__(self, table_name: str, option=False):
        self.option = option
        self.table_name = table_name
        self.additional_embed = None
        self.embed = self.set_schema()

    def set_schema(self):
        embed_color = 'ff0000'
        if not self.option:
            title = "Таблиця лідерів" if self.table_name == 'squadrons' else "Результати за день"
            self.additional_embed = DiscordEmbed(
                title=title + ' (Продовження)', color=embed_color, url=LB_URLS[1])
            return DiscordEmbed(
                title=title, color=embed_color, url=LB_URLS[0])
        else:
            title = "Активні гравці" if self.table_name == 'players' else "Результати за день"
            self.additional_embed = DiscordEmbed(
                title=title + ' (Продовження)', color=embed_color, url=CLAN_URL)
            return DiscordEmbed(
                title=title, color=embed_color, url=CLAN_URL)

    def add_clan_data(self, clan: Clan, title: str, message: str):
        if 15 < clan.rank < 31:
            self.additional_embed.add_embed_field(name=title,
                                                  value=message)
        else:
            self.embed.add_embed_field(name=title,
                                       value=message)

    def add_player_data(self, active_players: int, title: str, message: str):
        if active_players >= 25:
            self.additional_embed.add_embed_field(name=title,
                                                  value=message)
        else:
            self.embed.add_embed_field(name=title,
                                       value=message)


class ClanScraper:
    CSS = {
        'KILL_G':
            "body#bodyRoot div.squadrons-profile__header-stat.squadrons-stat > ul:nth-child(2) > li:nth-child(3)",
        'KILL_A':
            "body#bodyRoot div.squadrons-profile__header-stat.squadrons-stat > ul:nth-child(2) > li:nth-child(2)",
        'DEATHS':
            "body#bodyRoot div.squadrons-profile__header-stat.squadrons-stat > ul:nth-child(2) > li:nth-child(4)",
        'PLAYERS_COUNT':
            "div#squadronsInfoRoot div.squadrons-info__content-wrapper > div:nth-child(2)"
    }

    def __init__(self, url: str, rank: int):
        self.url = url
        self.rank = rank
        self.soup = BeautifulSoup(
            requests.get(url, timeout=10).text, "lxml")

    def fetch_clan_data(self) -> Clan:
        name = str(self.soup.find(
            class_="squadrons-info__title").text.split('[')[1].split(']')[0])[1:-1]
        if len(name) == 0:
            name = self.soup.find(class_="squadrons-info__title").text.split()[0][2:-2]
        points = int(self.soup.find(class_="squadrons-counter__value").text)
        killed_air = int(self.soup.select_one(self.CSS['KILL_A']).text)
        killed_ground = int(self.soup.select_one(self.CSS['KILL_G']).text)
        kills = killed_air + killed_ground
        deaths = int(self.soup.select_one(self.CSS['DEATHS']).text)
        k_d = round(float(kills / deaths), 2)
        players = int(self.soup.select_one(self.CSS['PLAYERS_COUNT']).text[44:])
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
            return None

    def update_clan_data(self):
        self.execute(f"SELECT * FROM {self.table_name} WHERE name = '{self.clan.name}'")
        if self.fetchone() is None:
            print('New clan')
            sql_query = f"INSERT INTO {self.table_name} VALUES (?, ?, ?, ?, ?)"
            sql_values = (self.clan.name, self.clan.rank, self.clan.points, self.clan.k_d, self.clan.players)
            self.execute(sql_query, sql_values)
        else:
            print('Update clan')

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
    def __init__(self, webhook_url: str, embeds: EmbedsBuilder, active_players=None):
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
