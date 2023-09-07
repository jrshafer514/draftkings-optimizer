import pandas as pd
from bs4 import BeautifulSoup
import requests
from pydfs_lineup_optimizer import get_optimizer, Site, Sport, PositionsStack
import tempfile

rename_dict = {
    "Patrick Mahomes II": "Patrick Mahomes"
}

teams_dict = {
    'ARI': "",
    'ATL': "",
    'BAL': "",
    'BUF': "",
    'CAR': "",
    'CHI': "",
    'CIN': "",
    'CLE': "",
    'DAL': "",
    'DEN': "",
    'DET': "",
    'GB': "",
    'HOU': "",
    'IND': "",
    'JAC': "",
    'KC': "",
    'LV': "",
    'LAC': "",
    'LAR': "",
    'MIA': "",
    'MIN': "",
    'NE': "",
    'NO': "",
    'NYG': "",
    'NYJ': "",
    'PHI': "",
    'PIT': "",
    'SF': "",
    'SEA': "",
    'TB': "",
    'TEN': "",
    'WAS': ""
}

def scrape_html(url: str):
    request = requests.get(url)
    s = BeautifulSoup(request.content, features='lxml')
    div = s.find_all("div", {"class": "mobile-table"})
    df1 = pd.read_html(str(div), skiprows=1, header=0)
    df = pd.DataFrame(df1[0])
    df = df[['Player', 'FPTS']]
    df.rename(columns={'Player':'Name'}, inplace=True)
    expr = "|".join(teams_dict.keys())
    df["Name"] = df["Name"].str.replace(expr, "", regex=True).str.strip()
    df["Name"] = df["Name"].replace(rename_dict)

    return df

def scrape_dst(url: str):
    request = requests.get(url)
    s = BeautifulSoup(request.content, features='lxml')
    div = s.find_all("div", {"class": "mobile-table"})
    df1 = pd.read_html(str(div), skiprows=0, header=0)
    df = pd.DataFrame(df1[0])
    df = df[['Player', 'FPTS']]
    df["Player"] = df["Player"].apply(lambda x: x.split()[-1])
    df.rename(columns={'Player':'Name'}, inplace=True)

    return df

def main():
    week = input("Enter Week Number: ")
    url = "https://www.fantasypros.com/nfl/projections/{position}.php?week={week}"
    dfs = []
    positions = ["qb", "rb", "wr", "te", "dst"]
    for position in positions:
        if position == "dst":
            df = scrape_dst(url.format(position=position, week=week))
            dfs.append(df)
        else:
            df = scrape_html(url.format(position=position, week=week))
            dfs.append(df)
    dfs = pd.concat(dfs)
    dk = input("Enter Draftkings Url: ")
    draftkings = pd.read_csv(dk)
    draftkings['Name'] = draftkings['Name'].str.strip()

    merged_df = draftkings.merge(dfs, how='left', on='Name')
    merged_df.drop(columns=["AvgPointsPerGame"], inplace=True)
    merged_df.rename(columns={"FPTS":"AvgPointsPerGame"}, inplace=True)
    merged_df['AvgPointsPerGame'] = merged_df['AvgPointsPerGame'].fillna(0)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as temp_csv:
        temp_csv_name = temp_csv.name
        merged_df.to_csv(temp_csv_name, index=False)

    optimizer = get_optimizer(Site.DRAFTKINGS, Sport.FOOTBALL)
    optimizer.load_players_from_csv(temp_csv_name)
    for lineup in optimizer.optimize(n=5):
        yield(lineup)

for lineup in main():
    print(lineup)