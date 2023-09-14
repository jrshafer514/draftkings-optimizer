from optimizer import *
from dotenv import load_dotenv, find_dotenv
import openai
import os
import tweepy
import datetime

path_to_keys = find_dotenv("api_keys.env")
load_dotenv(path_to_keys)

GPT_KEY = os.getenv("GPT_KEY")
MODEL = "gpt-3.5-turbo"
TWITTER_KEY = os.getenv("TWITTER_KEY")
TWITTER_SECRET = os.getenv("TWITTER_SECRET")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
ACCESS_TOKEN_SECRET = os.getenv("ACCESS_TOKEN_SECRET")
BEARER_TOKEN = os.getenv("BEARER_TOKEN")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_ID_SECRET")

class Twitter():
    GPT_KEY = GPT_KEY
    TWITTER_KEY = TWITTER_KEY
    TWITTER_SECRET = TWITTER_SECRET
    ACCESS_TOKEN = ACCESS_TOKEN
    ACCESS_TOKEN_SECRET = ACCESS_TOKEN_SECRET
    prompt = None
    lineups = None
    lineup_msg = None
    bad_chars = None
    week = None
    instance = None

    @classmethod
    def draftkings(self):
        self.lineups = Optimizer.draftkings_football().get_lineups()
        self.lineup_msg = Optimizer.lineup_prompt(self.lineups)
        self.prompt = "I am a professional fantasy football player. I want you to read the following information of optimized draftkings lineups and identify and select your 'picks of the week' - players with good value. Each lineup is denoted with a position - QB (Quarterback), RB (Runningback), WR (Wide reciever), TE (Tight End), FLEX (Either a RB, WR, or TE), and DST (Defense/Special Teams) - Name, Team (LAC, MIA, etc.), Game location (Team 1 @ Team 2), Points (Projected Fantasy Score), and Salary (Dollar $ Amount to 'draft' that player). The criteria for pick of the week is a relatively low dollar ($) amount mixed with a decently high point value. The lowest salary value is $2500, but $3000-$5000 for players is a good range for value. Also, if you notice one player being repeated in multiple lineups, you may refer to that player as a 'Must Draft' pick for the week. This is very important: do not mention the projected score, but you must mention the salary of the player. Also, you can only select 2 players with a salary over $7000 - the rest must be less than $7000.  There are 5 full lineups being given to you - please identify players to choose from as your picks of the week. The response needs to be less than 200 characters. We can use this template: 'The #Optimizer loves: [3 picks with salary more than $700] (in format) #{Player} - {Salary}, [5 picks with salary less than $6200] (in format) #{Player} - {Salary}. #fantasy #draftkings #dailyfantasy #dfs' Don't include the text in brackets [] or parenthesis (). Make sure there is a '#' before each player. Use the {} as a format implier to add the player and salary amount, but dont actually include the '{' or '}' character in the message. Need to select 1 or 2 QBs, 2 or 3 RBS, 2 or 3 WRs, and 1 TE or 1 DST. Here is this weeks data: \n" + self.lineup_msg
        self.bad_chars = ["{", "}"]
        self.week = "2"

        return self

    @classmethod
    def generate_tweet(self):
        openai.api_key = self.GPT_KEY
        response = openai.ChatCompletion.create(
            model=MODEL,
            messages=[
                {"role": "user", "content": self.prompt}
            ],
            temperature=0
        )
        tweet = response['choices'][0]['message']['content']
        tweet = "".join(x for x in tweet if not x in self.bad_chars)

        return tweet
    
    @classmethod
    def tweet(self, tweet):
        client = tweepy.Client(
                consumer_key=self.TWITTER_KEY,
                consumer_secret=self.TWITTER_SECRET,
                access_token=self.ACCESS_TOKEN,
                access_token_secret=self.ACCESS_TOKEN_SECRET
        )
        client.create_tweet(text=tweet, user_auth=True)

        return None
    
    @classmethod
    def process_tweet(self, tweet):
        lines = tweet.split("#")
        player_data = []
        week = self.week
        for line in lines:
            if "-" in line:
                player_name, price = line.split("-")
                player_name = player_name.strip()
                info = {
                    "player_name": player_name,
                    "week": week,
                    "timestamp": str(datetime.datetime.now())
                }
                player_data.append(info)

        path = os.path.join(os.pardir, "metadata", "data.json")
        with open(path, "w") as file:
            json.dump(player_data, file)
        
        return print(f"Written successfully to {path}")
        



