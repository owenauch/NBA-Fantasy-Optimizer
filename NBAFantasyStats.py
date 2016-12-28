from bs4 import BeautifulSoup
from urllib2 import urlopen
import csv
import pandas
import ssl
from sys import version_info

#website urls
opp_off_rebounds_url = "https://www.teamrankings.com/nba/stat/opponent-offensive-rebounds-per-game"
opp_def_rebounds_url = "https://www.teamrankings.com/nba/stat/opponent-defensive-rebounds-per-game"
opp_points_url = "https://www.teamrankings.com/nba/stat/opponent-points-per-game"
opp_assists_url = "https://www.teamrankings.com/nba/stat/opponent-assists-per-game"
opp_turnovers_url = "https://www.teamrankings.com/nba/stat/opponent-turnovers-per-game"
opp_blocks_url = "https://www.teamrankings.com/nba/stat/opponent-blocks-per-game"
opp_steals_url = "https://www.teamrankings.com/nba/stat/opponent-steals-per-game"
season_stat_url = "http://www.basketball-reference.com/leagues/NBA_2017_totals.html"
season_advanced_url = "http://www.basketball-reference.com/leagues/NBA_2017_advanced.html"
salary_url = "http://www.rotowire.com/daily/nba/optimizer.php?site=FanDuel&sport=NBA"

#FanDuel points per stat
POINT = 1
REBOUND = 1.2
ASSIST = 1.5
STEAL = 2
BLOCK = 2
TO = -1

#checks which algorithm the user would like to use
#the simple algorithm doesn't adjust for opponent defense
def check_algorithm():
	py3 = version_info[0] > 2 #creates boolean value for test that Python major version > 2

	response = ''
	if py3:
	  response = input("Welcome to the NBA Daily Fantasy Lineup Optimizer. Type 'simple' to use the simple algorithm or 'advanced' to use the advanced algorithm: ")
	else:
	  response = raw_input("Welcome to the NBA Daily Fantasy Lineup Optimizer. Type 'simple' to use the simple algorithm or 'advanced' to use the advanced algorithm: ")

	response = response.lower()

	#false if simple, true if advanced
	algo_bool = True
	if response == "simple":
		algo_bool = False
	elif response == "advanced":
		algo_bool = True
	else:
		print "Your input is not being recognized. Please try again."
		check_algorithm()

	return algo_bool

#verify set to false (not secure but doesn't really matter for this)
def verify_false():
	ctx = ssl.create_default_context()
	ctx.check_hostname = False
	ctx.verify_mode = ssl.CERT_NONE
	return ctx

#open and soupify
def soupify(url, ctx):
	html = urlopen(url, context=ctx).read()
	soup = BeautifulSoup(html, "lxml")
	return soup

#get stat for each team for 2016 off teamrankings.com
def get_stat_series(url, ctx):
	stat_soup = soupify(url, ctx)

	#find which stat it is
	title = stat_soup.find('title').string
	first_index = title.find("on")
	second_index = title[first_index + 2:].find("on")
	last_index = first_index + second_index + 1
	stat_cat = title[21:last_index]

	#just get first and second column
	stat_data = []
	team_index = []
	rows = stat_soup.find_all('tr')
	del rows[0]
	for row in rows:
		cols = row.find_all('td')
		team_index.append(cols[1]['data-sort'])
		stat_data.append((float)(cols[2].find(text=True)))

	#get in series and sort it
	stat_series = pandas.Series(stat_data, index=team_index, name=stat_cat)
	stat_series = stat_series.sort_index()
	return stat_series

#get season stats from basketball reference
def get_season_stats(url, ctx):
	season_soup = soupify(url, ctx)

	#get column names
	column_names = []
	table = season_soup.find('table', class_="stats_table")
	table_head = table.find('thead')
	tr = table_head.find('tr')
	for col in tr.find_all("th"):
		column_names.append(col.find(text=True))

	#get rid of rank, will be index
	del column_names[0]

	#get data in list matrix
	#make sure to cast strings to floats
	rows = season_soup.find_all('tr', class_ = "full_table")
	season_data = []
	for row in rows:
		cols = row.find_all('td')
		season_data_row = []
		for col in cols[0:4]:
			season_data_row.append(col.find(text=True))
		for col in cols[4:]:
			stat = col.find(text=True)
			if stat is None:
				stat = 0.0
			season_data_row.append(float(stat))
		season_data.append(season_data_row)

	#make into pandas dataframe
	season_df = pandas.DataFrame(season_data, columns=column_names)
	return season_df

