import sqlite3
from datetime import datetime

from config import DB_PATH


class Database:
    """
    Custom database class
    """
    player_tables = "players", "period_players"
    squadrons_tables = "squadrons", "period_squadrons"

    def __init__(self, initialize=False):
        self._conn = sqlite3.connect(DB_PATH)
        self._cursor = self._conn.cursor()
        if initialize is True:
            self.create_databases()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    @property
    def connection(self):
        return self._conn

    @property
    def cursor(self):
        return self._cursor

    def commit(self):
        self.connection.commit()

    def close(self, commit=True):
        if commit:
            self.commit()
        self.connection.close()

    def execute(self, sql, params=None):
        self.cursor.execute(sql, params or ())

    def fetchall(self):
        return self.cursor.fetchall()

    def fetchone(self):
        return self.cursor.fetchone()

    def query(self, sql, params=None):
        self.cursor.execute(sql, params or ())
        return self.fetchall()

    def set_ranks(self, table_name: str):
        """
        Sets the ranks of the players in the database
        """
        self.execute(f"""UPDATE {table_name}
                        SET rank = (
                            SELECT COUNT(*) + 1
                            FROM players p2
                            WHERE p2.points > {table_name}.points
                                    )
                        WHERE {table_name}.points IS NOT NULL;""")
        self.commit()

    def delete_data(self, name, table_name: str):
        """
        Try to delete a player from the database
        """
        self.execute(f"DELETE FROM {table_name} WHERE name = '{name}'")
        self.commit()

    def insert_player(self, player, table_name: str):
        """
        Insert a player into the database
        """
        self.execute(f"INSERT INTO {table_name} (name, points, role, date_join) VALUES (?, ?, ?, ?)",
                     (player.name, player.points, player.role, player.date_join))
        self.commit()

    def insert_clan(self, clan, table_name: str):
        """
        Insert a clan into the database
        """
        self.execute(f"INSERT INTO {table_name} (name, rank, points, k_d, players) VALUES(?, ?, ?, ?, ?)",
                     (clan.name, clan.rank, clan.points, clan.k_d, clan.players_count))
        self.commit()

    def check_quit(self, personal) -> tuple[str, int, datetime] | None:
        """
        Parses the players from the leaderboard,
        checks if they left and adds them to the Discord embed
        """
        self.execute("SELECT name FROM players")
        query_data = self.fetchone()
        db_personal = [person for person in query_data]
        quit_persons = set(db_personal) - set(personal)
        if quit_persons:
            for person in quit_persons:
                query_data = self.query(
                    f"SELECT name, points, date_join FROM players WHERE name = '{person}'")
                try:
                    name, points, date = query_data[0]
                    for table in self.player_tables:
                        self.delete_data(person, table)
                    return name, points, date
                except sqlite3.Error:
                    return None
        return None

    def create_databases(self):
        """
        Creates the database if it doesn't exist
        """
        for table_name in self.player_tables:
            self.execute(
                f'''
                CREATE TABLE IF NOT EXISTS {table_name} 
                (
                    "name" TEXT,
                    "points" INTEGER,
                    "role" TEXT,
                    "date_join" TEXT,
                    "rank" INTEGER
                )
                ''')
        for table_name in self.squadrons_tables:
            self.execute(
                f'''
                CREATE TABLE IF NOT EXISTS {table_name} 
                (
                    "name" TEXT,
                    "rank" INTEGER,
                    "points" INTEGER,
                    "k_d" INTEGER,
                    "players" INTEGER
                )
                ''')
