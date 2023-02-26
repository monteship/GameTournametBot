import datetime
import time

import requests
from bs4 import BeautifulSoup

from discord_webhook import DiscordEmbed, DiscordWebhook

from config import CLAN_URL, WEBHOOK_ABANDONED, WEBHOOK_PLAYERS, EMOJI, CLAN_LEADER
from database import Database

emoji = ['<:small_green_triangle:996827805725753374>',
         '🔻']


class Player:
    """
    Class representing a player
    """

    def __init__(self, name: str, points: int, role: str,
                 date_join: datetime, table_name: str):
        self.name = name
        self.points = points
        self.role = role
        self.date_join = date_join
        self.table_name = table_name
        self.rank = self.get_rank()
        self.changes = {'points': 0, 'role': None, 'rank': 0}

    def get_rank(self) -> int:
        """
        Fetches the rank of the player
        """
        with Database(self.table_name) as conn:
            query_data = conn.query(
                f"SELECT rank FROM {self.table_name} WHERE name = '{self.name}'")
            try:
                return query_data[0][0]
            except IndexError:
                return 150

    def get_points_changes(self) -> None:
        """
        Get the points change for the player.
        """
        with Database(self.table_name) as conn:
            try:
                query_data = conn.query(
                    f"SELECT points FROM {self.table_name} WHERE name = '{self.name}'")
                points_data = query_data[0][0]
                self.changes['points'] = self.points - points_data
            except IndexError:
                self.changes = None

    def get_rank_changes(self) -> None:
        """
        Get the change in rank for the player.
        """
        with Database(self.table_name) as conn:
            query_data = conn.query(
                f"SELECT rank FROM {self.table_name} WHERE name = '{self.name}'")
            try:
                rank_data = query_data[0][0]
                if rank_data is not None:
                    rank = int(rank_data)
                    self.changes['rank'] = rank - self.rank
                    self.rank = rank
            except IndexError:
                self.changes['rank'] = 0

    def format_changes(self):
        """
        Format the message to be sent based on the points change
        """
        message = None
        title = f"__{self.name}__"
        if self.name == CLAN_LEADER:
            title = f"{EMOJI['track_clan']} {self.name}"
        if self.changes['points'] != 0:
            if self.changes['points'] > 0:
                message = f"Очки: {self.points} {EMOJI['increase']} ``(+{self.changes['points']})``"
            else:
                message = f"Очки: {self.points} {EMOJI['decrease']} ``({self.changes['points']})``"
        if self.changes['rank'] != 0:
            if self.changes['rank'] < 0:
                message = message + f"\nМісце {self.rank} {EMOJI['increase']} ``({self.changes['rank']})``"
            else:
                message = message + f"\nМісце {self.rank} {EMOJI['decrease']} ``(+{self.changes['rank']})``"
        return message, title


