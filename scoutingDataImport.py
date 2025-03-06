import argparse
import ast
import requests
import pandas as pd
import statbotics

HEADERS = {
    'X-TBA-Auth-Key': "xgGoJmaz1XxRLpMGBF7AU16RBi1Lk48UpkLE2jMbSE0pyyTzBwyQYt1qwhc7xSk5"
}

def getEventData(eventKey):
    url = "https://www.thebluealliance.com/api/v3/event/" + eventKey +"/simple"
    data = requests.get(url, headers=HEADERS).json()
    print('Gathering data for: ' + str(data['year']) + " " + data['name'] + "\n")
    
    return str(data['year']) + data['name']

# Get the number of teams at an event, helpful for cleaning up the TBA API import. 
def getNumTeams(eventKey):
    # Retrieve rankings data
    url = "https://www.thebluealliance.com/api/v3/event/"+eventKey+"/rankings"
    data = requests.get(url, headers=HEADERS).json()
    return len(data['rankings']) #Return number of teams that competed in matches, avoids teams that just presented at DCMPs

def getRankings(eventKey):
    url = "https://www.thebluealliance.com/api/v3/event/" + eventKey +"/rankings"
    data = requests.get(url, headers=HEADERS).json()
    data = data['rankings']

    df = pd.json_normalize(data)

    # Expand 'sort_orders' list into separate columns
    sort_orders_df = df['sort_orders'].apply(pd.Series)
    sort_orders_df.columns = [f'sort_order_{i+1}' for i in range(len(sort_orders_df.columns))]
    
    # Merge expanded columns back into main DataFrame and drop the original 'sort_orders' column
    df = df.drop(columns=['sort_orders']).join(sort_orders_df)

    df.set_index('team_key', inplace=True)

    df_reorder = df.loc[:,['sort_order_1', 'sort_order_2', 'sort_order_3', 'sort_order_4', 'sort_order_5', 'sort_order_6', 'record.wins', 'record.losses', 'record.ties', 'dq', 'matches_played', 'extra_stats']]
    df_reorder['extra_stats'] = df_reorder['extra_stats'].explode()
    df_reorder = df_reorder.rename(columns={'extra_stats': 'Ranking Points', 'sort_order_1' : 'Ranking score',
                                            'sort_order_2': 'Avg Coop', 'sort_order_3': 'Average match points', 'sort_order_4': 'Average Auto points', 
                                            'sort_order_5': 'Average Barge points'})

    df_reorder = df_reorder.drop(columns=['sort_order_6'])
    return df_reorder

def getTBATeamEvent(numTeams, eventKey, eventData):
    #API Call just to get team event data, works for OPR and component OPR
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

    #Get rid of more statbotics data we don't care about. 
    df_expanded.drop(columns=['qual_num_teams','epa_unitless','elim_wins','elim_losses','elim_ties','elim_count','elim_winrate'
                              ,'elim_alliance',	'elim_is_captain',	'total_wins'
                              ,'total_losses',	'total_ties', 'total_count', 'total_winrate', 'district_points','epa_total_points_mean', 'epa_total_points_sd',
                              'epa_norm', 'epa_conf'], inplace=True)
    return df_expanded

#Some of the statbotics data is returned as nested dicts, this flattens them 
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

#Only runs locally for now, google cloud api credential process is confusing
def runMe(eventKey):
    workbookName = getEventData(eventKey)
    numTeams = getNumTeams(eventKey)
    coprs = getTBATeamEvent(numTeams, eventKey, "coprs")
    oprs = getTBATeamEvent(numTeams, eventKey, "oprs")
    rankings = getRankings(eventKey)

    teamList = list(coprs.index.values)
    epas = getStatboticsData(teamList, eventKey)


    #Add team names to columns from TBA data for ease of viewing
    coprs.insert(0, 'team_name', epas['team_name'])
    oprs.insert(0, 'team_name', epas['team_name'])
    rankings.insert(0, 'team_name', epas['team_name'])


    #Write OPR, COPR, EPA data to different sheets, this takes longer but is more human readable
    with pd.ExcelWriter(workbookName.replace(" ", "") + '.xlsx') as writer: 
        oprs.to_excel(writer, sheet_name='OPRs', index=True)
        coprs.to_excel(writer, sheet_name='Component OPRs', index=True)
        epas.to_excel(writer, sheet_name='EPA', index=True)
        rankings.to_excel(writer, sheet_name='Rankings', index=True)

    print("Finished gathering data, view data in the " + workbookName.replace(" ", "") + ".xlsx file")

def main():
    parser = argparse.ArgumentParser(description="Process an event key.")
    parser.add_argument('eventKey')
    
    args = parser.parse_args()
    
    #API endpoints for eventkey are case sensitive
    runMe(args.eventKey.lower())

if __name__ == "__main__":
    main()