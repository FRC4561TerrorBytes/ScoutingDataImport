import requests
import pandas as pd
import statbotics

HEADERS = {
    'X-TBA-Auth-Key': ""
}

eventKey = "2024nccmp"


def getTBATeamEvent(numTeams, eventKey, eventData):
    #API Call just to get team event data, works for OPR and component OPR, could also work on ranking
    url = "https://www.thebluealliance.com/api/v3/event/"+eventKey+"/"+eventData
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
    df.drop(columns=['team', 'year', 'event','offseason', 'event_name', 'state', 'country', 'district', 'type', 'week', 'status', 'num_teams' ], inplace=True) #Remove unneeded data
    return df
    

coprs = getTBATeamEvent(40, eventKey, "coprs")
oprs = getTBATeamEvent(40, eventKey, "oprs")

teamList = list(coprs.index.values)
epas = getStatboticsData(teamList, eventKey)

print(pd.concat([coprs,oprs,epas], axis=1))
