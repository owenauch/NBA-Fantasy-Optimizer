from bs4 import BeautifulSoup
from urllib2 import urlopen
import csv
import pandas
import TableScraper as ts

#url of table with values
url = "http://www.rotowire.com/daily/NBA/optimizer.php?site=FanDuel"

#columns for table
columns = ["Player", "Value"]

#make soup of url
soup = ts.make_soup(url)

table = ts.lol_table(soup)
