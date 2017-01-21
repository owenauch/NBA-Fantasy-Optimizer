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
TOV = -1

#2 PG, 2 SG, 2 SF, 2 PF, 1 C
salary_cap = 60000
PG_cap = 2
SG_cap = 2
SF_cap = 2
PF_cap = 2
C_cap = 1

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

#gets df of players playing tonight with "Player", "POS", "PPG", "Salary" columns
def get_simple_ppg(season, salary):
	#loops through each player playing tonight
	player_column = salary['Player']

	list = []

	#goes through all players playing tonight and presents their season stats as a Series
	for idx, player in enumerate(player_column):
		player_series = season.loc[season['Player'] == player].squeeze()

		#screen out ones where it doesn't match -- sorry Lou (Louis) Williams
		player = "unknown"
		ppg = 0
		ppd = 0

		if not(player_series.empty):

			#games played
			gp = float(player_series["G"])

			#points
	 		pts = float(player_series["PTS"])

	 		#offensive rebounds
			orb = float(player_series["ORB"])

			#defensive rebounds
	 		drb = float(player_series["DRB"])

	 		#assists
	 		ast = float(player_series["AST"])

	 		#steals
	 		stl = float(player_series["STL"])

	 		#blocks
	 		blk = float(player_series["BLK"])

	 		#turnovers
			tov = float(player_series["TOV"])

			total_points = (pts * POINT) + ((orb + drb) * REBOUND) + (ast * ASSIST) + (stl * STEAL) + (blk * BLOCK) + (tov * TOV)
			ppg = total_points / gp
			player = player_series["Player"]
			ppd = ppg / float(salary["Salary"][idx])

		row = [player, player_series["Pos"], ppg, ppd, float(salary["Salary"][idx])]

		list.append(row)

	df = pandas.DataFrame(list, columns=["Player", "POS", "PPG", "PPD", "Salary"])
	df_sort = df.sort_values(by="PPD", ascending=False)
	df_out = df_sort[df_sort["PPD"] != 0]

	return df_out

#returns a list of best lineup according to greedy algorithm)
def greedy_knap(avail_players):
	#list is position, cap, count
	PG = ["PG", PG_cap, 0, [], 0]
	SG = ["SG", SG_cap, 0, [], 1]
	SF = ["SF", SF_cap, 0, [], 2]
	PF = ["PF", PF_cap, 0, [], 3]
	C = ["C", C_cap, 0, [], 4]

	squad = [PG, SG, SF, PF, C]

	current_sal = 0

	#first, get best players in terms of ppg
	for i, row in avail_players.iterrows():
		for position in squad:
			#if it matches the position
			if (row["POS"] == position[0]):
				#if the position isn't full
				if (position[1] > position[2]):
					#if we can afford him
					if (current_sal + row["Salary"] <= salary_cap):
						#add him to the list for the position
						position[3].append(row["Player"])
						#increase current salary
						current_sal += row["Salary"]
						#increase number at position
						position[2] += 1
						#replace in squad
						squad_pos = position[4]
						squad[squad_pos] = position

	#now, loop through again by PPD and replace lowest PPG player at a position with a player with higher PPG
	#while staying under salary cap
	#loops through player
	for i, row in avail_players.iterrows():
		for position in squad:
			#if it matches the position
			if (row["POS"] == position[0]):
				#if there are two players at the position, find the one with lower PPG
				player = ""
				player_sal = 0
				player_ppg = 0
				player_slot = 0
				other_player = None

				if len(position[3]) == 2:
					for players in position[3]:
						#get player_1 row
						player_1 = avail_players.loc[avail_players['Player'] == position[3][0]]
						player_1_ppg = player_1["PPG"].values[0]

						#get player 2 row and ppg
						player_2 = avail_players.loc[avail_players['Player'] == position[3][1]]
						player_2_ppg = player_2["PPG"].values[0]

						if (player_1_ppg > player_2_ppg):
							player = player_2["Player"]
							player_sal = player_2["Salary"]
							player_ppg = player_2["PPG"]
							player_slot = 1
							other_player = player_1

						else:
							player = player_1["Player"]
							player_sal = player_1["Salary"]
							player_ppg = player_1["PPG"]
							other_player = player_2

				#if there's one player, just do that
				else:
					player_row = avail_players.loc[avail_players['Player'] == position[3][0]]
					player = player_row["Player"]
					player_sal = player_row["Salary"]
					player_ppg = player_row["PPG"] 
					other_player = player_row

				#if the player's ppg is higher than the lowest at their position
				player_ppg = player_ppg.values[0]
				player_sal = player_sal.values[0]
				player = player.values[0]

				#if it isn't a duplicate
				if (other_player["Player"].values[0] != row["Player"]):
					if (row["PPG"] > player_ppg):
						#if we can afford him
						if (row["Salary"] + current_sal - player_sal <= salary_cap):
							#replace the player in the squad
							current_sal = current_sal - player_sal + row["Salary"]
							position[3][player_slot] = row["Player"]
							squad_pos = position[4]
							squad[squad_pos] = position

	#get player names in a list
	best_squad = []
	for pos in squad:
		for player in pos[3]:
			best_squad.append(player)

	return best_squad

