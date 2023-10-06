import pandas as pd
from bs4 import BeautifulSoup
import requests
from pydfs_lineup_optimizer import get_optimizer, Site, Sport, PositionsStack
import tempfile
import json
from io import StringIO
class Draftkings():
    draftkings_url = None

    @classmethod
    def set_dk_url(cls, url):
        cls.draftkings_url = url
        return cls

class Optimizer():
    """
    This class handles optimizer functions.
    """
    def __init__(self, week: str) -> None:
        self.week = week
        self.rename_dict = None
        self.teams_dict = None
        self.url = None
        self.positions = None
        self.config_file = None

    @classmethod
    def draftkings_football(cls, week: str):
        """
        Construct Draftkings Football Optimizer Class

        Args:
            cls: The class itself.
            week (str): Football week to optimize.
        
        Returns: 
            Draftkings Football Optimizer: An instance of Draftkings Football Optimizer Class.
        """
        optimizer = cls(week)
        with open("config/optimizer_config.json") as j:
            optimizer.config_file = json.load(j)
        optimizer.rename_dict = optimizer.config_file["RENAME_DICT"]
        optimizer.teams_dict = optimizer.config_file["TEAMS_DICT"]
        optimizer.url = "https://www.fantasypros.com/nfl/projections/{position}.php?week={week}&scoring=PPR"
        optimizer.positions = ["qb", "rb", "wr", "te", "dst"]
    
        return optimizer

    def scrape_html(self, position: str):
        """
        Scrapes https://www.fantasypros.com for fantasy data.

        Args:
            position (str): Position to scrape data for.

        Returns:
            df (DataFrame): Pandas DataFrame with player and fantasy points projections.
        """
        request = requests.get(self.url.format(position=position, week=self.week))
        s = BeautifulSoup(request.content, features='lxml')
        div = s.find_all("div", {"class": "mobile-table"})
        buffer = StringIO(str(div))
        df1 = pd.read_html(buffer, skiprows=1, header=0)
        df = pd.DataFrame(df1[0])
        df = df[['Player', 'FPTS']]
        df.rename(columns={'Player':'Name'}, inplace=True)
        expr = "|".join(self.teams_dict.keys())
        df["Name"] = df["Name"].str.replace(expr, "", regex=True).str.strip()
        df["Name"] = df["Name"].replace(self.rename_dict)

        return df
    
    def scrape_dst(self, position: str):
        """
        Scrapes https://www.fantasypros.com for fantasy data for defenses.

        Args:
            position (str): Position to scrape data for.

        Returns:
            df (DataFrame): Pandas DataFrame with defense and fantasy points projections.
        """
        request = requests.get(self.url.format(position=position, week=self.week))
        s = BeautifulSoup(request.content, features='lxml')
        div = s.find_all("div", {"class": "mobile-table"})
        buffer = StringIO(str(div))
        df1 = pd.read_html(buffer, skiprows=0, header=0)
        df = pd.DataFrame(df1[0])
        df = df[['Player', 'FPTS']]
        df["Player"] = df["Player"].apply(lambda x: x.split()[-1])
        df.rename(columns={'Player':'Name'}, inplace=True)

        return df

    def get_lineups(self):
        """
        Gets optimized lineups from scraped data.

        Args:
            None

        Returns:
            lineup (generator): Generator object containing all optimized lineups.
            
        """
        dfs = []
        for position in self.positions:
            if position == "dst":
                df = self.scrape_dst(position=position)
                dfs.append(df)
            else:
                df = self.scrape_html(position=position)
                dfs.append(df)
        dfs = pd.concat(dfs)
        if Draftkings.draftkings_url:
            dk = Draftkings.draftkings_url
        else:
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
        optimizer.add_player_to_lineup(optimizer.get_player_by_name("Lamar Jackson"))
        for lineup in optimizer.optimize(n=5):

            yield(lineup)

    @staticmethod
    def lineup_prompt(lineups) -> str: 
        """
        Create string from lineup generator to be used as a prompt.

        Args:
            lineups (generator): Generator object containing lineups.

        ReturnsL
            output (str): String containing all lineups in generator.

        """
        output = "\n".join(str(lineup) for lineup in lineups)

        return output