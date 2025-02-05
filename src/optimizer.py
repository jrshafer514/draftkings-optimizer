import pandas as pd
from bs4 import BeautifulSoup
import requests
from pydfs_lineup_optimizer import get_optimizer, Site, Sport, PositionsStack, LineupOptimizer
import tempfile
import json
from io import StringIO
from typing import Generator
import requests
import os

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
        self.dk_url = None
        self.metadata_file = None

    @classmethod
    def draftkings_football(cls, week: str) -> 'Optimizer':
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
        optimizer.dk_url = "https://www.draftkings.com/lineup/getavailableplayerscsv?contestTypeId=21&draftGroupId={id}"
    
        return optimizer
    
    def get_contest_id(self) -> str:
        id = None
        response = requests.get("https://www.draftkings.com/lobby/getcontests?sport=NFL")
        data = response.json()

        for contest in data["Contests"]:
            if contest["gameType"] == "Classic" and "(Thu-Mon)" in contest["n"] and contest["dg"]:
                id = contest["dg"]
                break
        return str(id)


    def check_existing_contest(self):
        path = os.path.join(os.pardir, "metadata", "dk.json")

        try:
            with open(path, 'r') as file:
                data = json.load(file)
                week_data = data.get(str(self.week), None)
                if week_data:
                    # Return the first URL found for the week (assuming one entry per week)
                    return week_data[0]["url"] if week_data else None
                return None
        except (FileNotFoundError, ValueError):
            return None  # Return None if no data or file is found
    


    def scrape_html(self, position: str) -> pd.DataFrame:
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
    
    def scrape_dst(self, position: str) -> pd.DataFrame:
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

    def get_lineups(self) -> Generator[LineupOptimizer.optimize, None, None]:
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

        dk = self.check_existing_contest()

        if not dk:
            # If no URL is found, fetch a new one, record it, and proceed
            contest_id = self.get_contest_id()
            dk = self.dk_url.format(id=contest_id)
            self.record_metadata(id=contest_id, week=self.week)

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
        # optimizer.remove_player(optimizer.get_player_by_name("Jakobi Meyers"))
        # optimizer.player_pool.exclude_teams(['NYG'])

        # optimizer.remove_player(optimizer.get_player_by_name("Zach Charbonnet"))
        # optimizer.add_player_to_lineup(optimizer.get_player_by_name("Ja'Marr Chase"))
        # optimizer.add_player_to_lineup(optimizer.get_player_by_name("Allen Lazard"))

        # optimizer.set_players_from_one_team({'GB': 2})
        
        for lineup in optimizer.optimize(n=5):
            yield(lineup)

    @staticmethod
    def lineup_prompt(lineups: Generator[LineupOptimizer.optimize, None, None]) -> str: 
        """
        Create string from lineup generator to be used as a prompt.

        Args:
            lineups (generator): Generator object containing lineups.

        ReturnsL
            output (str): String containing all lineups in generator.

        """
        output = "\n".join(str(lineup) for lineup in lineups)

        return output
    
    def record_metadata(self, id, week):
        # Define the path to the metadata file
        path = os.path.join(os.pardir, "metadata", "dk.json")
        
        # Try to open the existing metadata file
        try:
            with open(path, "r") as file:
                existing_data = json.load(file)
        except (FileNotFoundError, ValueError):
            # If the file doesn't exist or is invalid, create an empty dictionary
            existing_data = {}

        # Prepare the new data with formatted URL for the given week
        new_data = {
            "week": week,
            "url": self.dk_url.format(id=id)
        }

        # If the week is not present in the metadata, add a new entry
        if str(week) not in existing_data:
            existing_data[str(week)] = []

        # Ensure there's only one URL for the week (or update the existing one)
        existing_data[str(week)] = [new_data]

        # Write the updated data back to the file
        with open(path, "w") as file:
            json.dump(existing_data, file, indent=4)