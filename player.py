import datetime
import time
from sqlite3 import OperationalError

import requests
from bs4 import BeautifulSoup, NavigableString

from discord_webhook import DiscordEmbed, DiscordWebhook

from config import CLAN_URL, WEBHOOK_ABANDONED, WEBHOOK_PLAYERS, EMOJI, CLAN_LEADER
from database import Database
from squadron import EmbedsBuilder, DiscordWebhookNotification


class Player:
    emoji = EMOJI
    """
    Class representing a player
    """

    def __init__(self, name: str, points: int, role: str,
                 date_join: datetime):
        self.name = name
        self.points = points
        self.role = role
        self.date_join = date_join
        self.rank = None
        self.changes = {'points': 0, 'role': None, 'rank': 0}

    def format_changes(self):
        """
        Format the message to be sent based on the points change
        """
        message = None
        title = f"__{self.name}__"
        if self.name == CLAN_LEADER:
            title = f"{self.emoji['track_clan']} {self.name}"
        if self.changes['points'] != 0:
            if self.changes['points'] > 0:
                message = f"Очки: {self.points} {self.emoji['increase']} ``(+{self.changes['points']})``"
            else:
                message = f"Очки: {self.points} {self.emoji['decrease']} ``({self.changes['points']})``"
        message = message + f"\nМісце {self.rank}"
        if self.changes['rank'] != 0:
            if self.changes['rank'] < 0:
                message = message + f" {self.emoji['increase']} ``({self.changes['rank']})``"
            else:
                message = message + f" {self.emoji['decrease']} ``(+{self.changes['rank']})``"
        return message, title


class ClanPageScraper:

    def __init__(self, clan_url: str):
        self.clan_url = clan_url
        self.members: int = 0
        self.element = self.process_clan_page()
        self.players = []
        for i in range(0, self.members):
            self.players.append(self.extract_player_data(i))

    def process_clan_page(self) -> NavigableString:
        page = requests.get(self.clan_url, timeout=50)
        soup = BeautifulSoup(page.text, 'lxml')
        self.members = int(str(soup.find(class_='squadrons-info__meta-item').text).split()[-1])
        return soup.find(class_="squadrons-members__grid-item")

    def extract_player_data(self, iteration) -> Player:
        """
        Extracts the player data from a BeautifulSoup element
        """
        i_range = 11 if iteration == 0 else 6
        i_range_2 = [6, 7, 9, 10] if iteration == 0 else [1, 2, 4, 5]
        name, points, role, date_join = '', 0, '', '01-01-2001'
        for i in range(i_range):
            self.element = self.element.find_next_sibling()
            if i == i_range_2[0]:
                name = self.element.text.strip()
            if i == i_range_2[1]:
                points = int(self.element.text.strip())
            if i == i_range_2[2]:
                role = str(self.element.text.strip())
            if i == i_range_2[3]:
                date_join = datetime.datetime.strptime(
                    self.element.text.strip(), '%d.%m.%Y').date()
                return Player(name, points, role, date_join)


class PlayerDatabase(Database):
    player_tables = "players", "period_players"

    def __init__(self, table_name: str, player: Player = None):
        super().__init__()
        self.table_name = table_name
        if player is not None:
            self.player = player
            self.player.rank = self.get_rank()

    def get_rank(self) -> int:
        query_data = self.query(
            f"SELECT rank FROM {self.table_name} WHERE name = '{self.player.name}'")
        try:
            return int(query_data[0][0])
        except IndexError:
            return 150

    def retrieve_player_points_changes(self):
        try:
            points_change = self.player.points - int(self.query(
                f"SELECT points FROM {self.table_name} WHERE name = '{self.player.name}'")[0][0])
            self.player.changes['points'] = points_change
        except IndexError:
            self.player.changes['points'] = 0

    def retrieve_player_rank_changes(self):
        try:
            rank_change = self.player.rank - self.query(
                f"SELECT rank FROM {self.table_name} WHERE name = '{self.player.name}'")[0][0]
            self.player.changes['rank'] = rank_change
        except IndexError:
            self.player.changes['rank'] = 0

    def update_player_data(self):
        self.execute(f"SELECT * FROM {self.table_name} WHERE name = '{self.player.name}'")
        if self.fetchone() is None:
            sql_query = f"INSERT INTO {self.table_name} VALUES (?, ?, ?, ?, ?)"
            sql_values = ((self.player.name, self.player.points, self.player.role, self.player.date_join,
                           self.player.rank))
            self.execute(sql_query, sql_values)
        else:
            sql_query = f'''UPDATE {self.table_name}
                                         SET points = ?,
                                             role = ?,
                                             date_join = ?
                                         WHERE name = ?'''
            sql_values = (self.player.points, self.player.role, self.player.date_join, self.player.name)
            self.execute(sql_query, sql_values)
            self.commit()
        self.commit()

    def update_players_ranks(self):
        """
        Sets the ranks of the players in the database
        """
        self.execute(f"""UPDATE {self.table_name}
                        SET rank = (
                            SELECT COUNT(*) + 1
                            FROM players p2
                            WHERE p2.points > {self.table_name}.points
                                    )
                        WHERE {self.table_name}.points IS NOT NULL;""")
        self.commit()