def get_current_salary(url, ctx):
	salary_soup = soupify(url, ctx)

	table = salary_soup.find('table', class_ = "rwo-playertable")
	rows = table.find_all('tr')
	salary_data = []
	#because it's weird
	counter = 0;
	for row in rows:
		if counter > 0:
			salary_data_row = []
			#add player name
			salary_data_row.append(row.find("a", class_ = "dplayer-link").find(text=True))
			#add salary
			salary = (row.find('td', class_ = "rwo-salary")["data-salary"])
			salary = salary.replace(",","")
			salary_data_row.append(float(salary))
			salary_data.append(salary_data_row)
		counter += 1	

	salary_df = pandas.DataFrame(salary_data, columns = ["Player", "Salary"])
	return salary_df

#get mean, standard error dataframe for a dataframe
def get_desc_stats(df):
	means = df.mean()
	means = means.rename("mean")
	stdevs = df.std()
	stdevs = stdevs.rename("stdev")
	desc_stats = pandas.concat([means, stdevs], axis=1)
	return desc_stats

#get estimated fantasy stats in a game for a player
#this number is unadjusted for opposition defense
def salary_stats(season, advanced, salary):
	#loops through each player playing tonight
	player_column = salary['Player']

	cats_list = ["Player", "G", "PTS", "ORB", "DRB", "AST", "STL", "BLK", "TOV", "USG%", "ORG%", "DRB%", "AST%", "STL%", "BLK%", "TOV%", "Salary", "POS"]
	#list of lists
	stat_lol = []
	for idx, player in enumerate(player_column):
		player_series = season.loc[season['Player'] == player].squeeze()
		player_series_advanced = advanced.loc[advanced['Player'] == player].squeeze()
		stats = []

		#player name
		stats.append(player)

		#games played
		gp = player_series["G"]
		stats.append(gp)

		#points
		pts = player_series["PTS"]
		stats.append(pts)

		#offensive rebounds
		orb = player_series["ORB"]
		stats.append(orb)

		#defensive rebounds
		drb = player_series["DRB"]
		stats.append(drb)

		#assists
		ast = player_series["AST"]
		stats.append(ast)

		#steals
		stl = player_series["STL"]
		stats.append(stl)

		#blocks
		blk = player_series["BLK"]
		stats.append(blk)

		#turnovers
		tov = player_series["TOV"]
		stats.append(tov)

		#usage percentage (correlates to points)
		#higher means you use more possessions
		usg = player_series_advanced["USG%"]
		stats.append(usg)

		#offensive rebound percentage
		orb_per = player_series_advanced["ORB%"]
		stats.append(orb_per)

		#defensive rebound percentage
		drb_per = player_series_advanced["DRB%"]
		stats.append(drb_per)

		#assist percentage
		ast_per = player_series_advanced["AST%"]
		stats.append(ast_per)

		#steal percentage
		stl_per = player_series_advanced["STL%"]
		stats.append(stl_per)

		#block percentage
		blk_per = player_series_advanced["BLK%"]
		stats.append(blk_per)

		#turnover rate
		tov_per = player_series_advanced["TOV%"]
		stats.append(tov_per)

		stats.append(salary["Salary"][idx])

		stats.append(player_series["Pos"])

		#add row to list of lists
		stat_lol.append(stats)

	#make into pandas
	stats_df = pandas.DataFrame(stat_lol, columns = cats_list)

	return stats_df

#adjusts statistics based on opponent defense
#sets the stats as per game
#and returns a dataframe with the adjusted stats
def adjust_stats(salary_stats, season_desc, advanced_desc, opp_stat, opp_desc):
	# print "Salary Stats"
	# print salary_stats
	# print "Season Desc"
	# print season_desc
	# print "Advanced Desc"
	# print advanced_desc
	# print "Opp Stat"
	# print opp_stat
	# print "Opponent Desc"
	# print opp_desc
	return None

