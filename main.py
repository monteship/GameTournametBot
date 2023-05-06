import datetime
import time

import schedule
from discord_webhook import DiscordWebhook
from pytz import timezone

from config import WEBHOOK_PLAYERS, WEBHOOK_DAY, WEBHOOK_SQUADRONS, WEBHOOK_ABANDONED
from database import Database
from player import PlayersLeaderboardUpdater
from squadron import ClansLeaderboardUpdater
from background import keep_alive
from concurrent.futures import ThreadPoolExecutor
import logging
from rich.logging import RichHandler

logging.basicConfig(
    level="INFO",
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True, tracebacks_show_locals=True)]
)

log = logging.getLogger("rich")


# All time provided in UTC because of Repl.it uses its own timezone


def parsing_players_thread(webhook, table_name):
    """
    Initialize a thread for parsing players
    """
    log.info("Parsing players [bold]'{}'[/bold]".format(table_name), extra={"markup": True})
    with ThreadPoolExecutor() as executor:
        executor.submit(PlayersLeaderboardUpdater, webhook, table_name)


def parsing_squadrons_thread(webhook, table_name):
    """
    Initialize a thread for parsing squadrons
    """
    log.info("Parsing squadrons [bold]'{}'[/bold]".format(table_name), extra={"markup": True})
    with ThreadPoolExecutor() as executor:
        executor.submit(ClansLeaderboardUpdater, webhook, table_name)


class ScheduleUpdater:
    web_hooks = [WEBHOOK_DAY, WEBHOOK_SQUADRONS, WEBHOOK_PLAYERS, WEBHOOK_ABANDONED]
    clans_parsing_time = [f"{hour}:{minute}" for hour in range(15, 23) for minute in ["00", "30"]]
    local_timezone = timezone('Europe/Kyiv')

    def __init__(self):
        self.schedule = schedule
        self.schedule_daily_squadrons_parsing()
        self.schedule_daily_players_parsing()

    def schedule_daily_squadrons_parsing(self):
        """
        Iterate through all clans_parsing_time values and schedule a job for each one
        """
        for parsing_time in self.clans_parsing_time:
            self.schedule.every().day.at(parsing_time).do(
                parsing_squadrons_thread,
                WEBHOOK_SQUADRONS, "squadrons"
            )
        self.schedule.every().day.at("22:15").do(
            parsing_squadrons_thread,
            WEBHOOK_DAY, "period_squadrons"

        )

    def schedule_daily_players_parsing(self):
        """
        Schedule a job for every day with publish check
        """
        self.schedule.every().day.at("22:20").do(
            parsing_players_thread,
            WEBHOOK_DAY, 'period_players'
        )
        self.schedule.every(1).minutes.do(
            parsing_players_thread,
            WEBHOOK_PLAYERS, 'players'
        )

    def start(self):
        """
        Initialize the schedule updater
        """
        log.info("[bold green blink]Starting...[/]", extra={"markup": True})
        keep_alive()
        with Database(initialize=True) as conn:
            conn.create_databases()
        self.clean_webhooks()
        while True:
            self.schedule.run_pending()
            time.sleep(30)

    def clean_webhooks(self):
        """
        Clean all webhooks for no reason
        """
        for webhook_url in self.web_hooks:
            webhook = DiscordWebhook(url=webhook_url)
            webhook.remove_embeds()


if __name__ == '__main__':
    scheduler = ScheduleUpdater()
    scheduler.start()
