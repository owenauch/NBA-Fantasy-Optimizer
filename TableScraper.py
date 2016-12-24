from bs4 import BeautifulSoup
from urllib2 import urlopen
import csv
import pandas

#url of Basketball Reference page
url = "http://www.basketball-reference.com/leagues/NBA_2017_totals.html"

#set columns for pandas dataframe
header = ["Player", "Pos", "Age", "Tm", "G", "GS", "MP", "FG", "FGA", "FG%", "3P", "3PA", "3P%", "2P", "2PA", "2P%", "eFG%", "FT", "FTA", "FT%", "ORB", "DRB", "TRB", "AST", "STL", "BLK", "TOV", "PF", "PTS"]

#open url and turn to BS object
def make_soup(url):
	html = urlopen(url).read()
	soup = BeautifulSoup(html, "lxml")
	return soup


#returns list of lists (lol_table) of html table
def lol_table(soup, class_name = ""):
	rows = []
	if class_name is "":
		rows = soup.find_all('tr')
	else:
		rows = soup.find_all('tr', class_ = class_name)
	data = []
	for row in rows:
		cols = row.find_all('td')
		data_row = []
		for col in cols:
			data_row.append(col.find(text=True))
		data.append(data_row)
	return data


#create pandas dataframe from lol_table and create csv of it
def to_pandas_csv(lol_table, csv_name, column_names):
	df = pandas.DataFrame(lol_table, columns=column_names)
	df.to_csv(csv_name)
	return df

def to_pandas(lol_table, column_names):
	df = pandas.DataFrame(lol_table, columns=column_names)
	return df
	
#to ensure it only runs this when called specifically
if __name__ == '__main__':
	soup = make_soup(url)
	table = lol_table(soup, "full_table")
	data_frame = to_pandas_csv(table, "nba.csv", header)
