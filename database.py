import sqlite3
from datetime import datetime

from config import DB_PATH


class Database:
    """
    Custom database class
    """
    player_tables = "players", "period_players"
    squadrons_tables = "squadrons", "period_squadrons"

    def __init__(self, table_name: str = None):
        self.table_name = table_name
        self.conn = sqlite3.connect(DB_PATH)
        self.cursor = self.conn.cursor()
        if table_name is None:
            print("Creating tables")
            self.create_databases()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.conn.commit()
        self.conn.close()

    def set_ranks(self):
        """
        Sets the ranks of the players in the database
        """
        try:
            self.cursor.execute(f"""UPDATE {self.table_name}
                            SET rank = (
                                SELECT COUNT(*) + 1
                                FROM players p2
                                WHERE p2.points > {self.table_name}.points
                                        )
                            WHERE {self.table_name}.points IS NOT NULL;""")
        except sqlite3.Error as err:
            print(f"Error setting ranks: {err}")
        finally:
            self.conn.commit()

    def delete_player(self, name, table_name=None):
        """
        Try to delete a player from the database
        """
        if table_name is None:
            table_name = self.table_name
        try:
            self.cursor.execute(f"DELETE FROM {table_name} WHERE name = '{name}'")
        except sqlite3.Error as err:
            print(f"Error deleting player: {err}")
        finally:
            self.conn.commit()

    def insert_player(self, player):
        """
        Insert a player into the database
        """
        self.cursor.execute(
            f"INSERT INTO {self.table_name} (name, points, role, date_join) VALUES (?, ?, ?, ?)",
            (player.name, player.points, player.role, player.date_join))
        self.conn.commit()

    def update_player(self, player):
        """
        Update a player in the database
        """
        try:
            self.delete_player(player.name)
        except sqlite3.Error:
            pass
        finally:
            self.insert_player(player)
        self.conn.commit()

    def check_quit(self, personal) -> tuple[str, int, datetime] | None:
        """
        Parses the players from the leaderboard,
        checks if they left and adds them to the Discord embed
        """
        self.cursor.execute("SELECT name FROM players")
        db_personal = [person[0] for person in self.cursor.fetchall()]
        quit_persons = set(db_personal) - set(personal)
        if quit_persons:
            for person in quit_persons:

                self.cursor.execute(
                    f"SELECT name, points, date_join FROM players WHERE name = '{person}'")
                try:
                    name, points, date = self.cursor.fetchall()[0]
                    print(name, points, date)
                    for table in self.player_tables:
                        self.delete_player(person, table)
                    return name, points, date
                except sqlite3.Error:
                    return None
        return None

    def create_databases(self):
        """
        Creates the database if it doesn't exist
        """
        for table_name in self.player_tables:
            self.cursor.execute(
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
            self.cursor.execute(
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

        self.conn.commit()
        self.conn.close()
