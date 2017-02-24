# The Porzingis Project

A script that scrapes stats for each player in the NBA from Basketball Reference, TeamRankings, and Rotowire, and generates an expected points value for each player. These expected points are then fed to a greedy algorithm that maximizes the total expected fantasy points while staying under a salary cap using a heuristic of preferencing undervalued players.

## How to Run

Clone the repo and run 
```
python NBAFantasyStats.py
```

##### Requires:
* [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/#Download)

Shoutout to Kristaps Porzingis for being the algorithm MVP
