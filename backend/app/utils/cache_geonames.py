#!/usr/bin/python3
#coding=utf-8

import json
from pathlib import Path
from collections import defaultdict
import re
from urllib.request import urlretrieve
import zipfile

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
            Path(f"{DST_DIR}{value}").mkdir(exist_ok=True)
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
geodata = defaultdict(lambda: defaultdict(lambda: {'districts': [], 'cities': []}))
RE_DISTRICT = re.compile(r"^(\w+)\.(\w+)\.(\w+)\t([^\t]+)\t.*$")

for district_line in districts_src.split("\n"):
    match = RE_DISTRICT.match(district_line)
    if match:
        geodata[match.group(1)][match.group(2)]['districts'].append(
                {'value': match.group(3), 'label': match.group(4)})
    else:
        print(district_line)

objects_zip_path = f"{DST_DIR}allCountries.zip"
urlretrieve(f"{SRC_DIR}allCountries.zip", objects_zip_path)

with zipfile.ZipFile(objects_zip_path, 'r') as zip_file:
    zip_file.extractall(DST_DIR)
Path(objects_zip_path).unlink()

objects_path = f"{DST_DIR}allCountries.txt"

with open(objects_path, 'r', encoding='utf-8') as objects_file:
    for object_line in objects_file:
        object = object_line.split("\t")
        if object[6] == 'P':
            geodata[object[8]][object[10] or '00']['cities'].append(object[1])

for country in geodata:
    country_dir = f"{DST_DIR}{country}"
    for region in geodata[country]:
        geodata[country][region]['districts'].sort(key=lambda x: x['label'])
        geodata[country][region]['cities'] = list(set(geodata[country][region]['cities']))
        geodata[country][region]['cities'].sort()
        with open(f"{country_dir}/{region}.json", "w", encoding="utf-8") as geodata_dst:
            json.dump(geodata[country][region], geodata_dst)




