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

    def delete_data(self, name, table_name: str):
        """
        Try to delete a player from the database
        """
        self.execute(f"DELETE FROM {table_name} WHERE name = '{name}'")
        self.commit()

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
