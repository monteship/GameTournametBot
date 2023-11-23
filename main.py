import time

import schedule

from background import keep_alive
from database import SQLDatabase
from notify import LeaderboardNotifier, PlayersNotifier, inform_leaving
from scrapers import (
    ClansLeaderboardScraper,
    ClanLeaderboardItem,
    GlobalLeaderboardItem,
    PlayersLeaderboardScraper,
)
from settings import CLANS


class ScheduleSpiders:
    def __init__(self):
        self.schedule = schedule
        self.db = SQLDatabase()
        self.schedule_daily_leader_board_parsing()
        self.schedule_daily_players_parsing()

    def update_leaderboard(self, table_name):
        scraper = ClansLeaderboardScraper()
        leaderboard_item: GlobalLeaderboardItem = scraper.get_leaderboard
        has_changes = self.db.update_leaderboard_data(leaderboard_item, table_name)
        if not has_changes:
            return
        for clan in CLANS:
            notify = LeaderboardNotifier(clan, has_changes, table_name)
            notify.process()

    def update_players(self, table_name):
        scraper = PlayersLeaderboardScraper()
        players_item: ClanLeaderboardItem = scraper.get_leaderboard
        has_changes, leavers = self.db.update_players_data(players_item, table_name)
        for clan, changes in has_changes.items():
            notify = PlayersNotifier(CLANS[clan], has_changes, table_name)
            notify.process()
        for leaver in leavers:
            inform_leaving(leaver, CLANS[leaver.clan])

    def schedule_daily_leader_board_parsing(self):
        self.schedule.every().day.at("22:15").do(
            self.update_leaderboard(table_name="squadrons_daily")
        )

        clans_parsing_time = [
            f"{hour}:{minute}" for hour in range(15, 23) for minute in ["00", "30"]
        ]
        for parsing_time in clans_parsing_time:
            self.schedule.every().day.at(parsing_time).do(
                self.update_leaderboard(table_name="squadrons_instant")
            )

    def schedule_daily_players_parsing(self):
        self.schedule.every().day.at("22:16").do(
            self.update_players(table_name="players_daily")
        )

        self.schedule.every().minute.do(
            self.update_players(table_name="players_instant")
        )

    def start(self):
        keep_alive()
        while True:
            self.schedule.run_pending()
            print("Sleeping for 30 seconds...")
            time.sleep(30)


if __name__ == "__main__":
    scheduler = ScheduleSpiders()
    scheduler.start()
