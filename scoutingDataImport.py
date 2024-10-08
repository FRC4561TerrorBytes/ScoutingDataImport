import requests
import pandas as pd
import statbotics

HEADERS = {
    'X-TBA-Auth-Key': "xgGoJmaz1XxRLpMGBF7AU16RBi1Lk48UpkLE2jMbSE0pyyTzBwyQYt1qwhc7xSk5"
}


def getComponentOPRs(numTeams, eventKey):
    #API Call just to get component OPR data
    url = "https://www.thebluealliance.com/api/v3/event/"+eventKey+"/coprs"
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

# def getStatboticsData(eventKey):



# coprs = getComponentOPRs(40, "2024nccmp")
