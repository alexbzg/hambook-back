#!/usr/bin/python3
#coding=utf-8

import json
from pathlib import Path

PUBLIC_PATH = "/var/www/hambook-dev-public"
DST_DIR = f"{PUBLIC_PATH}/countries+states+cities/"

with open(f"{PUBLIC_PATH}/countries+states+cities.json", 'r', encoding="utf-8") as src:
    data = json.load(src)
    for country in data:
        country_dir = f"{DST_DIR}{country['id']}"
        Path(country_dir).mkdir()
        for state in country["states"]:
            with open(f"{country_dir}/{state['id']}.json", "w", encoding="utf-8") as state_dst:
                json.dump(state, state_dst)
            del state['cities']
        with open(f"{country_dir}/states.json", "w", encoding="utf-8") as states_dst:
            json.dump(country['states'], states_dst)
        del country['states']
    with open(f"{DST_DIR}countries.json", 'w', encoding="utf-8") as countries_dst:
        json.dump(data, countries_dst)



