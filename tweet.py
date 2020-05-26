#!/usr/bin/env python
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


# reply
class Listener(tweepy.StreamListener):

    def on_status(self, status):
        if str(status.user.screen_name) == "seichi_ranking" or status.retweeted or "RT @" in status.text:
            return True

        reply = status.text.split(" ")
        while "" in reply:
            reply.remove("")
            
        name = reply[len(reply) - 1]
        if name == "@seichi_ranking":
            return True
        uuid = name_to_uuid(name)
        text = "@" + str(status.user.screen_name) + "\n" + name + ": \n"

        if uuid == "#null":
            text += name + "というmcidは存在しないヨ"
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
def tweet(title: str, rank={}):
    print("----tweet-----")
    print(daily_rank())
    text = random_unicode() + title + random_unicode() + "\n"
    if title == config.daily_title:
        text += dict_to_shaping_text(daily_rank()) + "#整地鯖"
        os.remove(config.daily_path)
    elif title == config.weekly_title:
        text += dict_to_shaping_text(weekly_rank()) + "#整地鯖"
        os.remove(config.weekly_path)
    elif title == config.monthly_title:
        text += dict_to_shaping_text(monthly_rank()) + "#整地鯖"
        os.remove(config.monthly_path)
    else:
        text += dict_to_shaping_text(rank)
    print(text)
    api.update_status(text)


def update_ranking():
    b_daily_rank = daily_rank()

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

    daily_rank_ = {}
    for rank in ranks:
        daily_rank_[rank["player"]["uuid"].replace("-", "")] = int(rank["data"]["raw_data"])

    diff_daily = sort_dict(sub_dict(daily_rank_, b_daily_rank))  # 更新前との差分

    # 各ランキング更新
    write_file(config.daily_path, sort_dict(daily_rank_))
    write_file(config.weekly_path, sort_dict(add_dict(weekly_rank(), diff_daily)))
    write_file(config.monthly_path, sort_dict(add_dict(monthly_rank(), diff_daily)))

    tweet(config.min30_title, diff_daily)
    print_ranking(daily_rank())


def monthly_job():
    if datetime.datetime.today().day != 1:
        return
    tweet(config.monthly_title)


listener = Listener()
stream = tweepy.Stream(auth, listener, secure=True)
stream.filter(track=["@seichi_ranking"], is_async=True)

schedule.every(30).minutes.do(update_ranking)
schedule.every().day.at("23:59").do(update_ranking)
schedule.every().day.at("00:00").do(monthly_job)
schedule.every().sunday.at("00:00").do(tweet, title=config.weekly_title)
schedule.every().day.at("00:00").do(tweet, title=config.daily_title)

while True:
    schedule.run_pending()
    time.sleep(1)
