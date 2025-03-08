# Scouting API Data Importing

Import data from TBA and Statbotics and output directly into a spreadsheet, the end goal is to populate a google sheet template or tableau dashboard for scouting meetings

## Install Dependencies

First, clone this repository to your local machine. Next, install dependencies with: `pip install -r requirements.txt` when run in the the cloned repository.

## Run The Script
In the directory where the script is located call:

`Python scoutingDataImport.py $eventKey`

For example, this will gather data for the 2025 PCH District Gainsville event:

`Python scoutingDataImport.py 2025gagai`

Once completed, the output file will be in the same folder and named for the event used. Event keys are easily gathered from The Blue Alliance event pages, with URLs formatted like `https://www.thebluealliance.com/event/2025inmis` where the event key is the last entry

### TBA API 
[TBA API](https://www.thebluealliance.com/apidocs/v3) is used to get data on component OPRs from all teams at an event

### Statbotics API
[Statbotics API](https://www.statbotics.io/api/python) is used to get data on EPA from teams at an event. 

### Dependencies
* [Pandas](https://pandas.pydata.org/)
* [Statbotics Python API](https://www.statbotics.io/api/python)
* [requests](https://pypi.org/project/requests/ )
* [openpyxl](https://pypi.org/project/openpyxl/)