def stringify_lineup(line):
	go_2 = range(2)
	positions = ["Point Guards", "Shooting Guards", "Small Forwards", "Power Forwards"]

	stringy_line = "Optimal FanDuel Lineup for Today \n \n"

	counter = 0
	for position in positions:
		stringy_line += position
		stringy_line += ": \n"
		for player in go_2:
			stringy_line += line[counter]
			stringy_line += "\n"
			counter += 1
		stringy_line += "\n"

	stringy_line += "Center:\n"
	stringy_line += line[counter]
	stringy_line += "\n"

	return stringy_line

#have injured players taken out of the lineup
def manual_injury(ppg, line):
	py3 = version_info[0] > 2 #creates boolean value for test that Python major version > 2
	injured = "y"

	while (injured == "y"):
		if py3:
			injured = input("Are any of the players in this lineup injured? (y/n)\n")
		else:
			injured = raw_input("Are any of the players in this lineup injured? (y/n)\n")

		injured = injured.lower()

		if (injured == "y"):
			if py3:
		  		player = input("Enter the injured player's name exactly: ")
			else:
		  		player = raw_input("Enter the injured player's name exactly: ")

		  	ppg = ppg[ppg["Player"] != player]

		  	print stringify_lineup(greedy_knap(ppg))

		

if __name__ == "__main__":

	print "\nFetching NBA statistics and determining optimal lineup...\n\n"

	ctx = verify_false()
	series_list = []
	df_list = []

	# off_rebounds_series = get_stat_series(opp_off_rebounds_url, ctx)
	# series_list.append(off_rebounds_series)

	# def_rebounds_series = get_stat_series(opp_def_rebounds_url, ctx)
	# series_list.append(def_rebounds_series)

	# opp_points_series = get_stat_series(opp_points_url, ctx)
	# series_list.append(opp_points_series)

	# opp_assists_series = get_stat_series(opp_assists_url, ctx)
	# series_list.append(opp_assists_series)

	# opp_turnovers_series = get_stat_series(opp_turnovers_url, ctx)
	# series_list.append(opp_turnovers_series)

	# opp_blocks_series = get_stat_series(opp_blocks_url, ctx)
	# series_list.append(opp_blocks_series)

	# opp_steals_series = get_stat_series(opp_steals_url, ctx)
	# series_list.append(opp_steals_series)

	# this contains all opponent stats for each category relevant for fantasy basketball
	# columns, in order, are: 
	# 'Opponent Offensive Rebounds per Game', 'Opponent Defensive Rebounds per Game', 
	# 'Opponent Points per Game', 'Opponent Assists per Game', 'Opponent Turnovers per Game', 'Opponent Blocks per Game', 'Opponent Steals per Game'
	# teams are in alphabetical order
	# opp_stat_df = pandas.concat(series_list, axis=1)
	# opp_stat_desc = get_desc_stats(opp_stat_df)
	# df_list.append(opp_stat_df)
	# df_list.append(opp_stat_desc)

	#call method to get season stats for each player
	season_df = get_season_stats(season_stat_url, ctx)
	season_desc_df = get_desc_stats(season_df)
	df_list.append(season_df)
	df_list.append(season_desc_df)

	#call method to get advanced stats for each player
	# season_advanced_df = get_season_stats(season_advanced_url, ctx)
	# advanced_desc_df = get_desc_stats(season_advanced_df)
	# df_list.append(season_advanced_df)
	# df_list.append(advanced_desc_df)

	#call method to get salaries for players playing tonight
	salary_df = get_current_salary(salary_url, ctx)
	salary_desc_df = get_desc_stats(salary_df)
	df_list.append(salary_df)
	df_list.append(salary_desc_df)

	#general approach for next part
	#get each player with position, and all scorable categories
	#find expected points scored, and choose best lineup with greedy algorithm (prioritizing for points per game)

	ppg_simple_df = get_simple_ppg(season_df, salary_df)

	lineup = greedy_knap(ppg_simple_df)

	pretty_lineup = stringify_lineup(lineup)

	print pretty_lineup

	uninjured_pretty = manual_injury(ppg_simple_df, pretty_lineup)






