import sqlite3

from .items import PlayerItem, ClanItem
from .settings import EMOJI, CLAN_LEADERS


class WtStatsScraperPipeline:
    def __init__(self):
        self.con = sqlite3.connect("wtstats.sqlite")
        self.cur = self.con.cursor()
        self.create_tables()
        self.changes = {}
        self.members = []

    def process_item(self, item, spider):
        if isinstance(item, PlayerItem):
            self.members.append(item['nick'])
            self.update_players(item, spider.table)
        if isinstance(item, ClanItem):
            self.update_squadrons(item)
        return item

    def update_players(self, item, table_name):
        self.cur.execute(
            f"SELECT nick, rating, activity FROM {table_name} WHERE nick = ?",
            (item['nick'],))
        result = self.cur.fetchone()
        if not result:
            self.cur.execute(
                f"INSERT INTO {table_name} VALUES (?, ?, ?, ?, ?)",
                (item['nick'], item['rating'], item['activity'], item['role'], item['date_joined']))
        else:
            self.cur.execute(
                f"UPDATE {table_name} SET rating = ?, activity = ?, role = ?, date_joined = ? WHERE nick = ?",
                (item['rating'], item['activity'], item['role'], item['date_joined'], item['nick']))
            nick, old_rating, old_activity = result
            if old_rating != item['rating']:
                self.make_player_message(nick, old_rating, item['rating'])
            ## todo: add activity chack for rating inactive players
        self.con.commit()

    def make_player_message(self, nick, old_rating, new_rating):
        title = f"{EMOJI['track_clan']} {nick}" if nick in CLAN_LEADERS else f"__{nick}__"
        change = new_rating - old_rating
        emoji = EMOJI['increase'] if change > 0 else EMOJI['decrease']
        message = f"Очки: {new_rating} {emoji} ``({change})``"
        self.changes[title] = message

    def update_squadrons(self, item):
        pass

    def close_spider(self, spider):
        self.con.commit()
        self.con.close()
        self.send_changes()

    def send_changes(self):
        pass

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
