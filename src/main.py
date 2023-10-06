from twitter import *
from optimizer import *

def main(week):
    dk_url = "https://www.draftkings.com/lineup/getavailableplayerscsv?contestTypeId=21&draftGroupId=93194"
    Draftkings.set_dk_url(dk_url)
    optimizer = Optimizer.draftkings_football(week)

    # lineups = optimizer.get_lineups()
    # for lineup in lineups:    
    #     print(lineup)

if __name__ == "__main__":
    week = input("Week number: ")
    main(week)