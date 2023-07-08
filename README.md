# Schedule Spiders

This script schedules the execution of web scraping spiders using the `schedule` library in Python. It automates the process of running spiders at specified times to scrape data from websites.

## Prerequisites

- Python 3.x
- `schedule` library (install using `pip install schedule`)

## Usage

1. Clone the repository and navigate to the project directory.
2. Install the required dependencies: `pip install -r requirements.txt`.
3. Modify the `PY_PATH` variable in the script to match the path to your Python executable.
4. Run the script: `python schedule_spiders.py`.

## Scheduling Spider Execution

The script contains two main spider scheduling methods:

### 1. `schedule_daily_leader_board_parsing`

This method schedules the execution of the spider `LeaderBoardStats` with the argument `table_name=squadrons_daily`. The spider will be executed every day at 22:15.

Additionally, the spider will also be executed multiple times between 15:00 and 23:00, at intervals of 30 minutes. The table name for these executions is set to `squadrons_instant`.

### 2. `schedule_daily_players_parsing`

This method schedules the execution of the spider `PlayerStats` with the argument `table_name=players_daily`. The spider will be executed every day at 22:16.

In addition, the spider will be executed every minute without any specific time constraints, with the table name set to `players_instant`.

## Customization

You can customize the scheduling times and spider arguments according to your requirements by modifying the `schedule_daily_leader_board_parsing` and `schedule_daily_players_parsing` methods.

## Keeping the Script Running

The script uses the `keep_alive` function from the `background` module to keep the script running. This is useful if you are hosting the script on a server or a cloud platform. You can modify the `keep_alive` function in the `background` module to add any additional functionality you need to keep the script alive.

## Database and Discord Settings

The script relies on certain settings and functionalities provided by other modules. The following additional modules are used:

- `discord_webhook`: The `DiscordWebhook` and `DiscordEmbed` classes are used for sending messages to Discord webhooks.
- `settings`: The script imports various settings from the `settings` module, such as webhook URLs, database name, and other constants.

## AbstractWTPipeline

This class is an abstract base class (ABC) that provides common functionality for processing web scraping items related to War Thunder players and squadrons.

### Class Variables

- `players_tables`: A list of player-related table names in the database.
- `squadrons_tables`: A list of squadron-related table names in the database.

### Methods

- `__init__(self)`: Initializes the class instance by establishing a database connection, creating necessary tables, and setting up other variables.
- `process_item(self, item, spider)`: The abstract method for processing a web scraping item. Must be implemented in subclasses.
- `update_data(self, item)`: The abstract method for updating data in the database. Must be implemented in subclasses.
- `make_message(self, old_data, item)`: The abstract method for creating a message based on old and new data. Must be implemented in subclasses.
- `build_embed(self)`: The abstract method for building the Discord embed message. Must be implemented in subclasses.
- `send_message(self)`: Sends the Discord embed message to the specified webhook URL.
- `close_spider(self, spider)`: Performs necessary actions when closing the spider, such as committing database changes and sending messages.

## PlayersWTPipeline

This class extends the `AbstractWTPipeline` class and implements the necessary methods for processing player-related web scraping items.

### Methods

- `__init__(self)`: Initializes the class instance and sets up additional variables.
- `process_item(self, item, spider)`: Processes a player-related web scraping item.
- `update_data(self, item)`: Updates player data in the database.
- `make_message(self, old_data, item)`: Creates a message based on player data changes.
- `build_embed(self)`: Builds the Discord embed message for player-related data.
- `check_leavers(self)`: Checks for players who have left the clan and sends appropriate messages.
- `assign_roles(self)`: Assigns roles to players based on their data.

## ClansWTPipeline

This class extends the `AbstractWTPipeline` class and implements the necessary methods for processing squadron-related web scraping items.

### Methods

- `process_item(self, item, spider)`: Processes a squadron-related web scraping item.
- `update_data(self, item)`: Updates squadron data in the database.
- `make_message(self, old_data, item)`: Creates a message based on squadron data changes.
- `build_embed(self)`: Builds the Discord embed message for squadron-related data.

## License

This script is released under the [MIT License](https://opensource.org/licenses/MIT). Feel free to modify and use it according to your needs.
