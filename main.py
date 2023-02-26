import datetime
from threading import Thread
import time
import schedule
from discord_webhook import DiscordWebhook
from pytz import timezone

from config import WEBHOOK_PLAYERS, PLAYERS_EMBEDS, DAY_START_EMBEDS, WEBHOOK_DAY, \
    DAY_START_EMBEDS, DAY_END_EMBEDS, WEBHOOK_SQUADRONS, SQUADRONS_PARSING_TIME, SQUAD_EMBEDS, WEBHOOK_ABANDONED
from database import Database
from player import PlayersLeaderboardUpdater
from squadron import ClansLeaderboardUpdater
from background import keep_alive


def parsing_players_thread():
    Thread(target=PlayersLeaderboardUpdater,
           args=[WEBHOOK_PLAYERS, 'players']).start()


def parsing_players_partial_thread():
    Thread(target=PlayersLeaderboardUpdater,
           args=[WEBHOOK_DAY, "period_players"]).start()


def parsing_squadrons_day_start_thread():
    Thread(target=ClansLeaderboardUpdater,
           args=[WEBHOOK_DAY, "period_squadrons"]).start()


def parsing_squadrons_day_end_thread():
    Thread(target=ClansLeaderboardUpdater,
           args=[WEBHOOK_DAY, "period_squadrons"]).start()


def parsing_squadrons_thread():
    Thread(target=ClansLeaderboardUpdater,
           args=[WEBHOOK_SQUADRONS, "squadrons"]).start()


def clean_webhooks():
    WEB_HOOKS = [WEBHOOK_DAY, WEBHOOK_SQUADRONS, WEBHOOK_PLAYERS, WEBHOOK_ABANDONED]
    for count, webhook_url in enumerate(WEB_HOOKS, 1):
        webhook = DiscordWebhook(url=webhook_url)
        webhook.remove_embeds()
        print(f"Webhook {count} cleaned!")


def time_checker():
    """
    Build time constant, check if it's time to start parsing
    """
    kiev_time = datetime.datetime.now(timezone('Europe/Kiev'))
    hours = kiev_time.hour
    minutes = kiev_time.minute
    current_time = str(hours * 60 + minutes)
    print(current_time)
    if current_time in SQUADRONS_PARSING_TIME:
        parsing_squadrons_thread()
    if current_time == '960':  # Run at 16:00 GMT+2
        parsing_squadrons_day_start_thread()
    if current_time == '984':  # Run at 16:40 GMT+2
        parsing_players_partial_thread()
    if current_time == '1443':  # Run at 00:05 GMT+2 next day
        parsing_squadrons_day_end_thread()
    if current_time == '1446':  # Run at 00:10 GMT+2 next day
        parsing_players_partial_thread()
    parsing_players_thread()  # Run every 1 minute


def main():
    """
    Main function
    """
    try:
        keep_alive()
        with Database(initialize=True) as conn:
            conn.create_databases()
            print("Database created")
        """parsing_squadrons_thread()
        parsing_squadrons_day_start_thread()
        parsing_players_partial_thread()"""
        clean_webhooks()
        schedule.every(60).seconds.do(time_checker)
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        print("Manually stopped")


if __name__ == '__main__':
    main()
