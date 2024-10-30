import datetime
import sqlite3
from abc import ABC, abstractmethod

from discord_webhook import DiscordWebhook, DiscordEmbed

from .settings import EMOJI, CLAN_LEADERS, CLAN_URL, WEBHOOK_PLAYERS, WEBHOOK_DAY, TRACKED_CLAN, WEBHOOK_SQUADRONS, \
    LEADERBOARD_URL, DB_NAME, WEBHOOK_ABANDONED


class AbstractWTPipeline(ABC):
    players_tables = [
        'players_daily', 'players_instant',
    ]
    squadrons_tables = [
        'squadrons_daily', 'squadrons_instant',
    ]

    def __init__(self):
        self.con = sqlite3.connect(DB_NAME)
        self.cur = self.con.cursor()
        self.first_message = DiscordEmbed(color='ff0000')
        self.second_message = DiscordEmbed(color='ff0000')
        self.table = None
        self.webhook_url = None
        self.create_tables()
        self.messages = dict()
        self.stop_item_iter = 52

    def process_item(self, item, spider):
        if not self.table:
            self.table = spider.table_name

    @abstractmethod
    def update_data(self, item):
        pass

    @abstractmethod
    def make_message(self, old_data, item):
        pass

    @abstractmethod
    def build_embed(self):
        pass

    def send_message(self):
        webhook = DiscordWebhook(url=self.webhook_url)
        webhook.add_embed(self.first_message)
        webhook.execute(remove_embeds=True)
        if len(self.messages) > ((self.stop_item_iter + 1) / 2):
            webhook.add_embed(self.second_message)
            webhook.execute(remove_embeds=True)

    def close_spider(self, spider):
        self.con.commit()
        self.con.close()
        if self.messages:
            self.build_embed()
            self.send_message()

    def create_tables(self):
        for table_name in self.players_tables:
            self.cur.execute(
                f'''
                CREATE TABLE IF NOT EXISTS {table_name} 
                       ("nick" TEXT, "rating" INTEGER, "activity" INTEGER, "role" TEXT, "date_joined" DATE)
                   ''')
        for table_name in self.squadrons_tables:
            self.cur.execute(
                f'''
                CREATE TABLE IF NOT EXISTS {table_name} 
                   ("tag" TEXT, "rank" INTEGER, "name" TEXT, "members" INTEGER, "rating" INTEGER, "kills_to_death" INTEGER)
                   ''')
        self.con.commit()


def inform_leaving(nick, rating, date_joined):
    webhook = DiscordWebhook(url=WEBHOOK_ABANDONED)
    webhook.remove_embeds()
    date_join = datetime.datetime.strptime(date_joined, '%Y-%m-%d').date()
    summary = datetime.datetime.today().date() - date_join
    embed = DiscordEmbed(
        title=f"{nick}",
        description=f""" \n ```Left us with points in quantity: {rating} \n
                    Stayed with us for a {str(summary.days)} day\n
                    Maybe he changed his nickname.```
                    [EXAMINE](https://warthunder.com/en/community/userinfo/?nick={nick})
                    \n""",
        color="000000",
        url=f"https://warthunder.com/en/community/userinfo/?nick={nick}"

    )
    webhook.add_embed(embed)
    webhook.execute(remove_embeds=True)


class PlayersWTPipeline(AbstractWTPipeline, ABC):

    def __init__(self):
        super().__init__()
        self.members = []

    def send_message(self):
        webhook = DiscordWebhook(url=self.webhook_url)
        webhook.add_embed(self.first_message)
        webhook.execute(remove_embeds=True)
        if len(self.messages) > ((self.stop_item_iter + 1) / 2):
            webhook.add_embed(self.second_message)
            webhook.execute(remove_embeds=True)
    def process_item(self, item, spider):
        super().process_item(item, spider)
        self.members.append(item['nick'])
        self.webhook_url = WEBHOOK_PLAYERS if self.table == 'players_instant' else WEBHOOK_DAY
        self.update_data(item)
        return item

    def update_data(self, item):
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
                self.make_message(result, item)
        self.con.commit()

    def make_message(self, old_data, item):
        title = f"{EMOJI['track_clan']} {item['nick']}" if item['nick'] in CLAN_LEADERS else f"__{item['nick']}__"
        change = int(item['rating']) - old_data[1]
        emoji = EMOJI['increase'] if change > 0 else EMOJI['decrease']
        message = f"Points: {item['rating']} {emoji} ``({change})``"
        self.messages[title] = message

    def build_embed(self):
        self.first_message.set_title("Active players" if self.table == 'players_instant' else "Results for the day")
        for message in {self.first_message, self.second_message}:
            message.set_url(CLAN_URL)
        for i, (title, changes) in enumerate(self.messages.items(), 1):
            if i > (self.stop_item_iter / 2):
                self.second_message.add_embed_field(
                    name=title,
                    value=changes
                )
            else:
                self.first_message.add_embed_field(
                    name=title,
                    value=changes
                )

    def close_spider(self, spider):
        self.check_leavers()
        self.assign_roles()
        self.con.commit()
        self.con.close()
        if self.messages:
            self.build_embed()
            self.send_message()

    def check_leavers(self):
        self.cur.execute("SELECT nick, rating, date_joined FROM players_instant")
        database_members = self.cur.fetchall()
        leavers = [member for member in database_members if member[0] not in self.members]
        if len(leavers) < 10:
            for leaver in leavers:
                inform_leaving(*leaver)
                for table_name in self.players_tables:
                    self.cur.execute(
                        f"DELETE FROM {table_name} WHERE nick = ?",
                        (leaver[0],))

    def assign_roles(self):
        pass


class ClansWTPipeline(AbstractWTPipeline, ABC):
    def process_item(self, item, spider):
        super().process_item(item, spider)
        self.webhook_url = WEBHOOK_SQUADRONS if self.table == 'squadrons_instant' else WEBHOOK_DAY
        self.update_data(item)
        return item

    def update_data(self, item):
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
            self.make_message(result, item)
        self.con.commit()

    def make_message(self, old_data, item):
        msg_emoji = EMOJI['track_clan'] if TRACKED_CLAN in item['name'] else EMOJI['all_clans']
        title = f"{msg_emoji}          __{item['name']}__"
        changes = dict(
            rank=item['rank'] - int(old_data[0]),
            members=item['members'] - int(old_data[1]),
            rating=item['rating'] - int(old_data[2]),
            kills_to_death=round((item['kills_to_death'] - int(old_data[3])), 2)
        )
        for key, change in changes.items():
            for i in range(0, 4):
                if change > 0:
                    changes[key] = f"{item[key]} {EMOJI['increase']} (+{change})"
                elif change < 0:
                    changes[key] = f"{item[key]} {EMOJI['decrease']} ({change})"
        message = f"""
            **Rank**: {item['rank']}
            **Points**: {item['rating']}
            **K\\D**: {item['kills_to_death']}
            **Members**: {item['members']}
        """
        self.messages[item['rank']] = (title, message)

    def build_embed(self):
        self.stop_item_iter = 19
        self.first_message.set_title("Leaderboard" if self.table == 'squadrons_instant' else "Results for the day")
        for message in {self.first_message, self.second_message}:
            message.set_url(LEADERBOARD_URL)
        for i, (title, changes) in self.messages.items():
            if i < ((self.stop_item_iter + 1) / 2):
                self.first_message.add_embed_field(
                    name=title,
                    value=changes
                )
            elif i < self.stop_item_iter:
                self.second_message.add_embed_field(
                    name=title,
                    value=changes
                )
