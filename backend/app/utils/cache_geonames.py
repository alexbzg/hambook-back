#!/usr/bin/python3
#coding=utf-8

import json
from pathlib import Path
from collections import defaultdict
import re

import requests

PUBLIC_PATH = "/var/www/hambook-dev-public"
SRC_DIR = "https://download.geonames.org/export/dump/"
DST_DIR = f"{PUBLIC_PATH}/geonames_cache/"

countries_src = requests.get(f"{SRC_DIR}countryInfo.txt").text
countries = []

for country_line in countries_src.split("\n"):
    if not country_line.startswith('#'):
        try:
            value, _, _, _, label, _ = country_line.split("\t", 5)
            countries.append({'value': value, 'label': label})
        except:
            print(country_line)
countries.sort(key=lambda x: x['label'])
with open(f"{DST_DIR}countries.json", 'w', encoding="utf-8") as countries_dst:
    json.dump(countries, countries_dst)

regions_src = requests.get(f"{SRC_DIR}admin1CodesASCII.txt").text
regions = defaultdict(list)
RE_REGION = re.compile(r"^(\w+)\.(\w+)\t([^\t]+)\t.*$")

for region_line in regions_src.split("\n"):
    match = RE_REGION.match(region_line)
    if match:
        regions[match.group(1)].append({'value': match.group(2), 'label': match.group(3)})
    else:
        print(region_line)
for country in regions:
    country_dir = f"{DST_DIR}{country}"
    Path(country_dir).mkdir(exist_ok=True)
    regions[country].sort(key=lambda x: x['label'])
    with open(f"{country_dir}/regions.json", "w", encoding="utf-8") as regions_dst:
        json.dump(regions[country], regions_dst)

districts_src = requests.get(f"{SRC_DIR}admin2Codes.txt").text
districts = defaultdict(lambda: defaultdict(list))
RE_DISTRICT = re.compile(r"^(\w+)\.(\w+)\.(\w+)\t([^\t]+)\t.*$")

for district_line in districts_src.split("\n"):
    match = RE_DISTRICT.match(district_line)
    if match:
        districts[match.group(1)][match.group(2)].append({'value': match.group(3), 'label': match.group(4)})
    else:
        print(district_line)
for country in districts:
    country_dir = f"{DST_DIR}{country}"
    for region in districts[country]:
        districts[country][region].sort(key=lambda x: x['label'])
        with open(f"{country_dir}/{region}.json", "w", encoding="utf-8") as districts_dst:
            json.dump(districts[country][region], districts_dst)


