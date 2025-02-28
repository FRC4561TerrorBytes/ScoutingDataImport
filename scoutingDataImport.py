import argparse
import ast
import requests
import pandas as pd
import statbotics
import openpyxl

HEADERS = {
    'X-TBA-Auth-Key': "xgGoJmaz1XxRLpMGBF7AU16RBi1Lk48UpkLE2jMbSE0pyyTzBwyQYt1qwhc7xSk5"
}


# gSheetAPIKey = "AIzaSyDUK48jMpr0KcJYiy8U-bI1Q0NZDa1MYSg"
# sheetID = "1ALwEwxlfVpOaDqcByMtsRlJOcqARDud4bCfM0cDZL-E"
# sheetName = "Sheet1"
# outputSheetURL = "https://sheets.googleapis.com/v4/spreadsheets/"+sheetID+"/values/"+sheetName+"!A1:Z?alt=json&key="+gSheetAPIKey
# print(outputSheetURL)

# Get the number of teams at an event, helpful for cleaning up the TBA API import. 
def getNumTeams(eventKey):
    # Retrieve rankings data
    url = "https://www.thebluealliance.com/api/v3/event/"+eventKey+"/rankings"
    data = requests.get(url, headers=HEADERS).json()
    print(data)
    return len(data['rankings']) #Return number of teams that competed in matches, avoids teams that just presented at DCMPs

def getTBATeamEvent(numTeams, eventKey, eventData):
    #API Call just to get team event data, works for OPR and component OPR, could also work on ranking
    url = "https://www.thebluealliance.com/api/v3/event/"+eventKey+"/"+ eventData
    data = requests.get(url, headers=HEADERS).json()
    df = pd.json_normalize(data).transpose()

    # Create lists of unique team numbers and component OPR types
    colNames = []
    teamNumbers = []
    for col in df.index :
        entry = col.split(".")
        colNames.append(entry[0])
        teamNumbers.append(entry[1])
    
    teamNumbers = teamNumbers[0:numTeams]
    colNames = sorted(set(colNames))

    df2 = pd.DataFrame(columns=colNames, index=teamNumbers) #Preparing output dataframe
    
    # Move data from the long but 1 column dataframe to a team x ComponentOPR  df for ease of use
    for col in df2.columns :
        currentcol = df[[col in s for s in df.index]]

        # Filtering out some weird API data that is more nested than spec, could fix this if desired
        if len(currentcol.index) > numTeams :
            continue

        currentcol = currentcol.set_axis(teamNumbers,axis=0)
        currentcol.columns = [col]
        currentcol = currentcol[col].round(3)
        df2[col] = currentcol
    
    return df2

def getStatboticsData(teamList, eventKey):

    # Create statbotics API object
    sb = statbotics.Statbotics()

    # Iterate through each team and pull data for a given event
    listOfTeams = []
    for team in teamList :
        listOfTeams.append(sb.get_team_event(int(team[3:]), eventKey))

    # Create dataframe from a list of dicts
    df = pd.DataFrame.from_records(listOfTeams, index=teamList)
    df.drop(columns=['team', 'year', 'event', 'event_name', 'state', 'country', 'district', 'type', 'week', 'status', 'time','first_event' ], inplace=True) #Remove unneeded data
    
    epa_flat = df['epa'].apply(flatten_record)
    record_flat = df['record'].apply(flatten_record)
    
    epa_df = pd.DataFrame(epa_flat.tolist(), index=df.index)
    record_df = pd.DataFrame(record_flat.tolist(), index=df.index)

    df_expanded = pd.concat([df.drop(columns=['epa', 'record']), epa_df.add_prefix("epa_"), record_df], axis=1)
    df_expanded.drop(columns=['qual_num_teams','epa_unitless','elim_wins','elim_losses','elim_ties','elim_count','elim_winrate'
                              ,'elim_alliance',	'elim_is_captain',	'total_wins'
                              ,'total_losses',	'total_ties', 'total_count', 'total_winrate'], inplace=True)
    return df_expanded

def flatten_record(record_dict):
    if isinstance(record_dict, str):
        record_dict = ast.literal_eval(record_dict)  # Convert string representation to dictionary
    record_flat = {}
    for key, value in record_dict.items():
        if isinstance(value, dict):
            for sub_key, sub_value in value.items():
                record_flat[f"{key}_{sub_key}"] = sub_value
        else:
            record_flat[key] = value
    return record_flat
    

#Designed to run in Neptyne google sheets editor, google cloud API seems kind of annoying and poorly documented
def runMe(eventKey):

    numTeams = getNumTeams(eventKey)
    coprs = getTBATeamEvent(numTeams, eventKey, "coprs")
    oprs = getTBATeamEvent(numTeams, eventKey, "oprs")

    teamList = list(coprs.index.values)
    epas = getStatboticsData(teamList, eventKey)

    fullData = pd.concat([coprs,oprs, epas], axis=1)
    fullData.index.name = 'Team'
    fullData.to_excel('Data.xlsx', sheet_name='WeekZeroData', index=True)
    #A1 = fullData

def main():
    parser = argparse.ArgumentParser(description="Process an event key.")
    parser.add_argument('-e', '--eventKey', required=True)
    
    args = parser.parse_args()
    
    print(f"Received event key: {args.eventKey}")

    runMe(args.eventKey)

if __name__ == "__main__":
    main()