import sqlite3
import time
import datetime

import requests
from bs4 import BeautifulSoup
from discord_webhook import DiscordEmbed, DiscordWebhook

from config import WEBHOOK_PLAYERS, PLAYERS_EMBED, CLAN_URL, DB_PATH, WEBHOOK_ABANDONED
from database import create_databases
from squadron import delete_embed


def extract_player_data(element, iteration: int):
    """
    Iterates through the elements and extracts the player data.
    :param element:
    :param iteration:
    :return:
    """
    iteration_range = 11 if iteration == 0 else 6
    iteration_range_2 = [6, 7, 9, 10] if iteration == 0 else [1, 2, 4, 5]
    player_data = {}
    for i in range(iteration_range):
        element = element.find_next_sibling()
        if i == iteration_range_2[0]:
            player_data['name'] = element.text.strip()
        if i == iteration_range_2[1]:
            player_data['points'] = int(element.text.strip())
        if i == iteration_range_2[2]:
            player_data['role'] = str(element.text.strip())
        if i == iteration_range_2[3]:
            player_data['date_join'] = datetime.datetime.strptime(
                element.text.strip(), '%d.%m.%Y').date()
            return player_data, element


def get_player_points_change(sql, table_name: str, player_data: dict):
    """
    Check if a player has changed their points
    :param sql: Sqlite3 connection
    :param table_name:
    :param player_data:
    :return: None
    """
    changes = {'points': None,
               'rank': None}
    rank = 0
    try:
        sql.execute(f"SELECT points, rank FROM {table_name} WHERE name = '{player_data['name']}'")
        data = sql.fetchall()
        changes['points'] = data[0][0] - player_data['points']
        rank = data[0][1]
    except IndexError:
        try:
            sql.execute(f"SELECT points FROM {table_name} WHERE name = '{player_data['name']}'")
            data = sql.fetchone()
            changes['points'] = data[0] - player_data['points']
        except TypeError:
            pass
    delete_player(sql, table_name, player_data)
    player_data = insert_player(sql, table_name, player_data, rank)
    return changes, player_data


def delete_player(sql, table_name, player_data: dict):
    """
    Try to delete a player from the database
    :param sql:
    :param player_data:
    :param table_name:
    :return: None
    """
    try:
        sql.execute(f"DELETE FROM {table_name} WHERE name = '{player_data['name']}'")
    except:
        pass


def insert_player(sql, table_name: str, player_data: dict, rank: int):
    """
    Insert a player into the database
    :param rank:
    :param sql:
    :param table_name:
    :param player_data:
    :return: None
    """
    player_data['rank'] = rank
    try:
        sql.execute(f"INSERT INTO {table_name} (name, points, role, date_join, rank) VALUES (?, ?, ?, ?, ?)",
                    list(player_data.values()))
    except ValueError:
        pass
    return player_data


def format_message(player_data: dict, player_changes: dict):
    """
    Format the message to be sent based on the points change
    :return: Message to be sent or None
    """
    message = None
    emoji = ['<:small_green_triangle:996827805725753374>',
             '🔻']
    if player_changes['points'] > 0:
        message = f"**Points**: {player_data['points']} {emoji[0]} (+{player_changes['points']})"
    if player_changes['points'] < 0:
        message = f"**Points**: {player_data['points']} {emoji[1]} ({player_changes['points']})"
    return message


def add_player_to_embed(discord_emb, discord_emb_2, player_data, message, players_discord):
    """
    Applies the given player data changes to the Discord embed
    :param player_data:
    :param discord_emb: Discord embed for first message
    :param discord_emb_2: Discord embed for second message
    :param message: Message with values
    :param players_discord: Quantity of players with stat changes
    :return: None
    """
    if player_data['rank']:
        stencil = f"Місце {player_data['rank']} в полку\n{player_data['name']}"
    else:
        stencil = f"{player_data['name']}"
    if players_discord >= 25:
        discord_emb_2.add_embed_field(name=stencil, value=message)
    discord_emb.add_embed_field(name=stencil, value=message)


def parsing_players(webhook_url: str, table_name: str, discord_emb: DiscordEmbed, discord_emb_2: DiscordEmbed):
    """
    Parses the players from the leaderboard, check stat changes and adds them to the Discord embed.
    Sends the message to the Discord webhook
    :param webhook_url: Discord webhook url for sending the message to the channel
    :param table_name:
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
    players_count = int(str(soup.find(class_='squadrons-info__meta-item').text).split()[-1])
    element = soup.find(class_="squadrons-members__grid-item")
    with sqlite3.connect(DB_PATH) as conn:
        sql = conn.cursor()
        for iteration in range(0, players_count):
            player_data, element = extract_player_data(element, iteration)
            personal.append(player_data['name'])
            player_changes, player_data = get_player_points_change(sql, table_name, player_data)
            if player_changes['points'] is not None:
                message = format_message(player_data, player_changes)
                if message is not None:
                    add_player_to_embed(discord_emb, discord_emb_2,
                                        player_data, message, players_discord)
                    players_discord += 1
        conn.commit()
    if players_discord >= 1:
        webhook.add_embed(discord_emb)
        webhook.execute(remove_embeds=True)
    if players_discord >= 25:
        webhook.add_embed(discord_emb_2)
        webhook.execute(remove_embeds=True)
    after_run(personal, table_name)


def after_run(personal: list, table_name: str):
    with sqlite3.connect(DB_PATH) as conn:
        sql = conn.cursor()
        set_ranks(sql, table_name)
        person_is_quit(sql, personal)
        conn.commit()


def set_ranks(sql, table_name):
    """
    :param sql:
    :param table_name:
    :return:
    """
    sql.execute(f"""UPDATE {table_name}
                    SET rank = (
                        SELECT COUNT(*) + 1
                        FROM players p2
                        WHERE p2.points > {table_name}.points
                    )
                    WHERE {table_name}.points IS NOT NULL;""")


def person_is_quit(sql, personal: list):
    """
    Parses the players from the leaderboard,
    check if they are imposter and adds them to the Discord embed
    :param sql:
    :param personal:
    :return:
    """
    sql.execute(f"SELECT name FROM players")
    sql_personal = [person[0] for person in sql.fetchall()]
    quit_persons = set(sql_personal) - set(personal)
    if quit_persons:
        for quit_person in quit_persons:
            table_name = 'players', 'period_players'
            name, points, date = None, None, None
            try:
                sql.execute(f"SELECT name, points, date_join FROM players WHERE name = '{quit_person}'")
                name, points, date = sql.fetchall()[0]
                for table in table_name:
                    delete_player(sql, table, quit_person)
            except:
                pass
            quitter_notify(name, points, date)


def quitter_notify(name, points, date):
    summary = datetime.datetime.today().date() - datetime.datetime.strptime(date, '%d-%m-%Y').date()
    webhook = DiscordWebhook(url=WEBHOOK_ABANDONED)
    webhook.add_embed(DiscordEmbed(
        title=f"**{name}**",
        description=f" \n Покинув нас з очками в кількості: **{points}** \n"
                    f"Пробув з нами **{str(summary.days)}** дня/днів",
        color="000000",
        url=f"https://warthunder.com/en/community/userinfo/?nick={name}"))
    webhook.execute(remove_embeds=True)


if __name__ == '__main__':
    create_databases()
    start = time.time()
    parsing_players(WEBHOOK_PLAYERS, 'players', *PLAYERS_EMBED)
    print(str(time.time() - start) + " seconds")
    print('Done')
