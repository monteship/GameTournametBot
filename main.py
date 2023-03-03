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


def time_now():
    return datetime.datetime.now(timezone('Europe/Kiev')).strftime('%H:%M')


class Scheduler:
    clans_parsing_time = [
        '17:00', '17:30', '18:00', '18:30', '19:00', '19:30', '20:00', '20:30',
        '21:00', '21:30', '22:00', '22:30', '23:00', '23:30', '00:00'
    ]

    def __init__(self):
        self.schedule = schedule
        self.schedule.every(1).minutes.do(self.parsing_players_thread, True)
        self.schedule_daily_jobs()

    def schedule_daily_jobs(self):
        self.schedule_daily_squadrons_parsing()
        self.schedule_daily_no_publish_checks()
        self.schedule_daily_publish_results_checks()

    def schedule_daily_squadrons_parsing(self):
        for parsing_time in self.clans_parsing_time:
            self.schedule.every().day.at(parsing_time).do(self.parsing_squadrons_thread, True)

    def schedule_daily_no_publish_checks(self):
        self.schedule.every().day.at("16:50").do(
            self.parsing_squadrons_partial_thread, False
        )
        self.schedule.every().day.at("17:00").do(
            self.parsing_players_partial_thread, False
        )

    def schedule_daily_publish_results_checks(self):
        self.schedule.every().day.at("00:15").do(
            self.parsing_squadrons_partial_thread, True
        )
        self.schedule.every().day.at("00:20").do(
            self.parsing_players_partial_thread, True
        )

    def start(self):
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
        web_hooks = [WEBHOOK_DAY, WEBHOOK_SQUADRONS, WEBHOOK_PLAYERS, WEBHOOK_ABANDONED]
        for webhook_url in web_hooks:
            DiscordWebhook(url=webhook_url).remove_embeds()

    def parsing_players_thread(self, publish):
        print(f"Parsing players at time {time_now()}")
        with ThreadPoolExecutor() as executor:
            executor.submit(PlayersLeaderboardUpdater,
                            WEBHOOK_PLAYERS, 'players', publish)

    def parsing_squadrons_thread(self, publish_changes):
        print(f"Parsing squadrons at time {time_now()}")
        with ThreadPoolExecutor() as executor:
            executor.submit(ClansLeaderboardUpdater,
                            WEBHOOK_SQUADRONS, "squadrons", publish_changes)

    def parsing_players_partial_thread(self, publish):
        print(f"Parsing players partial {publish} at time {time_now()}")
        with ThreadPoolExecutor() as executor:
            executor.submit(PlayersLeaderboardUpdater,
                            WEBHOOK_DAY, "period_players", publish)

    def parsing_squadrons_partial_thread(self, publish_changes):
        print(f"Parsing squadrons partial {publish_changes} at time {time_now()}")
        with ThreadPoolExecutor() as executor:
            executor.submit(ClansLeaderboardUpdater,
                            WEBHOOK_DAY, "period_squadrons", publish_changes)


if __name__ == '__main__':
    scheduler = Scheduler()
    scheduler.start()
