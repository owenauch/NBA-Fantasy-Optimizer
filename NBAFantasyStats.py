from bs4 import BeautifulSoup
from urllib2 import urlopen
import csv
import pandas
import ssl

#website urls
opp_off_rebounds_url = "https://www.teamrankings.com/nba/stat/opponent-offensive-rebounds-per-game"
opp_def_rebounds_url = "https://www.teamrankings.com/nba/stat/opponent-defensive-rebounds-per-game"
opp_points_url = "https://www.teamrankings.com/nba/stat/opponent-points-per-game"
opp_assists_url = "https://www.teamrankings.com/nba/stat/opponent-assists-per-game"
opp_turnovers_url = "https://www.teamrankings.com/nba/stat/opponent-turnovers-per-game"
opp_blocks_url = "https://www.teamrankings.com/nba/stat/opponent-blocks-per-game"
opp_steals_url = "https://www.teamrankings.com/nba/stat/opponent-steals-per-game"
season_stat_url = "http://www.basketball-reference.com/leagues/NBA_2017_totals.html"

#verify set to false (not secure but doesn't really matter for this)
def verify_false():
	ctx = ssl.create_default_context()
	ctx.check_hostname = False
	ctx.verify_mode = ssl.CERT_NONE
	return ctx

#get stat for each team for 2016 off teamrankings.com
def get_stat_series(url, ctx):
	#open and soupify
	html = urlopen(url, context=ctx).read()
	stat_soup = BeautifulSoup(html, "lxml")

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
	#open and soupify
	html = urlopen(url, context=ctx).read()
	season_soup = BeautifulSoup(html, "lxml")

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

#get mean, standard error dataframe for a dataframe
def get_desc_stats(df):
	means = df.mean()
	means = means.rename("mean")
	stdevs = df.std()
	stdevs = stdevs.rename("stdev")
	desc_stats = pandas.concat([means, stdevs], axis=1)
	return desc_stats

if __name__ == "__main__":
	ctx = verify_false()
	series_list = []

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

	#call method to get season stats for each player
	season_df = get_season_stats(season_stat_url, ctx)
	season_desc_df = get_desc_stats(season_df)

	print season_df.dtypes
	print season_desc_df

