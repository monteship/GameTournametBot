import abc
import datetime
from typing import List

from database import Leaver, DatabaseClanItem
from scrapers import ScrapedClanItem
from settings import ClanCredentials, EMOJI, LEADERBOARD_URL
from discord_webhook import DiscordWebhook, DiscordEmbed


def inform_leaving(leaver: Leaver, clan_credentials: ClanCredentials):
    webhook = DiscordWebhook(url=clan_credentials.webhook_leave)
    webhook.remove_embeds()
    date_join = datetime.datetime.strptime(leaver.date_joined, "%Y-%m-%d").date()
    summary = datetime.datetime.today().date() - date_join
    embed = DiscordEmbed(
        title=f"{leaver.nick}",
        description=f""" \n ```Left us with points in quantity: {leaver.rating} \n
                    Stayed with us for a {str(summary.days)} day\n
                    Maybe he changed his nickname.```
                    [EXAMINE](https://warthunder.com/en/community/userinfo/?nick={leaver.nick})
                    \n""",
        color="000000",
        url=f"https://warthunder.com/en/community/userinfo/?nick={leaver.nick}",
    )
    webhook.add_embed(embed)
    webhook.execute(remove_embeds=True)


class AbstractNotifier(abc.ABC):
    stop_items: int

    @abc.abstractmethod
    def __init__(
        self,
        clan_credentials: ClanCredentials,
        has_changes: dict[list] | list,
        table_name: str,
    ):
        self.clan_credentials = clan_credentials
        self.has_changes = has_changes
        self.table_name = table_name
        self.webhook_url = self.get_webhook_url()
        self.message = dict()
        self.webhook = DiscordWebhook(url=self.get_webhook_url())
        self.first_message = DiscordEmbed(color="ff0000", url=LEADERBOARD_URL)
        self.second_message = DiscordEmbed(color="ff0000", url=LEADERBOARD_URL)

    @abc.abstractmethod
    def generate_message(self) -> None:
        pass

    @abc.abstractmethod
    def embed_constructor(self) -> None:
        pass

    @abc.abstractmethod
    def get_webhook_url(self) -> str:
        pass

    def send_message(
        self,
    ):
        self.webhook.add_embed(self.first_message)
        self.webhook.execute(remove_embeds=True)
        if len(self.message) > self.stop_items:
            self.webhook.add_embed(self.second_message)
            self.webhook.execute(remove_embeds=True)

    def process(self):
        self.generate_message()
        self.embed_constructor()
        self.send_message()


class LeaderboardNotifier(AbstractNotifier):
    stop_items = 19

    def __init__(
        self,
        clan_credentials: ClanCredentials,
        has_changes: List,
        table_name: str,
    ):
        super().__init__(clan_credentials, has_changes, table_name)

    def generate_message(self):
        for old_data, item in self.has_changes:
            old_data: DatabaseClanItem = old_data
            item: ScrapedClanItem = item
            msg_emoji = (
                EMOJI["track_clan"]
                if self.clan_credentials.tag in item.name
                else EMOJI["all_clans"]
            )
            title = f"{msg_emoji}          __{item.name}__"
            changes = dict(
                rank=item.rank - int(old_data.rank),
                members=item.members - int(old_data.members),
                rating=item.rating - int(old_data.rating),
                kills_to_death=round(
                    (item.kills_to_death - int(old_data.kills_to_death)), 2
                ),
            )
            for key, change in changes.items():
                for i in range(0, 4):
                    if change > 0:
                        changes[
                            key
                        ] = f"{item.model_dump()[key]} {EMOJI['increase']} (+{change})"
                    elif change < 0:
                        changes[
                            key
                        ] = f"{item.model_dump()[key]} {EMOJI['decrease']} ({change})"
            message = f"""
                **Rank**: {item.rank}
                **Points**: {item.rating}
                **K\\D**: {item.kills_to_death}
                **Members**: {item.members}
            """
            self.message[item.rank] = (title, message)

    def embed_constructor(self):
        self.first_message.set_title(
            "Leaderboard"
            if self.table_name == "squadrons_instant"
            else "Results for the day"
        )
        for i, (title, changes) in self.message.items():
            if i < ((self.stop_items + 1) / 2):
                self.first_message.add_embed_field(name=title, value=changes)
            elif i < self.stop_items:
                self.second_message.add_embed_field(name=title, value=changes)

    def get_webhook_url(self):
        return (
            self.clan_credentials.webhook_squadrons
            if self.table_name == "squadrons_instant"
            else self.clan_credentials.webhook_day
        )


class PlayersNotifier(AbstractNotifier):
    stop_items = 52

    def __init__(
        self,
        clan_credentials: ClanCredentials,
        has_changes: dict[list],
        table_name: str,
    ):
        super().__init__(clan_credentials, has_changes, table_name)
        self.first_message = DiscordEmbed(color="ff0000", url=clan_credentials.url)
        self.second_message = DiscordEmbed(color="ff0000", url=clan_credentials.url)

    def generate_message(self):
        for old_data, item in self.has_changes:
            title = (
                f"{EMOJI['track_clan']} {item.nick}"
                if item.nick in self.clan_credentials.officers
                else f"__{item.nick}__"
            )
            change = int(item.rating) - old_data[1]
            emoji = EMOJI["increase"] if change > 0 else EMOJI["decrease"]
            message = f"Points: {item.rating} {emoji} ``({change})``"
            self.message[title] = message

    def embed_constructor(self):
        self.first_message.set_title(
            "Active players"
            if self.table_name == "players_instant"
            else "Results for the day"
        )
        for i, (title, changes) in enumerate(self.message.items(), 1):
            if i > (self.stop_items / 2):
                self.second_message.add_embed_field(name=title, value=changes)
            else:
                self.first_message.add_embed_field(name=title, value=changes)

    def get_webhook_url(self):
        return (
            self.clan_credentials.webhook_players
            if self.table_name == "players_instant"
            else self.clan_credentials.webhook_day
        )
