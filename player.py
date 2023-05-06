import datetime
import re
import time
from typing import Iterator

import requests
from bs4 import BeautifulSoup, NavigableString, ResultSet
from discord_webhook import DiscordEmbed, DiscordWebhook
from config import CLAN_URL, WEBHOOK_ABANDONED, WEBHOOK_PLAYERS, EMOJI, CLAN_LEADER
from database import Database
from squadron import EmbedsBuilder, DiscordWebhookNotification
from rich import print

class Player:
    """
    Class representing a player
    """
    emoji = EMOJI

    def __init__(self, name: str, points: int, role: str,
                 date_join: datetime):
        self.name = name
        self.points = points
        self.role = role
        self.date_join = date_join
        self.rank = None
        self.changes = {'points': 0, 'role': None, 'rank': 0}

    def title(self) -> str:
        if self.name in CLAN_LEADER:
            return f"{self.emoji['track_clan']} {self.name}"
        return f"__{self.name}__"

    def stats_changes(self) -> str:
        """
        Format the message to be sent based on the points change
        """
        message = ''
        if self.changes['points'] != 0:
            if self.changes['points'] > 0:
                message = \
                    f"Очки: {self.points} {self.emoji['increase']} ``(+{self.changes['points']})``"
            else:
                message = \
                    f"Очки: {self.points} {self.emoji['decrease']} ``({self.changes['points']})``"
        message = message + f"\nМісце {self.rank}"
        if self.changes['rank'] != 0:
            if self.changes['rank'] < 0:
                message = message + f" {self.emoji['increase']} ``({self.changes['rank']})``"
            else:
                message = message + f" {self.emoji['decrease']} ``(+{self.changes['rank']})``"
        return message


class ClanPageScraper:

    def __init__(self, clan_url: str):
        self.clan_url = clan_url
        self.members: int = 0
        self.element = self.get_clan_page()
        self.players = [player for player in self.player_generator()]

    def get_clan_page(self) -> ResultSet:
        page = requests.get(self.clan_url, timeout=50)
        soup = BeautifulSoup(page.text, 'lxml')
        return soup.find_all(class_="squadrons-members__grid-item")

    def player_generator(self) -> Iterator[Player]:
        """
        Generates the players
        """
        for i in range(7, len(self.element), 6):
            name = re.search(r'nick=(.*)"', str(self.element[i])).group(1)
            points = int(self.element[i+1].text.strip())
            role = str(self.element[i+3].text.strip())
            date_join = datetime.datetime.strptime(self.element[i+4].text.strip(), '%d.%m.%Y').date()
            yield Player(name, points, role, date_join)

