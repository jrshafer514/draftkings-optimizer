import json
import os
import pandas as pd
import requests

base_url = "https://www.draftkings.com/lobby/getcontests?sport=NFL"


response = requests.get(base_url)

data = response.json()

for contests in data["Contests"]:
    if contests["gameType"] == "Classic" and "(Thu-Mon)" in contests["n"] and contests["dg"]:
        print(contests["dg"])
        break