class PlayersLeaderboardUpdater:
    """
    Updater for the players leaderboard
    """

    def __init__(self, webhook_url: str, table_name: str):
        self.webhook_url = webhook_url
        self.table_name = table_name
        self.additional_embed = None
        self.embed = self.set_embed()
        self.personal = []
        self.players_data = []  # All players object's
        self.players_discord = 0
        self.element = None
        self.run()

    def set_embed(self) -> DiscordEmbed:
        """
        Set embed based on table name.
        """
        title = "Активні гравці" if self.table_name == 'players' else "Результати за день"
        self.additional_embed = DiscordEmbed(title=title + ' (Продовження)')
        return DiscordEmbed(title=title, color='ff0000', url=CLAN_URL)

    def run(self):
        """
        Run the leaderboard updater.
        """
        players_count = self.process_page()
        for iteration in range(0, players_count):
            self.extract_player_data(iteration)  # Make instance of players
        with Database(self.table_name) as conn:
            for player in self.players_data:
                player.get_points_changes()  # Points change
                conn.delete_data(player.name, self.table_name)  # Update database
                conn.commit()
                conn.insert_player(player, self.table_name)
            conn.set_ranks(self.table_name)  # Set ranks
            for player in self.players_data:
                try:
                    if player.changes['points'] != 0:
                        player.get_rank_changes()  # Get new rank
                        message, title = player.format_changes()
                        self.add_player_to_embed(title, message)
                        self.players_discord += 1
                except TypeError:
                    pass
        self.finish_process()

    def process_page(self):
        """
        Beautiful soup parser for the clan page.
        """
        page = requests.get(CLAN_URL, timeout=50)
        soup = BeautifulSoup(page.text, 'lxml')
        count_data = int(str(soup.find(class_='squadrons-info__meta-item').text).split()[-1])
        self.element = soup.find(class_="squadrons-members__grid-item")
        return count_data

    def finish_process(self):
        """
        After main process, send the embed.
        Cleans up database.
        """
        self.send_message_to_webhook()
        with Database(self.table_name) as conn:
            quitter_data = conn.check_quit(self.personal)
            if quitter_data is not None:
                quitter_inform(quitter_data)

    def extract_player_data(self, iteration):
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
                self.personal.append(name)
            if i == i_range_2[1]:
                points = int(self.element.text.strip())
            if i == i_range_2[2]:
                role = str(self.element.text.strip())
            if i == i_range_2[3]:
                date_join = datetime.datetime.strptime(
                    self.element.text.strip(), '%d.%m.%Y').date()
                self.players_data.append(Player(name, points, role, date_join, self.table_name))

    def add_player_to_embed(self, title: str, message: str):
        """
        Add player message to the Discord embed
        """
        if self.players_discord >= 25:
            self.additional_embed.add_embed_field(name=title,
                                                  value=message)
        else:
            self.embed.add_embed_field(name=title,
                                       value=message)

    def send_message_to_webhook(self):
        """
        Send Discord message with added players to the specified webhook URL
        """
        webhook = DiscordWebhook(url=self.webhook_url)
        webhook.remove_embeds()
        if self.players_discord >= 1:
            webhook.add_embed(self.embed)
            webhook.execute(remove_embeds=True)
        if self.players_discord >= 25:
            webhook.add_embed(self.additional_embed)
            webhook.execute(remove_embeds=True)


def quitter_inform(quitter_data: tuple[str, int, datetime]):
    """
    Informs the Discord webhook about the quitter
    """
    date_join = datetime.datetime.strptime(quitter_data[2], '%Y-%m-%d').date()
    summary = datetime.datetime.today().date() - date_join
    webhook = DiscordWebhook(url=WEBHOOK_ABANDONED)
    webhook.add_embed(DiscordEmbed(
        title=f"{quitter_data[0]}",
        description=f" \n ```Покинув нас з очками в кількості: {quitter_data[1]} \n"
                    f"Пробув з нами {str(summary.days)} дня/днів```",
        color="000000",
        url=f"https://warthunder.com/en/community/userinfo/?nick={quitter_data[0]}"))
    webhook.execute(remove_embeds=True)


if __name__ == '__main__':
    test_player = Player('test', 100, 'test',
                         datetime.datetime.today().date(), 'players')
    with Database('players') as test_conn:
        test_conn.insert_player(test_player, 'players')
        test_conn.execute(
            f"SELECT points FROM period_players WHERE name = '{test_player.name}'")
        NICKS = ['Spiox_', 'monteship', 'imeLman', 'YKPAiHA_172',
                 'SilverWINNER_UA', 'LuntikGG', 'PromiteUA',
                 'ROBOKRABE']
        for count, nick in enumerate(NICKS, 15):
            test_conn.execute(
                "UPDATE period_players SET points = ?, rank =? WHERE name = ?",
                (1200, count, nick))
            test_conn.commit()
    with Database(initialize=True) as test_conn:
        test_conn.create_databases()
        print("Database created")
    test_webhook = DiscordWebhook(url=WEBHOOK_PLAYERS)
    test_webhook.remove_embeds()
    start_time = time.time()
    PlayersLeaderboardUpdater(WEBHOOK_PLAYERS, 'period_players')
    print("End time: ", time.time() - start_time)
