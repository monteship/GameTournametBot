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

```python
schedule_daily_leader_board_parsing()
