import sqlite3
from typing import Optional, List

import pydantic

from scrapers import ClanLeaderboardItem, GlobalLeaderboardItem, ScrapedPlayerItem


class Leaver(pydantic.BaseModel):
    nick: str
    rating: str
    date_joined: str
    clan: str

    def __init__(self, nick: str, rating: str, date_joined: str, clan: str):
        super().__init__()
        self.nick = nick
        self.rating = rating
        self.date_joined = date_joined
        self.clan = clan


class SQLDatabase:
    players_tables = [
        "players_daily",
        "players_instant",
    ]
    squadrons_tables = [
        "squadrons_daily",
        "squadrons_instant",
    ]

    def __init__(self):
        self.con = sqlite3.connect("wtstats.sqlite")
        self.cur = self.con.cursor()
        self._create_tables()
        self.leavers = dict()

    def update_leaderboard_data(
        self, leaderboard_item: GlobalLeaderboardItem, table: str
    ) -> Optional[list]:
        has_changes = []
        for clan_item in leaderboard_item.clans:
            self.cur.execute(
                f"SELECT rank, members, rating, kills_to_death FROM {table} WHERE tag = ?",
                (clan_item.tag,),
            )
            stored_data = self.cur.fetchone()
            if not stored_data:
                self.cur.execute(
                    f"INSERT INTO {table} VALUES (?, ?, ?, ?, ?, ?)",
                    (str(clan_item)),
                )
            else:
                self.cur.execute(
                    f"UPDATE {table} SET name = ?, rank = ?, members = ?, rating = ?, kills_to_death = ? WHERE tag = ?",
                    (str(clan_item)),
                )
                has_changes.append((stored_data, clan_item))
        self.con.commit()
        return has_changes

    def update_players_data(
        self,
        leaderboard_item: ClanLeaderboardItem,
        table: str,
    ) -> (dict, List[Leaver]):
        has_changes = dict()
        leavers = self.check_leavers(leaderboard_item.players)
        for player_item in leaderboard_item.players:
            self.cur.execute(
                f"SELECT nick, rating, activity, clan FROM {table} WHERE nick = ?",
                (player_item.nick,),
            )
            stored_data = self.cur.fetchone()
            if not stored_data:
                self.cur.execute(
                    f"INSERT INTO {table} VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        player_item.nick,
                        player_item.rating,
                        player_item.activity,
                        player_item.role,
                        player_item.date_joined,
                        player_item.clan,
                    ),
                )
            else:
                self.cur.execute(
                    f"UPDATE {table} SET rating = ?, activity = ?, role = ?, date_joined = ?, clan = ? WHERE nick = ?",
                    (
                        player_item.rating,
                        player_item.activity,
                        player_item.role,
                        player_item.date_joined,
                        player_item.clan,
                        player_item.nick,
                    ),
                )
                if int(stored_data[1]) != int(player_item.rating):
                    has_changes[player_item.clan].append((stored_data, player_item))
        self.con.commit()
        return has_changes, leavers

    def check_leavers(self, players: list[ScrapedPlayerItem]) -> list:
        self.cur.execute("SELECT nick, rating, date_joined, clan FROM players_instant")
        database_members = self.cur.fetchall()
        leavers = [
            Leaver(*member)
            for member in database_members
            if member[0] not in [player.nick for player in players]
        ]
        if len(leavers) < 10:
            for leaver in leavers:
                for table_name in self.players_tables:
                    self.cur.execute(
                        f"DELETE FROM {table_name} WHERE nick = ?", (leaver[0],)
                    )
        self.con.commit()
        return leavers

    def _create_tables(self):
        for table_name in self.players_tables:
            self.cur.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                       "nick" TEXT, 
                       "rating" INTEGER, 
                       "activity" INTEGER, 
                       "role" TEXT, 
                       "date_joined" DATE, 
                       "clan" TEXT
                       )
                   """
            )
        for table_name in self.squadrons_tables:
            self.cur.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                   "tag" TEXT, 
                   "rank" INTEGER, 
                   "name" TEXT, 
                   "members" INTEGER, 
                   "rating" INTEGER, 
                   "kills_to_death" INTEGER
                   )
                   """
            )
        self.con.commit()


if __name__ == "__main__":
    db = SQLDatabase()
