from optimizer import *
from dotenv import load_dotenv, find_dotenv
import openai
import os

football = Optimizer.draftkings_football()
lineups = football.get_lineups()
lineup_msg = Optimizer.lineup_prompt(lineups)

path_to_keys = find_dotenv("api_keys.env")
load_dotenv(path_to_keys)

GPT_KEY = os.getenv("GPT_KEY")
MODEL = "gpt-3.5-turbo"

openai.api_key = GPT_KEY

prompt = "I am a professional fantasy football player. I want you to read the following information of optimized draftkings lineups and identify select your 'picks of the week' or players with good value. Each lineup is denoted with position - QB (Quarterback), RB (Runningback), WR (Wide reciever), TE (Tight End), FLEX (Either a RB, WR, or TE), and DST (Defense/Special Teams) - Name, Team (LAC, MIA, etc.), Game location (Team 1 @ Team 2), Points (Projected Fantasy Score), and Salary (Dollar $ Amount to 'draft' that player). The criteria for pick of the week is a relatively low dollar ($) amount mixed with a decently high point value. The lowest salary value is $2500, but $3000-$5000 for players is a good range for value. Also, if you notice one player being repeated in multiple lineups, you may refer to that player as a 'Must Draft' pick for the week. This is very important: do not mention the projected score, but you must mention the salary of the player. Also, you can only select 2 players with a salary over $7000 - the rest must be less than $7000.  There are 5 full lineups being given to you - please identify players to choose from as your picks of the week. The response needs to be less than 200 characters. We can use this template: 'Optimizer loves: 3 picks with salary more than $7000 in format {Player} - {Salary}. Value picks for the week: 5 picks with salary less than $6200 in format {Player} - {Salary}' Need to select 1 or 2 QBs, 2 or 3 RBS, 2 or 3 WRs, and 1 TE or 1 DST. Here is this weeks data: \n" + lineup_msg

response = openai.ChatCompletion.create(
    model=MODEL,
    messages=[
        {"role": "user", "content": prompt}
    ],
    temperature=0
)

# print(response['choices'][0]['message']['content'])