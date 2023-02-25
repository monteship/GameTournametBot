import time

import requests
from bs4 import BeautifulSoup
from discord_webhook import DiscordWebhook, DiscordEmbed
from selenium import webdriver
from selenium.common import TimeoutException

from config import WEBHOOK_DAY, DAY_START_EMBEDS, DB_PATH, TRACKED_CLAN_NAME, LB_URLS
from player import Database

# Selenium options
options = webdriver.ChromeOptions()
options.add_argument("--headless")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--no-sandbox")
options.add_argument("--disable-logging")

# Constants
CSS_SELECTORS = {
    'SQUAD_NAME':
        "div#squadronsInfoRoot div.squadrons-info__title",
    'POINTS':
        "body#bodyRoot div:nth-child(1) > div.squadrons-counter__value",
    'KILL_G':
        "body#bodyRoot div.squadrons-profile__header-stat.squadrons-stat > ul:nth-child(2) > li:nth-child(3)",
    'KILL_A':
        "body#bodyRoot div.squadrons-profile__header-stat.squadrons-stat > ul:nth-child(2) > li:nth-child(2)",
    'DEATHS':
        "body#bodyRoot div.squadrons-profile__header-stat.squadrons-stat > ul:nth-child(2) > li:nth-child(4)",
    'PLAYERS_COUNT':
        "div#squadronsInfoRoot div.squadrons-info__content-wrapper > div:nth-child(2)"
}


class Clan:
    def __init__(self, rank: int, clan_url: str, table_name: str):
        self.rank = rank
        self.clan_url = clan_url
        self.table_name = table_name
        self.name: str = ''
        self.points: int = 0
        self.k_d: float = 0.0
        self.players_count: int = 0
        self.extract_clan_data()
        self.changes = self.get_squadron_stats_change()
        self.title = None
        self.message = None

    def extract_clan_data(self):
        page = requests.get(self.clan_url, timeout=10)
        soup = BeautifulSoup(page.text, 'lxml')
        name = str(soup.find(class_="squadrons-info__title").text.split('[')[1].split(']')[0])[1:-1]
        if len(name) == 0:
            name = soup.find(class_="squadrons-info__title").text.split()[0][2:-2]
        self.name = name
        self.points = int(soup.find(class_="squadrons-counter__value").text)
        killed_air = int(soup.select_one(CSS_SELECTORS['KILL_A']).text)
        killed_ground = int(soup.select_one(CSS_SELECTORS['KILL_G']).text)
        kills = killed_air + killed_ground
        deaths = int(soup.select_one(CSS_SELECTORS['DEATHS']).text)
        self.k_d = round(float(kills / deaths), 2)
        self.players_count = int(soup.select_one(CSS_SELECTORS['PLAYERS_COUNT']).text[44:])

    def get_squadron_stats_change(self):
        with Database(self.table_name) as conn:
            try:
                query_data = conn.query(
                    f"SELECT rank FROM {self.table_name} WHERE name = '{self.name}'")
                rank_change = self.rank - int(query_data[0][0])
                query_data = conn.query(
                    f"SELECT points FROM {self.table_name} WHERE name = '{self.name}'")
                points_change = self.points - int(query_data[0][0])
                query_data = conn.query(
                    f"SELECT k_d FROM {self.table_name} WHERE name = '{self.name}'")
                old_k_d = float(query_data[0][0])
                k_d_change = round(round(float(self.k_d), 2) - old_k_d, 2)
                query_data = conn.query(
                    f"SELECT players FROM {self.table_name} WHERE name = '{self.name}'")
                players_change = self.players_count - int(query_data[0][0])
                return [rank_change, points_change, k_d_change, players_change]
            except:
                return None

    def format_message(self):

        msg_data = [self.rank, self.points, self.k_d, self.players_count]
        emoji = ':star:' if self.name == TRACKED_CLAN_NAME else ':military_helmet: '
        if self.changes is not None:
            for i in range(0, 4):
                if self.changes[i] > 0:
                    msg_data[i] = \
                        f"{msg_data[i]} <:small_green_triangle:996827805725753374> (+{self.changes[i]})"
                elif self.changes[i] < 0:
                    msg_data[i] = \
                        f"{msg_data[i]} 🔻 (+{self.changes[i]})"
        self.title = f"{emoji}  __{self.name}__"
        self.message = """
                                        **Місце**: {}
                                        **Очки**: {}
                                        **K\\D**: {}
                                        **Члени**: {}
                                        """.format(*msg_data)


class ClansLeaderboardUpdater:
    def __init__(self, webhook_url: str, table_name: str,
                 discord_emb: tuple[DiscordEmbed, DiscordEmbed]):
        self.webhook_url = webhook_url
        self.table_name = table_name
        self.discord_emb = discord_emb
        self.temp_rank = 0
        self.clans_list = []
        self.process_leaderboard_pages()

    def process_leaderboard_pages(self):
        temp_rank = 0
        driver = webdriver.Chrome(
            executable_path='chromedriver', options=options)
        driver.set_page_load_timeout(10)
        for leaderboard_page in LB_URLS:
            try:
                driver.get(leaderboard_page)
            except TimeoutException:
                driver.execute_script("window.stop();")
            time.sleep(5)
            links = driver.find_elements('tag name', "a")
            for link in links:
                temp_url = link.get_attribute('href')
                if temp_url[0:45] == 'https://warthunder.com/en/community/claninfo/':
                    temp_rank += 1
                    self.run_page(temp_rank, temp_url)
        self.send_message_to_webhook()
        driver.close()

    def run_page(self, rank, url):
        clan = Clan(rank, url, 'players')
        with Database(self.table_name) as conn:
            conn.delete_data(clan.name, self.table_name)
            conn.insert_clan(clan, self.table_name)
        if clan.rank < 31:
            clan.format_message()
            self.add_clan_to_embed(clan)

    def add_clan_to_embed(self, clan):
        if 15 < clan.rank < 31:
            self.discord_emb[1].add_embed_field(name=clan.title,
                                                value=clan.message)
        else:
            self.discord_emb[0].add_embed_field(name=clan.title,
                                                value=clan.message)

    def send_message_to_webhook(self):
        webhook = DiscordWebhook(url=self.webhook_url)
        webhook.add_embed(self.discord_emb[0])
        webhook.execute(remove_embeds=True)
        webhook.add_embed(self.discord_emb[1])
        webhook.execute(remove_embeds=True)


if __name__ == '__main__':
    start = time.time()
    ClansLeaderboardUpdater(WEBHOOK_DAY, "squadrons", DAY_START_EMBEDS)
    print(time.time() - start)
