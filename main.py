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


# All time provided in UTC because of Repl.it uses its own timezone


class ScheduleUpdater:
    web_hooks = [WEBHOOK_DAY, WEBHOOK_SQUADRONS, WEBHOOK_PLAYERS, WEBHOOK_ABANDONED]
    clans_parsing_time = [
        '15:00', '15:30', '16:00', '16:30', '17:00', '17:30', '18:00', '18:30',
        '19:00', '19:30', '20:00', '20:30', '21:00', '21:30', '22:00'
    ]
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
                self.parsing_squadrons_thread,
                WEBHOOK_SQUADRONS, "squadrons"
            )
        self.schedule.every().day.at("22:15").do(
            self.parsing_squadrons_thread,
            WEBHOOK_DAY, "period_squadrons"

        )

    def schedule_daily_players_parsing(self):
        """
        Schedule a job for every day with publish check
        """
        self.schedule.every(1).minutes.do(
            self.parsing_players_thread,
            WEBHOOK_PLAYERS, 'players'
        )
        self.schedule.every().day.at("22:20").do(
            self.parsing_players_thread,
            WEBHOOK_DAY, 'period_players'
        )

    def start(self):
        """
        Initialize the schedule updater
        """
        print(f"Starting at time {self.time_now()}")
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

    def parsing_players_thread(self, webhook, table_name):
        """
        Initialize a thread for parsing players
        """
        print(f"Parsing players'{table_name}' at time {self.time_now()}")
        with ThreadPoolExecutor() as executor:
            executor.submit(PlayersLeaderboardUpdater,
                            webhook, table_name)

    def parsing_squadrons_thread(self, webhook, table_name):
        """
        Initialize a thread for parsing squadrons
        """
        print(f"Parsing squadrons '{table_name}' at time {self.time_now()}")
        with ThreadPoolExecutor() as executor:
            executor.submit(ClansLeaderboardUpdater,
                            webhook, table_name)

    def time_now(self):
        """
        Get current time in Kyiv/Europe
        """
        return datetime.datetime.now(self.local_timezone).strftime('%H:%M')


if __name__ == '__main__':
    scheduler = ScheduleUpdater()
    scheduler.start()
