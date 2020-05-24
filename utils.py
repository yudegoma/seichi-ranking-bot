import requests
import random
from collections import OrderedDict, Counter
import json

uuid_url = "https://api.mojang.com/user/profiles/"
name_url = "https://api.mojang.com/users/profiles/minecraft/"


def sort_dict(d: dict) -> dict:
    return OrderedDict(sorted(d.items(), key=lambda x: x[1], reverse=True))


def add_dict(d1: dict, d2: dict) -> dict:
    return dict(Counter(d1) + Counter(d2))


def sub_dict(d1: dict, d2: dict) -> dict:
    return dict(Counter(d1) - Counter(d2))


def random_unicode() -> chr:
    return chr(random.choice(
        (random.randrange(0x1F300, 0x1F64F), random.randrange(0x1F680, 0x1F6FA), random.randrange(0x1F90D, 0x1F9AA))))


def uuid_to_name(uuid: str) -> str:
    r_get = requests.get(uuid_url + uuid + "/names")
    return r_get.json()[len(r_get.json()) - 1]["name"]


def name_to_uuid(name: str) -> str:
    r_get = requests.get(name_url + name)
    print(r_get.status_code)
    if r_get.status_code != requests.codes.ok:
        return "#null"
    return r_get.json()["id"]


def dict_to_shaping_text(ranks: dict) -> str:
    i = 0
    result = ""
    for uuid, value in ranks.items():
        i += 1
        result += "{}位: {:>16}: {}\n".format(i, uuid_to_name(uuid), value)
        if i == 5:
            break
    return result


def print_ranking(ranks: dict):
    for k, v in ranks.items():
        print(k, v)


def read_file(path: str) -> dict:
    with open(path, "r") as f:
        return json.load(f)


def write_file(path: str, d: dict):
    with open(path, "w") as f:
        json.dump(d, f, indent=4)


