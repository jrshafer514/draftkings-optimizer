from twitter import *
from optimizer import *
import os

def main(week):
    optimizer = Optimizer.draftkings_football(week)
    # twitter = Twitter.draftkings(week)
    
    # tweet = twitter.generate_tweet()
    # twitter.tweet(tweet)
    # twitter.process_tweet(tweet)

    lineups = optimizer.get_lineups()
    for lineup in lineups:    
        print('\n\n\n', lineup, '\n\n\n')


        

if __name__ == "__main__":
    week = "20"
    os.chdir("src/")

    meta_path = os.path.join(os.pardir, "metadata", "data.json")

    # try:
    #     with open(meta_path, "r") as f:
    #         metadata = json.load(f)
    #     for data in metadata:
    #         if int(data["week"]) > week:
    #             week = int(data["week"]) + 1

    # except ValueError:
    #     week = int(input("Enter Week Number: "))

    main(week)