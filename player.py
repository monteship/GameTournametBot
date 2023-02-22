import sqlite3
import time

import requests
from bs4 import BeautifulSoup
from discord_webhook import DiscordEmbed, DiscordWebhook

import config
from database import create_databases
from squadron import delete_embed


def parsing_players(webhookURL: str, discord_emb: DiscordEmbed, discord_emb_2: DiscordEmbed):
    delete_embed(discord_emb, discord_emb_2)
    webhook = DiscordWebhook(url=webhookURL)
    player_points_change = 0
    players_discord = 0
    page = requests.get(config.CLAN_URL)
    soup = BeautifulSoup(page.text, 'lxml')
    players_count = int(
        str((soup.find(class_='squadrons-info__meta-item').text
             )).split('Number of players: ')[1].replace(' ', ""))
    a_bs = soup.find(class_="squadrons-members__grid-item")
    for _ in range(0, players_count):
        a_bs = a_bs.find_next_sibling().find_next_sibling().find_next_sibling(
        ).find_next_sibling().find_next_sibling().find_next_sibling()
        name = str(str(a_bs.find_next_sibling().text).strip())
        points = int(
            str(a_bs.find_next_sibling().find_next_sibling().text).strip())
        with sqlite3.connect(config.DB_PATH, check_same_thread=False) as data_base:
            sql = data_base.cursor()
            try:
                sql.execute(f"SELECT points FROM players WHERE name = '{name}'")
                player_points_change = points - int(sql.fetchone()[0])
            except:
                None

            try:
                sql.execute(f"DELETE FROM players WHERE name = '{name}'")
                data_base.commit()
            except:
                try:
                    sql.execute("ROLLBACK")
                    data_base.commit()
                except:
                    None
            sql.execute(
                f"INSERT INTO players(name, points) VALUES('{name}', {points})")
            data_base.commit()
            if player_points_change > 0:
                players_discord += 1
                value = f"""
                    **Points**: {points} <:small_green_triangle:996827805725753374> (+{player_points_change})
                    """
                if players_discord >= 25:
                    discord_emb_2.add_embed_field(name=name, value=value)
                else:
                    discord_emb.add_embed_field(name=name, value=value)
            elif player_points_change < 0:
                players_discord += 1
                value = f"""
                    **Points**: {points} 🔻 ({player_points_change})
                    """
                if players_discord >= 25:
                    discord_emb_2.add_embed_field(name=name, value=value)
                else:
                    discord_emb.add_embed_field(name=name, value=value)
    if players_discord >= 1:
        webhook.add_embed(discord_emb)
        webhook.execute(remove_embeds=True)
    if players_discord >= 25:
        webhook.add_embed(discord_emb_2)
        webhook.execute(remove_embeds=True)


if __name__ == '__main__':
    # Used for testing purposes
    create_databases()
    start = time.time()
    parsing_players(config.WEBHOOK_PLAYERS, *config.PLAYERS_EMBED)
    print(str(time.time() - start) + " seconds")
    print('Done')
