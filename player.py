import sqlite3
import time

import requests
from bs4 import BeautifulSoup
from discord_webhook import DiscordEmbed, DiscordWebhook

from config import WEBHOOK_PLAYERS, PLAYERS_EMBED, CLAN_URL, DB_PATH, WEBHOOK_ABANDONED
from database import create_databases
from squadron import delete_embed


def get_player_points_change(sql, name, points):
    """
    Check if a player has changed their points
    :param sql: Sqlite3 connection
    :param name: Name of the player from leaderboard
    :param points: Current points of the player
    :return: None
    """
    try:
        sql.execute(f"SELECT points FROM players WHERE name = '{name}'")
        old_points = int(sql.fetchone()[0])
        return points - old_points
    except TypeError:
        return None


def delete_player(sql, name):
    """
    Try to delete a player from the database
    :param sql: Sqlite3 connection
    :param name: Name of the player from leaderboard
    :return: None
    """
    try:
        sql.execute(f"DELETE FROM players WHERE name = '{name}'")
        return None
    except:
        return None


def insert_player(sql, name, points):
    """
    Insert a player into the database
    :param sql: Sqlite3 connection
    :param name: Name of the player from leaderboard
    :param points: Current points of the player
    :return: None
    """
    try:
        sql.execute(f"INSERT INTO players (name, points) VALUES('{name}', {points})")
        return None
    except:
        return None


def format_message(points, points_change):
    """
    Format the message to be sent based on the points change
    :param points: Current points of the player
    :param points_change: Value of the points change
    :return: Message to be sent or None
    """
    if points_change > 0:
        return f"**Points**: {points} <:small_green_triangle:996827805725753374> (+{points_change})"
    if points_change < 0:
        return f"**Points**: {points} 🔻 ({points_change})"
    return None


def add_player_to_embed(discord_emb, discord_emb_2, name, message, players_discord):
    """
    Applies the given player data changes to the Discord embed
    :param discord_emb: Discord embed for first message
    :param discord_emb_2: Discord embed for second message
    :param name: Player name
    :param message: Message with values
    :param players_discord: Quantity of players with stat changes
    :return: None
    """
    if players_discord >= 25:
        discord_emb_2.add_embed_field(name=name, value=message)
    else:
        discord_emb.add_embed_field(name=name, value=message)


def parsing_players(webhook_url: str, discord_emb: DiscordEmbed, discord_emb_2: DiscordEmbed):
    """
    Parses the players from the leaderboard, check stat changes and adds them to the Discord embed.
    Sends the message to the Discord webhook
    :param webhook_url: Discord webhook url for sending the message to the channel
    :param discord_emb: Discord embed for first message
    :param discord_emb_2: Discord embed for second message
    :return: None
    """
    delete_embed(discord_emb, discord_emb_2)
    personal = []
    webhook = DiscordWebhook(url=webhook_url)
    players_discord = 0
    page = requests.get(CLAN_URL, timeout=50)
    soup = BeautifulSoup(page.text, 'lxml')
    players_count = int(
        str(soup.find(class_='squadrons-info__meta-item').text).split('Number of players: ')[1].replace(' ', ""))
    a_bs = soup.find(class_="squadrons-members__grid-item")
    with sqlite3.connect(DB_PATH) as conn:
        sql = conn.cursor()
        for _ in range(0, players_count):
            a_bs = a_bs.find_next_sibling().find_next_sibling().find_next_sibling().find_next_sibling().find_next_sibling().find_next_sibling()
            name = str(str(a_bs.find_next_sibling().text).strip())
            personal.append(name)
            points = int(str(a_bs.find_next_sibling().find_next_sibling().text).strip())
            player_points_change = get_player_points_change(sql, name, points)
            if player_points_change is not None:
                delete_player(sql, name)
                insert_player(sql, name, points)
                message = format_message(points, player_points_change)
                if message is not None:
                    add_player_to_embed(discord_emb, discord_emb_2, name, message, players_discord)
                    players_discord += 1
        conn.commit()
    if players_discord >= 1:
        webhook.add_embed(discord_emb)
        webhook.execute(remove_embeds=True)
    if players_discord >= 25:
        webhook.add_embed(discord_emb_2)
        webhook.execute(remove_embeds=True)
    is_imposter(personal)


def is_imposter(personal: list):
    """
    Parses the players from the leaderboard, check if they are imposter and adds them to the Discord embed.
    :param personal:
    :return:
    """
    with sqlite3.connect(DB_PATH) as conn:
        sql = conn.cursor()
        sql.execute(f"SELECT name FROM players")
        sql_personal = [person[0] for person in sql.fetchall()]
        imposters = set(sql_personal) - set(personal)
        if imposters:
            for imposter in imposters:
                print(f"Imposter: {imposter}")
                sql.execute(f"SELECT name, points FROM players WHERE name = '{imposter}'")
                imposter_data = sql.fetchall()
                delete_player(sql, imposter)
                conn.commit()
                abandoned_notify(imposter_data[0][0], imposter_data[0][1])


def abandoned_notify(imposter_name, imposter_points):
    webhook = DiscordWebhook(url=WEBHOOK_ABANDONED)
    webhook.add_embed(DiscordEmbed(title=f"Нас покинув {imposter_name} з очками в кількості: {imposter_points}",
                                   color="000000",
                                   url=f"https://warthunder.com/en/community/userinfo/?nick={imposter_name}"))
    webhook.execute(remove_embeds=True)


if __name__ == '__main__':
    create_databases()
    start = time.time()
    parsing_players(WEBHOOK_PLAYERS, *PLAYERS_EMBED)
    print(str(time.time() - start) + " seconds")
    print('Done')
