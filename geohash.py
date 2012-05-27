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
import hashlib, urllib, argparse, time, csv, json

parser = argparse.ArgumentParser(description="Calculate a geohash location based on the midnight price for BTC trades.")

subparsers = parser.add_subparsers(help="sub-commands", dest="parser")

globalhash_parser = subparsers.add_parser("globalhash", help="calculate the globalhash")
globalhash_parser.add_argument('-s', '--symbol', help="symbol of the market (default: mtgoxUSD)", default="mtgoxUSD")
globalhash_parser.add_argument('-m', '--map', help="print URL to a mapping service instead of displaying the raw latitude & longitude.", default="", choices=["google", "osm", "yahoo", "bing"])

graticule_parser = subparsers.add_parser("graticule", help="calculate the geohash of a graticule")
graticule_parser.add_argument('lat', help="latitude (integer part)", type=int)
graticule_parser.add_argument('lon', help="longitude (integer part)", type=int)
graticule_parser.add_argument('-s', '--symbol', help="symbol of the market (default: mtgoxUSD)", default="mtgoxUSD")
graticule_parser.add_argument('-m', '--map', help="print URL to a mapping service instead of displaying the raw latitude & longitude.", default="", choices=["google", "osm", "yahoo", "bing"])

list_symbols_parser = subparsers.add_parser("list-symbols", help="list all available symbols")

def get_midnight(thirtyw_rule):
    """Calculate unix timestamp of last midnight (UTC)"""
    utc_unix = time.time()
    midnight = utc_unix - utc_unix % 86400

    if thirtyw_rule:
        midnight -= 86400

    return midnight

def get_price(timestamp, symbol):
    """Returns the first price after the unix date in timestamp"""
    try:
        csvinfo = urllib.urlopen("http://bitcoincharts.com/t/trades.csv?symbol={0}&start={1}".format(symbol, int(timestamp)))
    except IOError as (errno, strerror):
        print "Could not retrieve data from bitcoincharts: " + str(strerror)
        raise SystemExit

    reader = csv.reader(csvinfo, delimiter=',')

    firstprice = -1

    try:
        firstprice = reader.next()[1]			# Price is in the second column
    except StopIteration:
        raise ValueError("No price data for symbol \"{0}\".".format(symbol))
    except IndexError:
        raise ValueError("Symbol \"{0}\" not found. Try another one.".format(symbol))

    return firstprice

def algorithm(date, price):
    """Calculate the geohash algorithm and return a tupel with the results for latitude & longitude"""
    thestring = str(date) + "-" + str(price)

    thehash = hashlib.md5(thestring).hexdigest()

    hexnum = (thehash[0:16], thehash[16:32])

    curpow = 1
    decnum = [0.0, 0.0]

    while curpow <= len(hexnum[0]):
        decnum[0] += int(hexnum[0][curpow-1], 16) * (1.0 / (16.0 ** curpow))
        decnum[1] += int(hexnum[1][curpow-1], 16) * (1.0 / (16.0 ** curpow))
        curpow += 1

    return decnum

def graticule(decnum, latitude, longitude):
    """Calculate the geohash coordinates for a graticule."""
    if latitude >= 0:
        latitude += decnum[0]
    else:
        latitude += decnum[0] * -1

    if longitude >= 0:
        longitude += decnum[1]
    else:
        longitude += decnum[1] * -1

    return (latitude, longitude)

def globalhash(decnum):
    """Calculate the globalhash coordinates."""
    latitude = decnum[0] * 180 - 90
    longitude = decnum[1] * 360 - 180

    return (latitude, longitude)

def print_coords(map, latitude, longitude):
    """Print the coordinates on the console."""
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

def list_symbols():
    try:
        btcinfo = urllib.urlopen("http://bitcoincharts.com/t/markets.json")
        jsoninfo = btcinfo.read()
        jsoninfo = json.loads(jsoninfo)

        for sym in jsoninfo:
            print sym["symbol"]
    except IOError as (errno, strerror):
        print "Could not retrieve data from bitcoincharts: " + str(strerror)
        raise SystemExit

#
# End of function definitions
#

args = parser.parse_args()

if args.parser == "graticule":
    if abs(args.lat) > 90 or abs(args.lon) > 180:
        raise ValueError("Graticule coordinates out of range.")

    # 30W Time Zone Rule (see http://wiki.xkcd.com/geohashing/30W)
    midnight = get_midnight(args.lat > -30)

    price = get_price(midnight, args.symbol)
    decnum = algorithm(date.today(), price)

    coords = graticule(decnum, args.lat, args.lon)
    print_coords(args.map.lower(), coords[0], coords[1])
elif args.parser == "globalhash":
    midnight = get_midnight(True)			# Globalhash is always with 30W rule.

    price = get_price(midnight, args.symbol)
    decnum = algorithm(date.today(), price)

    coords = globalhash(decnum)
    print_coords(args.map.lower(), coords[0], coords[1])
elif args.parser == "list-symbols":
    list_symbols()
