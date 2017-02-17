# The Porzingis Project
#### NBA Daily Fantasy Lineup Optimizer for Fanduel
----
This repository contains a script that uses Python to scrape stats for each player in the NBA from Basketball Reference, TeamRankings, and Rotowire, and crunches these stats in order to project the total fantasy points for the current day for each player on FanDuel. These inputs are fed into a greedy algorithm that tries to select a lineup of players that maximizes the total expected fantasy points while staying under a salary cap. This is an example of [the knapsack problem](https://en.wikipedia.org/wiki/Knapsack_problem), which is NP-complete, so the algorithm uses a heuristic of starting with the most undervalued players (those that produce the higher number of points per salary dollar), and then replacing players who put up few fantasy points per night with slightly less efficient players that put up more. This script is nicknamed the Porzingis Project because the algorithm sees Kristaps Porzingis as the perfect fantasy player, putting him in the lineup almost every night that he plays.

#### Requires
* [Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/#Download)
