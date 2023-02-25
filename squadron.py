import sqlite3
import time
import timeit

import requests
from bs4 import BeautifulSoup
from discord_webhook import DiscordWebhook, DiscordEmbed
from selenium import webdriver

from config import WEBHOOK_DAY, DAY_START_EMBEDS, DB_PATH, TRACKED_CLAN_NAME, LB_URLS
from player import Database

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

# Selenium options
options = webdriver.ChromeOptions()
options.add_argument("--headless")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--no-sandbox")
options.add_argument("--disable-logging")


def delete_embed(*elements) -> None:
    """
    Delete deprecated embed elements
    :param elements: List of DiscordEmbed elements
    :return: None
    """
    try:
        for element in elements:
            for field in range(0, len(element.get_embed_fields())):
                element.delete_embed_field(field)
        return None
    except IndexError:
        return None


def extract_squadron_data(url) -> dict:
    """
    Get data from squadron page using CSS selectors
    :param url: URL of the squadron page
    :return: Dictionary with squadron data
    """
    page = requests.get(url, timeout=10)
    soup = BeautifulSoup(page.text, 'lxml')
    name = str(soup.find(class_="squadrons-info__title").text.split('[')[1].split(']')[0])
    points = int(soup.find(class_="squadrons-counter__value").text)
    killed_air = int(soup.select_one(CSS_SELECTORS['KILL_A']).text)
    killed_ground = int(soup.select_one(CSS_SELECTORS['KILL_G']).text)
    kills = killed_air + killed_ground
    deaths = int(soup.select_one(CSS_SELECTORS['DEATHS']).text)
    k_d = round(float(kills / deaths), 2)
    players_count = int(soup.select_one(CSS_SELECTORS['PLAYERS_COUNT']).text[44:])
    return {'name': name, 'points': points, 'k_d': k_d, 'players_count': players_count}


def extract_squadron_data_2(url) -> dict:
    pass


def get_squadron_stats_change(sql, table_name: str, squadron_data: dict):
    """
    Try to get squadron stats change and return list of changes
    :param sql: Sqlite3 connection
    :param table_name: Table name
    :param squadron_data: Squadron stats
    :return: List with changes
    """
    try:
        sql.execute(f"SELECT rank FROM {table_name} WHERE name = '{squadron_data['name']}'")
        rank_place_change = squadron_data['rank_place'] - int(sql.fetchone()[0])
        sql.execute(f"SELECT points FROM {table_name} WHERE name = '{squadron_data['name']}'")
        points_change = squadron_data['points'] - int(sql.fetchone()[0])
        sql.execute(f"SELECT k_d FROM {table_name} WHERE name = '{squadron_data['name']}'")
        old_k_d = float(sql.fetchone()[0])
        k_d_change = round(round(float(squadron_data['k_d']), 2) - old_k_d, 2)
        sql.execute(f"SELECT players FROM {table_name} WHERE name = '{squadron_data['name']}'")
        players_count_change = squadron_data['players_count'] - int(sql.fetchone()[0])
        return [rank_place_change, points_change, k_d_change, players_count_change]
    except TypeError:
        return None


def delete_squadron_data(sql, table_name: str, squadron_data: dict) -> None:
    """
    Delete squadron data from database
    :param sql: Sqlite3 connection
    :param table_name: Table name
    :param squadron_data: Squadron stats
    :return:
    """
    try:
        sql.execute(f"DELETE FROM {table_name} WHERE name = '{squadron_data['name']}'")
        return None
    except ValueError:
        return None


def insert_squadron_data(sql, table_name: str, squadron_data: dict):
    """
    Insert squadron data to database
    :param sql: Sqlite3 connection
    :param table_name: Table name
    :param squadron_data: Squadron stats
    :return: None
    """
    try:
        sql.execute(
            f"INSERT INTO {table_name} (name, rank, points, k_d, players) "
            "VALUES('{name}', {rank_place}, {points}, {k_d}, {players_count})".format(
                **squadron_data))
        return None
    except ValueError:
        return None


def format_message(squadron_data: dict, squadron_changes: list):
    """
    Used to format message based on squadron stat changes
    :param squadron_data: Squadron stats
    :param squadron_changes: Squadron stats changes
    :return: title: message:
    """
    test_name = squadron_data['name']
    data = list(squadron_data.values())
    emoji = ':star:' if squadron_data['name'] == TRACKED_CLAN_NAME else ':military_helmet: '
    if squadron_changes is not None:
        for i in range(0, 4):
            if squadron_changes[i] > 0:
                data[i] = f"{data[i]} <:small_green_triangle:996827805725753374> (+{squadron_changes[i]})"
            elif squadron_changes[i] < 0:
                data[i] = f"{data[i]} 🔻 ({squadron_changes[i]})"
    title = f"{emoji} {str(data[-1])}. __{squadron_data['name'][1:-1]}__"
    message = """
                                        **Очки**: {}
                                        **K\\D**: {}
                                        **Члени**: {}
                                        """.format(*data[1:-1])
    return title, message


def add_squadron_to_embed(discord_emb, discord_emb_2, title, message, squadron_data: dict):
    """
    Adds a new message to DiscordEmbed
    :param discord_emb: Discord embed for first message
    :param discord_emb_2: Discord embed for second message
    :param title: Title for new message
    :param message: Message for new message
    :param squadron_data: Squadron stats
    :return: None
    """
    if 15 < squadron_data['rank_place'] < 31:
        discord_emb_2.add_embed_field(name=title, value=message)
    else:
        discord_emb.add_embed_field(name=title, value=message)


def parsing_squadrons(webhook_url: str, table_name: str,
                      discord_emb: DiscordEmbed, discord_emb_2: DiscordEmbed):
    """
    Parses the squadrons from the leaderboard, check stat changes and adds them to the Discord embed.
    Sends the message to the Discord webhook
    :param webhook_url: Discord webhook URL
    :param table_name: Table name
    :param discord_emb: Discord embed for first message
    :param discord_emb_2: Discord embed for second message
    :return:
    """
    delete_embed(discord_emb, discord_emb_2)
    webhook = DiscordWebhook(url=webhook_url)
    discord_emb.set_timestamp()
    rank_place = 0
    with webdriver.Chrome(executable_path='chromedriver', options=options) as driver:
        for leaderboard_page in LB_URLS:
            driver.get(leaderboard_page)
            time.sleep(5)
            links = driver.find_elements('tag name', "a")
            for link in links:
                clan_url = link.get_attribute('href')
                if clan_url[0:45] == 'https://warthunder.com/en/community/claninfo/':
                    rank_place += 1
                    squadron_data = extract_squadron_data(clan_url)
                    squadron_data['rank_place'] = rank_place
                    with sqlite3.connect(DB_PATH) as conn:
                        sql = conn.cursor()
                        squadron_changes = get_squadron_stats_change(sql, table_name, squadron_data)
                        if squadron_changes is not None:
                            delete_squadron_data(sql, table_name, squadron_data)
                        insert_squadron_data(sql, table_name, squadron_data)
                        if squadron_data['rank_place'] < 31:
                            title, message = format_message(squadron_data, squadron_changes)
                            add_squadron_to_embed(discord_emb, discord_emb_2, title, message, squadron_data)
                        conn.commit()
    webhook.add_embed(discord_emb)
    webhook.execute(remove_embeds=True)
    webhook.add_embed(discord_emb_2)
    webhook.execute(remove_embeds=True)


if __name__ == '__main__':
    start = time.time()
    parsing_squadrons(WEBHOOK_DAY, "period_squadrons", *DAY_START_EMBEDS)
    print(time.time() - start)
