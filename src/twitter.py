from optimizer import *
from dotenv import load_dotenv, find_dotenv
import openai
import os
import tweepy
import datetime

path_to_keys = find_dotenv("api_keys.env")
load_dotenv(path_to_keys)

class Twitter():
    """
    This class handles twitter related functions.
    """
    def __init__(self) -> None:
        """
        Initialize a new instance of Twitter class.

        Attributes:
            MODEL: GPT Model to use for Twitter message.
            GPT_KEY: API Key for GPT.
            TWITTER_KEY: API Key for Twitter.
            TWITTER_SECRET: API Secret for Twitter.
            ACCES_TOKEN: Access Token for Twitter.
            ACCESS_TOKEN_SECRET: Access Token Secret for Twitter.
            prompt: Prompt to give to GPT.
            lineups: Lineups to construct prompt.
            lineup_msg: Concatenated lineups to construct prompt.
            bad_chars: Characters to remove from GPT prompt.
            week: Football week to create tweet for.

        """
        self.MODEL = "gpt-3.5-turbo"
        self.GPT_KEY = os.getenv("GPT_KEY")
        self.TWITTER_KEY = os.getenv("TWITTER_KEY")
        self.TWITTER_SECRET = os.getenv("TWITTER_SECRET")
        self.ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
        self.ACCESS_TOKEN_SECRET = os.getenv("ACCESS_TOKEN_SECRET")
        self.prompt = None
        self.lineups = None
        self.lineup_msg = None
        self.bad_chars = None
        self.week = None

    @classmethod
    def draftkings(cls, week) -> 'Twitter':
        """
        Construct Draftkings Twitter Class.

        Args: 
            cls: The class itself.
            week (str): Football week to create tweet for.
        
        Returns:
            Draftkings Twitter Class: An instance of Draftkings Twitter Class.
        """
        instance = cls()
        instance.lineups = Optimizer.draftkings_football(week).get_lineups()
        instance.lineup_msg = Optimizer.lineup_prompt(instance.lineups)
        instance.bad_chars = ["{", "}"]
        instance.week = Optimizer.draftkings_football(week).week
        with open(os.path.join(os.pardir, "prompt.txt"), "r") as p:
            instance.prompt = p.read() + instance.lineup_msg

        return instance

    def generate_tweet(self) -> str:
        """
        Generates tweet from Chat GPT.

        Returns:
            tweet (str): Message to be tweeted.
        """
        openai.api_key = self.GPT_KEY
        response = openai.ChatCompletion.create(
            model=self.MODEL,
            messages=[
                {"role": "user", "content": self.prompt}
            ],
            temperature=0
        )
        tweet = response['choices'][0]['message']['content']
        tweet = "".join(x for x in tweet if not x in self.bad_chars)

        return tweet
    
    def tweet(self, tweet: str) -> None:
        """
        Tweets a message using Twitter API.

        Args:
            tweet (str): Message to be tweeted.
        """
        client = tweepy.Client(
                consumer_key=self.TWITTER_KEY,
                consumer_secret=self.TWITTER_SECRET,
                access_token=self.ACCESS_TOKEN,
                access_token_secret=self.ACCESS_TOKEN_SECRET
        )
        client.create_tweet(text=tweet, user_auth=True)

        return None
    
    def process_tweet(self, tweet: str) -> str:
        """
        Proccesses tweet and stores values for player, price, week, and timestamp in json file.

        Args:
            tweet (str): Message to be tweeted. 

        Returns:
            Print statement with path to file.
        """
        lines = tweet.split("#")
        player_data = []
        for line in lines:
            if "-" in line:
                player_name, price, *rest = line.split("-")
                print(rest)
                player_name = player_name.strip()
                info = {
                    "player_name": player_name,
                    "price": price.replace(",", "").strip().replace(".", ""),
                    "week": self.week,
                    "timestamp": str(datetime.datetime.now())
                }
                player_data.append(info)

        path = os.path.join(os.pardir, "metadata", "data.json")

        try:
            with open(path, "r") as file:
                existing_data = json.load(file)
        
        except ValueError:
            existing_data = None

        
        if not existing_data:
            existing_data = [
                {
                    "player_name": "Week 0",
                    "price": "Week 0",
                    "week": 0,
                    "timestamp": "Week 0"
                }
            ]
        

        existing_data.extend(player_data)

        with open(path, "w") as file:
            json.dump(existing_data, file, indent=4)

        return print(f"Written successfully to {path}") 