class PlayerDatabase(Database):
    player_tables = "players", "period_players"

    def __init__(self, table_name: str, player: Player = None):
        super().__init__()
        self.table_name = table_name
        if player is not None:
            self.player = player
            self.player.rank = self.get_rank()

    def get_rank(self) -> int:
        try:
            return int(self.query(
                f"SELECT rank FROM {self.table_name} WHERE name = '{self.player.name}'")[0][0])
        except IndexError as err:
            print(err, 'line 102')
            return 150

    def retrieve_player_points_changes(self):
        try:
            points_change = self.player.points - int(self.query(
                f"SELECT points FROM {self.table_name} WHERE name = '{self.player.name}'")[0][0])
            self.player.changes['points'] = points_change
        except IndexError as err:
            print(err, 'line 110')
            self.player.changes['points'] = 0

    def retrieve_player_rank_changes(self):
        try:
            rank_change = self.player.rank - self.query(
                f"SELECT rank FROM {self.table_name} WHERE name = '{self.player.name}'")[0][0]
            self.player.changes['rank'] = rank_change
        except IndexError as err:
            print(err, 'line 118')
            self.player.changes['rank'] = 0

    def update_player_data(self):
        """
        Updates the player data in the database if it exists,
        else creates it
        """
        self.execute(f'''SELECT * FROM {self.table_name}
                          WHERE name = "{self.player.name}"''')
        if self.fetchone() is None:
            sql_query = f'''INSERT INTO {self.table_name}
                             VALUES (?, ?, ?, ?, ?)'''
            sql_values = ((self.player.name,
                           self.player.points,
                           self.player.role,
                           self.player.date_join,
                           self.player.rank))
            self.execute(sql_query, sql_values)
        else:
            sql_query = f'''UPDATE {self.table_name}
                             SET points = ?,
                                 role = ?,
                                 date_join = ?
                             WHERE name = ?'''
            sql_values = (self.player.points,
                          self.player.role,
                          self.player.date_join,
                          self.player.name)
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
    Main class for updating the players leaderboard
    """

    def __init__(self, webhook_url: str, table_name: str, ):
        self.webhook_url = webhook_url
        self.table_name = table_name
        self.embeds = EmbedsBuilder(self.table_name)
        self.personal = []
        self.active_players = 0
        self.element = None
        self.players = ClanPageScraper(CLAN_URL).players
        self.process_players()

    def process_players(self):
        """
        Run the leaderboard updater.
        """
        for player in self.players:
            self.personal.append(player.name)
            with PlayerDatabase(self.table_name, player) as conn:
                conn.retrieve_player_points_changes()
                conn.update_player_data()

        # Update the players ranks
        with PlayerDatabase(self.table_name) as conn:
            conn.update_players_ranks()

        # Get players rank changes after updating players data
        for player in self.players:
            if player.changes['points'] == 0:
                continue
            with PlayerDatabase(self.table_name, player) as conn:
                conn.retrieve_player_rank_changes()
                self.active_players += 1
                self.embeds.add_player_data(self.active_players, player)

        # Finish update
        DiscordWebhookNotification(self.webhook_url, self.embeds, self.active_players)
        QuittersProcess(self.personal)


class Quitter:
    def __init__(self, name: str, points: int, date_join: datetime):
        self.name = name
        self.points = points
        self.date_join = date_join
        self.quit = self._nick_validation()

    def _nick_validation(self) -> bool:
        page = requests.get(
            f"https://warthunder.com/en/community/searchplayers/?name={self.name}",
            timeout=10)
        soup = BeautifulSoup(page.content, "lxml")
        return bool(soup.find_all(string=self.name))


class QuittersProcess:
    """
    Class representing the informer for the quitter
    """
    player_tables = ["players", "period_players"]

    def __init__(self, personal: list):
        self.personal = personal
        self.quitters: list[Quitter] = []
        self.check_quit()
        if self.quitters:
            self.quitter_inform()

    def check_quit(self) -> list | None:
        """
        Parses the players from the leaderboard,
        checks if they left and adds them to the Discord embed
        """
        with PlayerDatabase('players') as conn:
            query_data = conn.query("SELECT name FROM players")
            db_personal = [person[0] for person in query_data]
            quit_persons = set(db_personal) - set(self.personal)
            if not quit_persons:
                return None
            for person in quit_persons:
                name, points, date_join = conn.query(
                    f"SELECT name, points, date_join FROM players WHERE name = '{person}'")[0]
                self.quitters.append(Quitter(name, points, date_join))
                for table in self.player_tables:
                    conn.delete_data(person, table)

    def quitter_inform(self):
        """
        Informs the Discord webhook about the quitter
        """
        webhook = DiscordWebhook(url=WEBHOOK_ABANDONED)
        webhook.remove_embeds()
        for quitter in self.quitters:
            if not quitter.quit:
                embed = DiscordEmbed(
                    title=f"{quitter.name} змінив нікнейм...")
            else:
                date_join = datetime.datetime.strptime(
                    quitter.date_join, '%Y-%m-%d').date()
                summary = datetime.datetime.today().date() - date_join
                embed = DiscordEmbed(
                    title=quitter.name,
                    description=f" \n ```Покинув нас з очками в кількості: {quitter.points} \n"
                                f"Пробув з нами {str(summary.days)} дня/днів```",
                    color="000000",
                    url=f"https://warthunder.com/en/community/userinfo/?nick={quitter.name}")
            webhook.add_embed(embed)
            webhook.execute(remove_embeds=True)


if __name__ == '__main__':
    start_time_t = time.time()
    PlayersLeaderboardUpdater(WEBHOOK_PLAYERS, 'period_players')
    print("End time: ", time.time() - start_time_t)
