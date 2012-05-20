#!/usr/bin/python

# Copyright (C) 2011 Mark Holmquist
# Copyright (C) 2011, 2012 Michael Bemmerl

# This script is free software, licensed under the GPLv3, of which you should have received a copy with this software.
# If you didn't, I apologize, but you'll be able to find it at /usr/share/common-licences/GPL-3 or http://www.gnu.org/licenses/gpl-3.0.txt

# This script will calculate a geohash location for you based on the first price at a market for BTC trades after midnight (UTC).
# Usually, people use the DJIA for this algorithm, but I didn't think that was nerdy enough :)
# It will also automagically give you a link to a google map to the location.
# If you'd like any help with it, don't hesitate to open up an issue at github.
# Have fun!

from datetime import date
import hashlib
import urllib
import argparse
import time
import csv

parser = argparse.ArgumentParser(description="Calculate a geohash location based on the opening price for BTC trades.")
parser.add_argument('lat', help="latitude (integer part)", type=int)
parser.add_argument('lon', help="longitude (integer part)", type=int)
parser.add_argument('-s', '--symbol', help="symbol of the market (default: mtgoxUSD)", default="mtgoxUSD")
parser.add_argument('-m', '--map', help="print URL to a mapping service instead of displaying the raw latitude & longitude.", default="", choices=["google", "osm", "yahoo", "bing"])

args = parser.parse_args()

latitude = args.lat
longitude = args.lon
symbol = args.symbol
map = args.map.lower()

# Calculate unix timestamp of last midnight (UTC)
utc_unix = time.time()
midnight = utc_unix - utc_unix % 86400

try:
    csvinfo = urllib.urlopen("http://bitcoincharts.com/t/trades.csv?symbol={0}&start={1}".format(symbol, int(midnight)))
except IOError as (errno, strerror):
    print "Could not retrieve data from bitcoincharts: " + str(strerror)
    raise SystemExit

reader = csv.reader(csvinfo, delimiter=',')

firstprice = -1

try:
    # Price is in the second column
    firstprice = reader.next()[1]
except StopIteration:
    raise ValueError("No price data for symbol \"{0}\".".format(symbol))
except IndexError:
    raise ValueError("Symbol \"{0}\" not found. Try another one.".format(symbol))

thestring = str(date.today()) + "-" + str(firstprice)

thehash = hashlib.md5(thestring).hexdigest()

hexnum = (thehash[0:16], thehash[16:32])

curpow = 1
decnum = [0.0, 0.0]

while curpow <= len(hexnum[0]):
    decnum[0] += int(hexnum[0][curpow-1], 16) * (1.0 / (16.0 ** curpow))
    decnum[1] += int(hexnum[1][curpow-1], 16) * (1.0 / (16.0 ** curpow))
    curpow += 1

if latitude >= 0:
    latitude += decnum[0]
else:
    latitude += decnum[0] * -1

if longitude >= 0:
    longitude += decnum[1]
else:
    longitude += decnum[1] * -1

url = ""

if map == "google":
    url = "http://maps.google.com/maps?q={0},{1}({2})&iwloc=A"
elif map == "osm":
    url = "http://osm.org/?mlat={0}&mlon={1}&zoom=12"
elif map == "yahoo":
    url = "http://maps.yahoo.com/maps_result?ard=1&mag=9&lat={0}&lon={1}"
elif map == "bing":
    url = "http://www.bing.com/maps/?q={0}+{1}&lvl=11"

if map != "":
    print url.format(latitude, longitude, "Geohash+for+" + str(date.today()))
else:
    print "latitude: " + str(latitude)
    print "longitude: " + str(longitude)