class PlayersLeaderboardUpdater:
    """
    Updater for the players leaderboard
    """

    def __init__(self, webhook_url: str, table_name: str, initial: bool = False):
        self.webhook_url = webhook_url
        self.table_name = table_name
        self.embeds = EmbedsBuilder(self.table_name, option=True)
        self.personal = []
        self.active_players = 0
        self.element = None
        self.run(initial)

    def run(self, initial: bool):
        """
        Run the leaderboard updater.
        """
        # Get all players instances
        scraper = ClanPageScraper(CLAN_URL)

        # Get players points changes and update for getting new rank
        for player in scraper.players:
            self.personal.append(player.name)
            with PlayerDatabase(self.table_name, player) as conn:
                if not initial:
                    conn.retrieve_player_points_changes()
                conn.update_player_data()

        # Update the players ranks
        with PlayerDatabase(self.table_name) as conn:
            conn.update_players_ranks()

        # Get players rank changes after updating players data
        for player in scraper.players:
            if player.changes['points'] == 0:
                continue
            with PlayerDatabase(self.table_name, player) as conn:
                conn.retrieve_player_rank_changes()
                message, title = player.format_changes()
                self.active_players += 1
                self.embeds.add_player_data(self.active_players, title, message)

        # Finish update
        DiscordWebhookNotification(self.webhook_url, self.embeds, self.active_players)
        QuitterInformer(self.personal)


class QuitterInformer:
    player_tables = ["players", "period_players"]

    def __init__(self, personal: list):
        self.personal = personal
        self.quitters = self.check_quit()
        if self.quitters is not None:
            self.quitter_inform()

    def check_quit(self) -> list | None:
        """
        Parses the players from the leaderboard,
        checks if they left and adds them to the Discord embed
        """
        quitters_data = []
        with PlayerDatabase('players') as conn:
            query_data = conn.query("SELECT name FROM players")
            db_personal = [person[0] for person in query_data]
            quit_persons = set(db_personal) - set(self.personal)
            if not quit_persons:
                return None
            for person in quit_persons:

                quitters_data.append(conn.query(
                    f"SELECT name, points, date_join FROM players WHERE name = '{person}'")[0])
                for table in self.player_tables:
                    conn.delete_data(person, table)
            return quitters_data

    def quitter_inform(self):
        """
        Informs the Discord webhook about the quitter
        """
        webhook = DiscordWebhook(url=WEBHOOK_ABANDONED)
        webhook.remove_embeds()
        for data in self.quitters:
            date_join = datetime.datetime.strptime(data[2], '%Y-%m-%d').date()
            summary = datetime.datetime.today().date() - date_join
            embed = DiscordEmbed(
                title=f"{data[0]}",
                description=f" \n ```Покинув нас з очками в кількості: {data[1]} \n"
                            f"Пробув з нами {str(summary.days)} дня/днів```",
                color="000000",
                url=f"https://warthunder.com/en/community/userinfo/?nick={data[0]}")

            webhook.add_embed(embed)
            webhook.execute(remove_embeds=True)


if __name__ == '__main__':
    start_time = time.time()
    PlayersLeaderboardUpdater(WEBHOOK_PLAYERS, 'players')
    print("End time: ", time.time() - start_time)
