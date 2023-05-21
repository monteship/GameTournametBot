import logging
import sqlite3

from .items import PlayerItem, ClanItem
from .settings import EMOJI, CLAN_LEADERS, CLAN_URL, WEBHOOK_PLAYERS, WEBHOOK_DAY

from discord_webhook import DiscordWebhook, DiscordEmbed


class WtStatsScraperPipeline:
    def __init__(self):
        self.con = sqlite3.connect("wtstats.sqlite")
        self.cur = self.con.cursor()
        self.table_name = None
        self.create_tables()
        self.changes = dict()
        self.members = []

    def process_item(self, item, spider):
        if not self.table_name:
            self.table_name = spider.table_name
        if isinstance(item, PlayerItem):
            self.members.append(item['nick'])
            self.update_players(item)
        if isinstance(item, ClanItem):
            self.update_squadrons(item)
        return item

    def update_players(self, item):
        self.cur.execute(
            f"SELECT nick, rating, activity FROM {self.table_name} WHERE nick = ?",
            (item['nick'],))
        result = self.cur.fetchone()
        if not result:
            self.cur.execute(
                f"INSERT INTO {self.table_name} VALUES (?, ?, ?, ?, ?)",
                (item['nick'], item['rating'], item['activity'], item['role'], item['date_joined']))
        else:
            self.cur.execute(
                f"UPDATE {self.table_name} SET rating = ?, activity = ?, role = ?, date_joined = ? WHERE nick = ?",
                (item['rating'], item['activity'], item['role'], item['date_joined'], item['nick']))
            if int(result[1]) != int(item['rating']):
                self.make_player_message(result[0], int(result[1]), int(item['rating']))
            ## todo: add activity chack for rating inactive players
        self.con.commit()

    def make_player_message(self, nick, old_rating, new_rating):
        title = f"{EMOJI['track_clan']} {nick}" if nick in CLAN_LEADERS else f"__{nick}__"
        change = new_rating - old_rating
        emoji = EMOJI['increase'] if change > 0 else EMOJI['decrease']
        message = f"Очки: {new_rating} {emoji} ``({change})``"
        self.changes[title] = message

    def send_changes(self):
        announce = "Активні гравці" if self.table_name == 'players_instant' else "Результати за день"
        embed = DiscordEmbed(title=announce, color='ff0000', url=CLAN_URL)
        additional_embed = DiscordEmbed(color='ff0000', url=CLAN_URL)
        for i, (title, changes) in enumerate(self.changes.items()):
            if i >= 25:
                additional_embed.add_embed_field(name=title, value=changes)
            else:
                embed.add_embed_field(name=title, value=changes)
        webhook = DiscordWebhook(url=WEBHOOK_PLAYERS if self.table_name == 'players_instant' else WEBHOOK_DAY)
        if self.changes:
            webhook.add_embed(embed)
            webhook.execute(remove_embeds=True)
        if len(self.changes) > 25:
            webhook.add_embed(additional_embed)
            webhook.execute(remove_embeds=True)

    def check_leavers(self):
        self.cur.execute("SELECT nick FROM players_instant")
        database_members = self.cur.fetchall()
        logging.info(f"Database members: {database_members}")

    def update_squadrons(self, item):
        pass

    def close_spider(self, spider):
        self.con.commit()
        self.check_leavers()
        self.con.close()
        self.send_changes()

    def create_tables(self):
        for table_name in ['players_daily', 'players_instant']:
            self.cur.execute(
                f'''CREATE TABLE IF NOT EXISTS {table_name} 
                    ("nick" TEXT, "rating" INTEGER, "activity" INTEGER, "role" TEXT, "date_joined" DATE)
                ''')
        for table_name in ['squadrons_daily', 'squadrons_instant']:
            self.cur.execute(
                f'''CREATE TABLE IF NOT EXISTS {table_name} 
                ("tag" TEXT, "rank" INTEGER, "name" TEXT, "members" INTEGER, "rating" INTEGER, "kills_to_death" INTEGER)
                ''')
        self.con.commit()
