import sqlite3
import time

import requests
from bs4 import BeautifulSoup
from discord_webhook import DiscordWebhook, DiscordEmbed
from selenium import webdriver

import config
from database import create_databases

# Selenium options
options = webdriver.ChromeOptions()
options.add_argument("--headless")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--no-sandbox")
options.add_argument("--disable-logging")


def delete_embed(*elements) -> None:
    """Delete deprecated embed elements"""
    for element in elements:
        for field in range(0, len(element.get_embed_fields())):
            element.delete_embed_field(field)


def get_leaderboard_group(url) -> int:
    """
    Get the group of the leaderboard
    by comparing the url of the page with the url of the leaderboard
    return the group of the leaderboard
    """
    top = 0
    if url == 'https://warthunder.com/en/community/clansleaderboard/page/2/?type=hist&sort=ftime':
        top += 20
    elif url == 'https://warthunder.com/en/community/clansleaderboard/page/3/?type=hist&sort=ftime':
        top += 40
    return top


def extract_squadron_data(url) -> dict:
    """
    Extract the squadron data from the url
    using CSS Selector.
    """
    page = requests.get(url, timeout=10)
    soup = BeautifulSoup(page.text, 'lxml')
    full_name = soup.select_one(config.CSS_SQUAD_NAME).text[25:]
    name = str(full_name.split(' ')[0])[1:-1]
    points = int(soup.select_one(config.CSS_POINTS).text)
    kills = int(soup.select_one(config.CSS_KILLED_GROUND).text) + int(soup.select_one(config.CSS_KILLED_AIR).text)
    deaths = int(soup.select_one(config.CSS_DEATHS).text)
    k_d = round(float(kills / deaths), 2)
    players_count = int(soup.select_one(config.CSS_PLAYERS_COUNT).text[44:])
    return {'name': name, 'points': points, 'kills': kills, 'deaths': deaths, 'k_d': k_d,
            'players_count': players_count}


def get_squadrons_stat_update(table_name: str, rank_place: int, squadron_data: dict) -> list:
    """
    Get/write squadron stat changes.
    Returns a list of stat changes.
    """
    rank_place_change, points_change, kills_change, deaths_change, k_d_change, players_count_change = 0, 0, 0, 0, 0.00, 0
    with sqlite3.connect(config.DB_PATH, check_same_thread=False) as data_base:
        sql = data_base.cursor()
        try:
            sql.execute(f"SELECT rank FROM {table_name} WHERE name = '{squadron_data['name']}'")
            rank_place_change = rank_place - int(sql.fetchone()[0])
            sql.execute(f"SELECT points FROM {table_name} WHERE name = '{squadron_data['name']}'")
            points_change = squadron_data['points'] - int(sql.fetchone()[0])
            sql.execute(f"SELECT kills FROM {table_name} WHERE name = '{squadron_data['name']}'")
            old_kills = int(sql.fetchone()[0])
            kills_change = squadron_data['kills'] - sql.fetchone()[0]
            sql.execute(f"SELECT deaths FROM {table_name} WHERE name = '{squadron_data['name']}'")
            old_deaths = int(sql.fetchone()[0])
            deaths_change = squadron_data['deaths'] - old_deaths
            k_d_change = round(float(squadron_data['k_d']), 2) - (old_kills / old_deaths)
            sql.execute(f"SELECT players FROM {table_name} WHERE name = '{squadron_data['name']}'")
            players_count_change = squadron_data['players_count'] - int(sql.fetchone()[0])
            print(rank_place_change, points_change, kills_change, deaths_change, k_d_change, players_count_change)
        except:
            None
        try:
            sql.execute(f"DELETE FROM {table_name} WHERE name = '{squadron_data['name']}'")
            data_base.commit()
        except:
            None
            try:
                sql.execute("ROLLBACK")
                data_base.commit()
            except:
                None
        sql.execute(
            f"INSERT INTO {table_name} (name, rank, points, kills, deaths, players) "
            "VALUES('{name}', {rank_place}, {points}, {kills}, {deaths}, {players_count})".format(
                **squadron_data))
        data_base.commit()
    return [rank_place_change, points_change, kills_change, deaths_change,
            k_d_change, players_count_change]


def changes_notification(squadron_data: dict, changes: list,
                         discord_emb: DiscordEmbed, discord_emb_2: DiscordEmbed):
    """ Creates a notification about changes on a leaderboard
    """
    data = list(squadron_data.values())
    rank, name = squadron_data['rank_place'], squadron_data['name']
    emoji = ':star:' if name == config.TRACKED_CLAN_NAME else ':military_helmet: '
    for i in range(0, 5):
        if changes[i] > 0:
            data[i] = f"{data[i]} <:small_green_triangle:996827805725753374> (+{changes[i]})"
        elif changes[i] < 0:
            data[i] = f"{data[i]} 🔻 ({changes[i]})"
    if rank <= 15:
        discord_emb.add_embed_field(name=f"{emoji}{str(data[-1]).ljust(10)} {name}",
                                    value="""
                                        **Points**: {}
                                        **Kills**: {}
                                        **Deaths**: {}
                                        **K\\D**: {}
                                        **Members**: {}
                                        """.format(*data[1:-1]))
    if 15 < rank < 31:
        discord_emb_2.add_embed_field(name=f"{emoji}{str(data[-1]).ljust(10)} {name}",
                                      value="""
                                        **Points**: {}
                                        **Kills**: {}
                                        **Deaths**: {}
                                        **K\\D**: {}
                                        **Members**: {}
                                        """.format(*data[1:-1]))

    return discord_emb, discord_emb_2


def parsing_squadrons(webhook_url: str, table_name: str,
                      discord_emb: DiscordEmbed, discord_emb_2: DiscordEmbed):
    """
    Parses the squadrons table and sends it to the Discord webhook.
    """
    delete_embed(discord_emb, discord_emb_2)
    webhook = DiscordWebhook(url=webhook_url)
    discord_emb.set_timestamp()
    rank_place = 0
    with webdriver.Chrome(executable_path='chromedriver', options=options) as driver:
        for leaderboard_page in config.LB_URLS:
            driver.get(leaderboard_page)
            time.sleep(5)
            links = driver.find_elements('tag name', "a")
            for link in links:
                clan_url = link.get_attribute('href')
                if clan_url[0:45] == 'https://warthunder.com/en/community/claninfo/':
                    rank_place += 1
                    squadron_data = extract_squadron_data(clan_url)
                    squadron_data['rank_place'] = rank_place
                    changes = get_squadrons_stat_update(table_name, rank_place, squadron_data)
                    discord_emb, discord_emb_2 = changes_notification(squadron_data, changes, discord_emb,
                                                                      discord_emb_2)
    webhook.add_embed(discord_emb)
    webhook.execute(remove_embeds=True)
    webhook.add_embed(discord_emb_2)
    webhook.execute(remove_embeds=True)


if __name__ == '__main__':
    create_databases()
    print("Database created")
    parsing_squadrons(config.WEBHOOK_DAY, "period_squadrons", *config.DAY_START_EMBEDS)
    print('Done')
