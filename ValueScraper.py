from bs4 import BeautifulSoup
from urllib2 import urlopen
import csv
import pandas
import TableScraper as ts

#url of table with values
url = "http://www.rotowire.com/daily/NBA/optimizer.php?site=FanDuel"

#columns for table
columns = ["Lock", "Name", "Team", "Opp", "Pos", "ML", "O/U", "Mins", "Salary", "Points", "Value", "Exclude"]

#make soup of url
soup = ts.make_soup(url)

# rows = []
# if class_name is "":
# 	rows = soup.find_all('tr')
# else:
# 	rows = soup.find_all('tr', class_ = class_name)
# data = []
# for row in rows:
# 	cols = row.find_all('td')
# 	data_row = []
# 	for col in cols:
# 		data_row.append(col.find(text=True))
# 	data.append(data_row)
# return data

print soup.prettify()
# data = []
# table_body = soup.find('tbody', {"id": "players"})
# rows = table_body.findChildren('tr')
# for row in rows:
# 	data_row = []
# 	for col in row.find_all('td'):
# 		if col['class'][0] == "rwo-name":
# 			data_row.append("dilf")
# 			print "A"
# 		else:
# 			data_row.append(col.find(text=True))
# 		print col['class']
# 	data.append(data_row)

# df = ts.to_pandas_csv(data, "values.csv", columns)

# print df