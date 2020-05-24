import tweepy
import schedule
import time
import datetime
from utils import *
import os
import config

url = "https://w4.minecraftserver.jp/api/ranking"
payload = {"type": "break", "duration": "daily"}

auth = tweepy.OAuthHandler(config.CK, config.CS)
auth.set_access_token(config.AT, config.AS)

api = tweepy.API(auth)


def daily_reply(uuid: str) -> str:
    return ("daily: " + str(daily_rank[uuid]) + "\n") if uuid in daily_rank else "daily: 0\n"


def weekly_reply(uuid: str) -> str:
    return ("weekly: " + str(weekly_rank[uuid]) + "\n") if uuid in weekly_rank else "weekly: 0\n"


def monthly_reply(uuid: str) -> str:
    return ("monthly: " + str(monthly_rank[uuid]) + "\n") if uuid in monthly_rank else "monthly: 0\n"


# reply
class Listener(tweepy.StreamListener):

    def on_status(self, status):
        if str(status.user.screen_name) == "seichi_ranking" or status.retweeted or "RT @" in status.text:
            return True

        reply = status.text.split(" ")
        while "" in reply:
            reply.remove("")
        name = reply[len(reply) - 1]
        uuid = name_to_uuid(name)
        text = "@" + str(status.user.screen_name) + "\n" + name + ": \n"

        if uuid == "#null":
            text = name + "というmcidは存在しないヨ"
        else:
            if "daily" in reply:
                text += daily_reply(uuid)
            if "weekly" in reply:
                text += weekly_reply(uuid)
            if "monthly" in reply:
                text += monthly_reply(uuid)
            if "daily" not in reply and "weekly" not in reply and "monthly" not in reply and len(reply) == 2:
                text += daily_reply(uuid) + weekly_reply(uuid) + monthly_reply(uuid)

        api.update_status(text, status.id)
        return True

    def on_error(self, status_code):
        print('Got an error with status code: ' + str(status_code))
        return True

    def on_timeout(self):
        print('Timeout...')
        return True


# ツイート
def tweet(ranks: dict, rank_name: str):
    text = random_unicode() + rank_name + random_unicode() + "\n" + dict_to_shaping_text(ranks)
    if rank_name != "ざっくり30分整地量ランキング":
        text += "#整地鯖"

    api.update_status(text)
    if rank_name == "日間整地量ランキング":
        os.remove("./daily.json")
    if rank_name == "週間整地量ランキング":
        os.remove("./weekly.json")
    if rank_name == "月間整地量ランキング":
        os.remove("./monthly.json")
    ranks.clear()


def update_ranking():
    global daily_rank, weekly_rank, monthly_rank

    b_daily_rank = daily_rank.copy()
    daily_rank = {}
    r_get = requests.get(url, params=payload)
    if r_get.status_code != requests.codes.ok:
        return
    r_json = r_get.json()
    ranks = r_json["ranks"].copy()
    while len(r_json["ranks"]) > 99:
        next_p = {"type": "break", "offset": str(len(ranks) - 1), "duration": "daily"}
        r_get = requests.get(url, params=next_p)
        r_json = r_get.json()
        ranks.extend(r_json["ranks"].copy())

    for rank in ranks:
        daily_rank[rank["player"]["uuid"].replace("-", "")] = int(rank["data"]["raw_data"])

    diff_daily = sort_dict(sub_dict(daily_rank, b_daily_rank))  # 更新前との差分

    # 各ランキング更新
    daily_rank = sort_dict(daily_rank)
    weekly_rank = sort_dict(add_dict(weekly_rank, diff_daily))
    monthly_rank = sort_dict(add_dict(monthly_rank, diff_daily))
    write_file("daily.json", daily_rank)
    write_file("weekly.json", weekly_rank)
    write_file("monthly.json", monthly_rank)

    tweet(diff_daily, "ざっくり30分整地量ランキング")
    print_ranking(daily_rank)


def monthly_job():
    if datetime.datetime.today().day != 1:
        return
    tweet(monthly_rank, "月間整地量ランキング")


listener = Listener()
stream = tweepy.Stream(auth, listener, secure=True)
stream.filter(track=["@seichi_ranking"], is_async=True)

if os.path.exists("./daily.json"):
    daily_rank = read_file("./daily.json")
else:
    daily_rank = {}
if os.path.exists("./weekly.json"):
    weekly_rank = read_file("./weekly.json")
else:
    weekly_rank = {}
if os.path.exists("./monthly.json"):
    monthly_rank = read_file("./monthly.json")
else:
    monthly_rank = {}

schedule.every().day.at("23:59").do(update_ranking)
schedule.every().day.at("00:00").do(monthly_job)
schedule.every().sunday.at("00:00").do(tweet, ranks=weekly_rank, rank_name="週間整地量ランキング")
schedule.every().day.at("00:00").do(tweet, ranks=daily_rank, rank_name="日間整地量ランキング")
schedule.every(30).minutes.do(update_ranking)

while True:
    schedule.run_pending()
    time.sleep(1)
