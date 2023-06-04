import logging
import sqlite3

from .items import PlayerItem, ClanItem
from .settings import EMOJI, CLAN_LEADERS, CLAN_URL, WEBHOOK_PLAYERS, WEBHOOK_DAY, TRACKED_CLANS

from discord_webhook import DiscordWebhook, DiscordEmbed


class WtStatsScraperPipeline:
    def __init__(self):
        self.con = sqlite3.connect("wtstats.sqlite")
        self.cur = self.con.cursor()
        self.table = None
        self.create_tables()
        self.changes = dict()
        self.player_iter = 0
        self.members = []

    def process_item(self, item, spider):
        if not self.table:
            self.table = spider.table_name

        if isinstance(item, PlayerItem):
            self.members.append(item['nick'])
            self.update_players(item)

        if isinstance(item, ClanItem):
            self.update_squadrons(item)
        return item

    def update_players(self, item):
        self.cur.execute(
            f"SELECT nick, rating, activity FROM {self.table} WHERE nick = ?",
            (item['nick'],))
        result = self.cur.fetchone()
        if not result:
            self.cur.execute(
                f"INSERT INTO {self.table} VALUES (?, ?, ?, ?, ?)",
                (item['nick'], item['rating'], item['activity'], item['role'], item['date_joined']))
        else:
            self.cur.execute(
                f"UPDATE {self.table} SET rating = ?, activity = ?, role = ?, date_joined = ? WHERE nick = ?",
                (item['rating'], item['activity'], item['role'], item['date_joined'], item['nick']))
            if int(result[1]) != int(item['rating']):
                self.make_player_message(result, item)
        self.con.commit()

    def make_player_message(self, old_data, item):
        title = f"{EMOJI['track_clan']} {item['nick']}" if item['nick'] in CLAN_LEADERS else f"__{item['nick']}__"
        change = int(item['rating']) - old_data[1]
        emoji = EMOJI['increase'] if change > 0 else EMOJI['decrease']
        message = f"Очки: {item['rating']} {emoji} ``({change})``"
        self.changes[self.player_iter] = (title, message)

    def check_leavers(self):
        self.cur.execute("SELECT nick FROM players_instant")
        database_members = self.cur.fetchall()
        logging.info(f"Database members: {database_members}")

    def update_squadrons(self, item):
        self.cur.execute(
            f"SELECT rank, members, rating, kills_to_death FROM {self.table} WHERE tag = ?",
            (item['tag'],))
        result = self.cur.fetchone()
        if not result:
            self.cur.execute(
                f"INSERT INTO {self.table} VALUES (?, ?, ?, ?, ?, ?)",
                (item['tag'], item['name'], item['rank'], item['members'], item['rating'], item['kills_to_death']))
        else:
            self.cur.execute(
                f"UPDATE {self.table} SET name = ?, rank = ?, members = ?, rating = ?, kills_to_death = ? WHERE tag = ?",
                (item['name'], item['rank'], item['members'], item['rating'], item['kills_to_death'], item['tag']))
            self.make_squad_message(result, item)
        self.con.commit()

    def make_squad_message(self, old_data, item):
        msg_emoji = EMOJI['track_clan'] if item['name'] in TRACKED_CLANS else EMOJI['all_clans']
        title = f"{msg_emoji}          __{item['name']}__"
        changes = dict(
            rank=item['rank'] - old_data[0],
            members=item['rank'] - old_data[1],
            rating=item['rank'] - old_data[2],
            kills_to_death=round((item['rank'] - old_data[3]), 2)
        )
        for key, change in changes.items():
            for i in range(0, 4):
                if change > 0:
                    changes[key] = f"{item[key]} {EMOJI['increase']} (+{change})"
                elif change < 0:
                    changes[key] = f"{item[key]} {EMOJI['decrease']} ({change})"
        message = f"""
            **Місце**: {item['rank']}
            **Очки**: {item['rating']}
            **K\\D**: {item['kills_to_death']}
            **Члени**: {item['members']}
        """
        self.changes[item['rank']] = (title, message)

    def close_spider(self, spider):
        self.con.commit()
        self.check_leavers()
        self.con.close()
        self.send_changes()

    def send_changes(self):
        if 'players' in self.table:
            items_per_message = 26
            stop_item_count = 200
            embed_url = CLAN_URL
            webhook_url = WEBHOOK_PLAYERS if self.table == 'players_instant' else WEBHOOK_DAY
            announce = "Активні гравці" if self.table == 'players_instant' else "Результати за день"
        else:
            items_per_message = 9
            stop_item_count = 18
            embed_url = 'https://warthunder.com/en/community/clansleaderboard/'
            webhook_url = WEBHOOK_PLAYERS if self.table == 'squadrons_instant' else WEBHOOK_DAY
            announce = "Таблиця лідерів" if self.table == 'squadrons_instant' else "Результати за день"
        embed = DiscordEmbed(title=announce, color='ff0000', url=embed_url)
        additional_embed = DiscordEmbed(color='ff0000', url=embed_url)
        for i, (title, changes) in self.changes.items():
            if i >= stop_item_count:
                break
            if i >= items_per_message:
                additional_embed.add_embed_field(
                    name=title,
                    value=changes
                )
            else:
                embed.add_embed_field(
                    name=title,
                    value=changes
                )
        webhook = DiscordWebhook(url=webhook_url)
        if self.changes:
            webhook.add_embed(embed)
            webhook.execute(remove_embeds=True)
        if len(self.changes) > items_per_message:
            webhook.add_embed(additional_embed)
            webhook.execute(remove_embeds=True)

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
