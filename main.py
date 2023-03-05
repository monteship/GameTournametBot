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

def time_now():
    """
    Get current time in Kyiv/Europe
    """
    return datetime.datetime.now(timezone('Europe/Kyiv')).strftime('%H:%M')


class ScheduleUpdater:
    clans_parsing_time = [
        '15:00', '15:30', '16:00', '16:30', '17:00', '17:30', '18:00', '18:30',
        '19:00', '19:30', '20:00', '20:30', '21:00', '21:30', '22:00'
    ]

    def __init__(self):
        self.schedule = schedule
        self.schedule_daily_jobs()

    def schedule_daily_jobs(self):
        """
        Schedule daily jobs
        """
        self.schedule_daily_squadrons_parsing()
        self.schedule_daily_players_parsing()

    def schedule_daily_squadrons_parsing(self):
        """
        Iterate through all clans_parsing_time values and schedule a job for each one
        """
        for parsing_time in self.clans_parsing_time:
            self.schedule.every().day.at(parsing_time).do(
                self.parsing_squadrons_thread
            )
        self.schedule.every().day.at("22:15").do(
            self.parsing_squadrons_partial_thread
        )

    def schedule_daily_players_parsing(self):
        """
        Schedule a job for every day with publish check
        """
        self.schedule.every(1).minutes.do(
            self.parsing_players_thread, True
        )
        self.schedule.every().day.at("15:00").do(
            self.parsing_players_partial_thread, False
        )
        self.schedule.every().day.at("22:20").do(
            self.parsing_players_partial_thread, True
        )

    def start(self):
        """
        Initialize the schedule updater
        """
        try:
            print(f"Starting at time {time_now()}")
            keep_alive()
            with Database(initialize=True) as conn:
                conn.create_databases()
            self.clean_webhooks()
            while True:
                self.schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            print(f"Manually stopped at time {time_now()}")

    def clean_webhooks(self):
        """
        Clean all webhooks for no reason
        """
        web_hooks = [WEBHOOK_DAY, WEBHOOK_SQUADRONS, WEBHOOK_PLAYERS, WEBHOOK_ABANDONED]
        for webhook_url in web_hooks:
            DiscordWebhook(url=webhook_url).remove_embeds()

    def parsing_players_thread(self, publish):
        """
        Initialize a thread for parsing players for instant updates
        """
        print(f"Parsing players at time {time_now()}")
        with ThreadPoolExecutor() as executor:
            executor.submit(PlayersLeaderboardUpdater,
                            WEBHOOK_PLAYERS, 'players', publish)

    def parsing_squadrons_thread(self):
        """
        Initialize a thread for parsing squadrons for instant updates
        """
        print(f"Parsing squadrons at time {time_now()}")
        with ThreadPoolExecutor() as executor:
            executor.submit(ClansLeaderboardUpdater,
                            WEBHOOK_SQUADRONS, "squadrons")

    def parsing_players_partial_thread(self, publish):
        """
        Initialize a thread for parsing players for day statistics
        """
        print(f"Parsing players partial {publish} at time {time_now()}")
        with ThreadPoolExecutor() as executor:
            executor.submit(PlayersLeaderboardUpdater,
                            WEBHOOK_DAY, "period_players", publish)

    def parsing_squadrons_partial_thread(self):
        """
        Initialize a thread for parsing squadrons for day statistics
        """
        print(f"Parsing squadrons partial at time {time_now()}")
        with ThreadPoolExecutor() as executor:
            executor.submit(ClansLeaderboardUpdater,
                            WEBHOOK_DAY, "period_squadrons")


if __name__ == '__main__':
    scheduler = ScheduleUpdater()
    scheduler.start()
