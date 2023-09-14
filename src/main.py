from twitter import *

def main():
    twitter = Twitter.draftkings()
    tweet = twitter.generate_tweet()
    # twitter.tweet(tweet)
    twitter.process_tweet(tweet)

if __name__ == "__main__":
    main()