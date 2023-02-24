import datetime
import time

import sqlite3
import requests
from bs4 import BeautifulSoup

from discord_webhook import DiscordEmbed, DiscordWebhook

from config import CLAN_URL, WEBHOOK_ABANDONED, WEBHOOK_PLAYERS, PLAYERS_EMBED, DB_PATH


def get_soup():
    page = requests.get(CLAN_URL, timeout=50)
    return BeautifulSoup(page.text, 'lxml')


class Player:
    def __init__(self, name: str, points: int, role: str, date_join: datetime, table_name: str):
        self.name: str = name
        self.points: int = points
        self.role: str = role
        self.date_join: datetime = date_join
        self.table_name: str = table_name
        self.old_rank: int = self.get_rank()
        self.changes: dict = {'points_change': None, 'role_change': None, 'rank_change': None}
        self.rank: int = 0

    def get_rank(self) -> int:
        with DatabaseUpdate(self.table_name) as getter:
            try:
                getter.sql.execute(f"SELECT rank FROM {self.table_name} WHERE name = '{self.name}'")
                data = getter.sql.fetchone()[0]
                return data
            except TypeError:
                return 0

    def get_stats_changes(self, change) -> str:
        with DatabaseUpdate(self.table_name) as getter:
            getter.sql.execute(
                f"SELECT {change} FROM {self.table_name} WHERE name = '{self.name}'")
            if change == 'points':
                try:
                    data = getter.sql.fetchone()[0]
                    self.changes['points_change'] = self.points - data
                except TypeError as e:
                    self.changes['points_change'] = 0
                    self.old_rank = 0
            if change == 'role':
                self.changes['role_change'] = f"{self.role} --> {data[0]}"
            if change == 'rank':
                try:
                    data = getter.sql.fetchone()[0]
                    self.rank = data
                    self.changes['rank_change'] = int(data) - int(self.old_rank)
                except TypeError as e:
                    self.changes['points_change'] = 0
                    self.rank = 0

    def format_change(self, change):
        """
        Format the message to be sent based on the points change
        """
        message = None
        title = f"{self.name}\nМісце {self.rank}"
        emoji = ['<:small_green_triangle:996827805725753374>',
                 '🔻']
        if change == 'points':
            if self.changes['points_change'] > 0:
                message = f"**Очки**: {self.points} {emoji[0]} (+{self.changes['points_change']})"
            if self.changes['points_change'] < 0:
                message = f"**Очки**: {self.points} {emoji[1]} ({self.changes['points_change']})"
            return message
        if change == 'rank':
            try:
                if self.changes['rank_change'] > 0:
                    title = f"Місце: {self.rank} {emoji[0]} (+{self.changes['rank_change']})\n{self.name}"
                if self.changes['rank_change'] < 0:
                    title = f"Місце: {self.rank} {emoji[1]} (+{self.changes['rank_change']})\n{self.name}"
            except TypeError as e:
                self.changes['rank_change'] = 0
            return title


class PlayersLeaderboardUpdater:

    def __init__(self, webhook_url: str, table_name: str,
                 discord_emb: DiscordEmbed, discord_emb_2: DiscordEmbed):
        self.webhook_url = webhook_url
        self.table_name = table_name
        self.discord_emb = discord_emb
        self.discord_emb_2 = discord_emb_2
        self.personal = []
        self.players_data = []  # All players object's
        self.players_discord = 0
        self.run()

    def run(self):
        self.delete_embed()
        message_data, title_data = [], []
        soup = get_soup()
        players_count = int(str(soup.find(class_='squadrons-info__meta-item').text).split()[-1])
        element = soup.find(class_="squadrons-members__grid-item")
        for iteration in range(0, players_count):
            element = self.extract_player_data(element, iteration)
        with DatabaseUpdate(self.table_name) as updater:
            for player in self.players_data:
                player.get_stats_changes('points')
                message_data.append(player.format_change('points'))
                updater.update_player(player)
            updater.set_ranks()
            for player in self.players_data:
                player.get_stats_changes('rank')
                title_data.append(player.format_change('rank'))
            for message, title in zip(message_data, title_data):
                if message is not None:
                    self.add_player_to_embed(title, message)
                    self.players_discord += 1
        self.send_message_to_webhook()
        self.person_is_quit()

    def delete_embed(self):
        elements = self.discord_emb, self.discord_emb_2
        try:
            for element in elements:
                for field in range(0, len(element.get_embed_fields())):
                    element.delete_embed_field(field)
        except IndexError:
            pass

    def extract_player_data(self, element, iteration):
        """
        Extracts the player data from a BeautifulSoup element
        """
        i_range = 11 if iteration == 0 else 6
        i_range_2 = [6, 7, 9, 10] if iteration == 0 else [1, 2, 4, 5]
        name, points, role, date_join = '', 0, '', '01-01-2001'
        for i in range(i_range):
            element = element.find_next_sibling()
            if i == i_range_2[0]:
                name = element.text.strip()
                self.personal.append(name)
            if i == i_range_2[1]:
                points = int(element.text.strip())
            if i == i_range_2[2]:
                role = str(element.text.strip())
            if i == i_range_2[3]:
                date_join = datetime.datetime.strptime(
                    element.text.strip(), '%d.%m.%Y').date()
                self.players_data.append(Player(name, points, role, date_join, self.table_name))
                return element

    def add_player_to_embed(self, title: str, message: str):
        """
        Add player and message to the Discord embed
        """
        if self.players_discord >= 25:
            self.discord_emb_2.add_embed_field(name=title, value=message)
        self.discord_emb.add_embed_field(name=title, value=message)

    def send_message_to_webhook(self):
        """
        Send Discord message with added players to the specified webhook URL
        """
        webhook = DiscordWebhook(url=self.webhook_url)
        if self.players_discord >= 1:
            webhook.add_embed(self.discord_emb)
            webhook.execute(remove_embeds=True)
        if self.players_discord >= 25:
            webhook.add_embed(self.discord_emb_2)
            webhook.execute(remove_embeds=True)

    def person_is_quit(self):
        """
        Parses the players from the leaderboard,
        check if they are leave and adds them to the Discord embed

        """
        with DatabaseUpdate('players') as getter:
            getter.sql.execute(f"SELECT name FROM players")
            sql_personal = [person[0] for person in getter.sql.fetchall()]
            quit_persons = set(sql_personal) - set(self.personal)
            if quit_persons:
                for person in quit_persons:
                    table_names = 'players', 'period_players'
                    name, points, date = None, None, None
                    getter.sql.execute(f"SELECT name, points, date_join FROM players WHERE name = '{person}'")
                    try:
                        name, points, date = getter.sql.fetchall()[0]
                        for table in table_names:
                            getter.delete_player(table, person)
                    except sqlite3.Error:
                        pass
                    quitter_notify(name, points, date)


