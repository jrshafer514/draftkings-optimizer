from twitter import *
from optimizer import *

def main(week):
    twitter = Twitter.draftkings(week)
    tweet = twitter.generate_tweet()
    # twitter.tweet(tweet)
    twitter.process_tweet(tweet) 

if __name__ == "__main__":
    week = input("Week number: ")
    main(week)