#returns df of player, salary and points
def get_points_salary(salary_stats):

	points_values = []
	for player in salary_stats.itertuples():
		row = []
		gp = player[2]

		#fantasy points per game from PTS (index 3)
		fan_pts = (player[3]/gp) * POINT

		#fantasy points per game from REBOUNDS (index 4 + 5)
		fan_rbs = ((player[4] + player[5])/gp) * REBOUND

		#fantasy points per game from AST (index 6)
		fan_ast = (player[6]/gp) * ASSIST

		#fantasy points per game from STL (index 7)
		fan_stl = (player[7]/gp) * STEAL

		#fantasy points per game from BLK (index 8)
		fan_blk = (player[8]/gp) * BLOCK

		#fantasy points per game from TOV (index 9)
		fan_tov = (player[9]/gp) * TO

		fan_total = fan_pts + fan_rbs + fan_ast + fan_stl + fan_blk + fan_tov
		salary = player[17]
		name = player[1]
		position = player[18]

		#each row has name, salary and fantasy point total
		row.append(name)
		row.append(position)
		row.append(salary)
		row.append(fan_total)
		points_values.append(row)

	points_and_salary = pandas.DataFrame(points_values, columns=["Player", "Salary", "Fantasy Points", "Position"])
	return points_and_salary

#finds optimized lineup based on points per dollar and salary
def optimize_players(points_salary):
	print "a"


	
		

if __name__ == "__main__":
	#check which algorithm
	is_advanced = check_algorithm()

	ctx = verify_false()
	series_list = []
	df_list = []

	#only execute if advanced algorithm
	if is_advanced:
		off_rebounds_series = get_stat_series(opp_off_rebounds_url, ctx)
		series_list.append(off_rebounds_series)

		def_rebounds_series = get_stat_series(opp_def_rebounds_url, ctx)
		series_list.append(def_rebounds_series)

		opp_points_series = get_stat_series(opp_points_url, ctx)
		series_list.append(opp_points_series)

		opp_assists_series = get_stat_series(opp_assists_url, ctx)
		series_list.append(opp_assists_series)

		opp_turnovers_series = get_stat_series(opp_turnovers_url, ctx)
		series_list.append(opp_turnovers_series)

		opp_blocks_series = get_stat_series(opp_blocks_url, ctx)
		series_list.append(opp_blocks_series)

		opp_steals_series = get_stat_series(opp_steals_url, ctx)
		series_list.append(opp_steals_series)

		# this contains all opponent stats for each category relevant for fantasy basketball
		# columns, in order, are: 
		# 'Opponent Offensive Rebounds per Game', 'Opponent Defensive Rebounds per Game', 
		# 'Opponent Points per Game', 'Opponent Assists per Game', 'Opponent Turnovers per Game', 'Opponent Blocks per Game', 'Opponent Steals per Game'
		# teams are in alphabetical order
		opp_stat_df = pandas.concat(series_list, axis=1)
		opp_stat_desc = get_desc_stats(opp_stat_df)
		df_list.append(opp_stat_df)
		df_list.append(opp_stat_desc)

	#call method to get season stats for each player
	season_df = get_season_stats(season_stat_url, ctx)
	season_desc_df = get_desc_stats(season_df)
	df_list.append(season_df)
	df_list.append(season_desc_df)

	#call method to get advanced stats for each player
	season_advanced_df = get_season_stats(season_advanced_url, ctx)
	advanced_desc_df = get_desc_stats(season_advanced_df)
	df_list.append(season_advanced_df)
	df_list.append(advanced_desc_df)

	#call method to get salaries for players playing tonight
	salary_df = get_current_salary(salary_url, ctx)
	salary_desc_df = get_desc_stats(salary_df)
	df_list.append(salary_df)
	df_list.append(salary_desc_df)

	#df of salary and stats
	salary_stats_df = salary_stats(season_df, season_advanced_df, salary_df)

	if is_advanced:
		#df of stats adjusted for opposing team
		adjusted_stats_df = adjust_stats(salary_stats_df, season_desc_df, advanced_desc_df, opp_stat_df, opp_stat_desc)
	else:
		#gets df of players, salaries and points
		points_salary_df = get_points_salary(salary_stats_df)
		#finds optimized lineups
		print points_salary_df
		optimize_players(points_salary_df)



