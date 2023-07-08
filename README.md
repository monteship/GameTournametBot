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

## Note

Make sure to set the correct Python path in the `PY_PATH` variable to ensure the spiders are executed using the correct Python interpreter.

## License

This script is released under the [MIT License](https://opensource.org/licenses/MIT). Feel free to modify and use it according to your needs.