def quitter_notify(name: str, points: int, date: datetime):
    """
    Informs the Discord webhook about the quitter
    """
    summary = datetime.datetime.today().date() - datetime.datetime.strptime(date, '%d-%m-%Y').date()
    webhook = DiscordWebhook(url=WEBHOOK_ABANDONED)
    webhook.add_embed(DiscordEmbed(
        title=f"**{name}**",
        description=f" \n Покинув нас з очками в кількості: **{points}** \n"
                    f"Пробув з нами **{str(summary.days)}** дня/днів",
        color="000000",
        url=f"https://warthunder.com/en/community/userinfo/?nick={name}"))
    webhook.execute(remove_embeds=True)


class DatabaseUpdate:
    def __init__(self, table_name: str = 'null'):
        self.table_name = table_name
        self.db_file = DB_PATH
        self.conn = None
        self.sql = None

    def __enter__(self):
        self.conn = sqlite3.connect(self.db_file)
        self.sql = self.conn.cursor()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            self.conn.commit()
            self.conn.close()

    def set_ranks(self):
        """
        Sets the ranks of the players in the database
        """
        self.sql.execute(f"""UPDATE {self.table_name}
                        SET rank = (
                            SELECT COUNT(*) + 1
                            FROM players p2
                            WHERE p2.points > {self.table_name}.points
                                    )
                        WHERE {self.table_name}.points IS NOT NULL;""")

    def delete_player(self, table_name, name):
        """
            Try to delete a player from the database
        """
        try:
            self.sql.execute(f"DELETE FROM {table_name} WHERE name = '{name}'")
        except ValueError:
            pass

    def insert_player(self, table_name: str, player: Player):
        """
        Insert a player into the database
        """
        self.sql.execute(
            f"INSERT INTO {table_name} (name, points, role, date_join, rank) VALUES (?, ?, ?, ?, ?)",
            (player.name, player.points, player.role, player.date_join, player.rank))

    def update_player(self, player: Player):
        try:
            self.sql.execute(
                "UPDATE players SET points = ?, role = ?, date_join = ? WHERE name = ?",
                (player.points, player.role, player.date_join, player.name))
            if player.name == 'KOlS':
                print('doane')
        except sqlite3.Error as e:
            print(e)
            try:
                self.delete_player(self.table_name, player.name)
            except sqlite3.Error:
                pass
            self.insert_player(self.table_name, player)
        self.conn.commit()

    def create_databases(self):
        """
        Creates the database if it doesn't exist
        """
        self.sql.execute(
            '''
            CREATE TABLE IF NOT EXISTS "players" 
            ("name" TEXT,
            "points" INTEGER,
            "role" TEXT,
            "date_join" TEXT,
            "rank" INTEGER)
            ''')
        self.sql.execute(
            '''
            CREATE TABLE IF NOT EXISTS "period_players" 
            ("name" TEXT,
            "points" INTEGER,
            "role" TEXT,
            "date_join" TEXT,
            "rank" INTEGER)
            ''')
        self.sql.execute(
            '''
            CREATE TABLE IF NOT EXISTS "squadrons" 
            ("name" TEXT,
            "rank" INTEGER,
            "points" INTEGER,
            "k_d" INTEGER,
            "players" INTEGER)
            ''')
        self.sql.execute(
            '''
            CREATE TABLE IF NOT EXISTS "period_squadrons" 
            ("name" TEXT,
            "rank" INTEGER,
            "points" INTEGER,
            "k_d" INTEGER,
            "players" INTEGER)
            ''')


if __name__ == '__main__':
    start_time = time.time()
    PlayersLeaderboardUpdater(WEBHOOK_PLAYERS, 'players', *PLAYERS_EMBED)
    print("End time: ", time.time() - start_time)
