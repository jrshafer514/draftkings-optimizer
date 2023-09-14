import pandas as pd
from bs4 import BeautifulSoup
import requests
from pydfs_lineup_optimizer import get_optimizer, Site, Sport, PositionsStack
import tempfile
import json

class Optimizer():
    rename_dict = None
    teams_dict = None
    url = None
    positions = None
    config_file = None
    week = None

    @staticmethod
    def return_week():
        week = input("Enter Week: ")
        return week

    @classmethod
    def draftkings_football(self):
        with open("config/optimizer_config.json") as j:
            self.config_file = json.load(j)
        self.rename_dict = self.config_file["RENAME_DICT"]
        self.teams_dict = self.config_file["TEAMS_DICT"]
        self.url = "https://www.fantasypros.com/nfl/projections/{position}.php?week={week}&scoring=PPR"
        self.positions = ["qb", "rb", "wr", "te", "dst"]
        self.week = self.return_week()
        return self

    @classmethod
    def scrape_html(self, url: str, week: str, position: str):
        request = requests.get(self.url.format(position=position, week=week))
        s = BeautifulSoup(request.content, features='lxml')
        div = s.find_all("div", {"class": "mobile-table"})
        df1 = pd.read_html(str(div), skiprows=1, header=0)
        df = pd.DataFrame(df1[0])
        df = df[['Player', 'FPTS']]
        df.rename(columns={'Player':'Name'}, inplace=True)
        expr = "|".join(self.teams_dict.keys())
        df["Name"] = df["Name"].str.replace(expr, "", regex=True).str.strip()
        df["Name"] = df["Name"].replace(self.rename_dict)
        return df
    
    @classmethod
    def scrape_dst(self, url: str, week: str, position: str):
        request = requests.get(self.url.format(position=position, week=week))
        s = BeautifulSoup(request.content, features='lxml')
        div = s.find_all("div", {"class": "mobile-table"})
        df1 = pd.read_html(str(div), skiprows=0, header=0)
        df = pd.DataFrame(df1[0])
        df = df[['Player', 'FPTS']]
        df["Player"] = df["Player"].apply(lambda x: x.split()[-1])
        df.rename(columns={'Player':'Name'}, inplace=True)

        return df
    
    @classmethod
    def get_lineups(self):
        week = self.week
        dfs = []
        for position in self.positions:
            if position == "dst":
                df = self.scrape_dst(self.url, week=week, position=position)
                dfs.append(df)
            else:
                df = self.scrape_html(self.url, week=week, position=position)
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
        optimizer.set_max_repeating_players(2)
        for lineup in optimizer.optimize(n=5):

            yield(lineup)

    @staticmethod
    def lineup_prompt(lineups):
        output = "\n".join(str(lineup) for lineup in lineups)

        return output