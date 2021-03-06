#!/usr/bin/env python
import tweepy
import schedule
import time
import datetime
from utils import *
import os
import config

url = "https://w4.minecraftserver.jp/api/ranking"
payload = {"type": "break", "duration": "daily"}    # 日間整地ランキング

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
        uuid = name_to_uuid(name)
        text = "@" + str(status.user.screen_name) + "\n" + name + ": \n"

        if uuid == "#null":
            text += name + "というmcidは存在しないヨ"
        else:
            # リプライに各文字列が含まれていたら対応したテキストを追加
            if "daily" in reply:
                text += daily_reply(uuid)
            if "weekly" in reply:
                text += weekly_reply(uuid)
            if "monthly" in reply:
                text += monthly_reply(uuid)
            if "daily" not in reply and "weekly" not in reply and "monthly" not in reply and len(reply) == 2:
                text += daily_reply(uuid) + weekly_reply(uuid) + monthly_reply(uuid)

        api.update_status(text, status.id)  # 返信
        return True

    def on_error(self, status_code):
        print('Got an error with status code: ' + str(status_code))
        return True

    def on_timeout(self):
        print('Timeout...')
        return True


# ツイート
def tweet(title: str, rm=True, rank={}):
    print("----tweet-----")
    print(daily_rank())
    text = random_unicode() + title + random_unicode() + "\n"
    if title == config.daily_title:
        text += dict_to_shaping_text(daily_rank()) + "#整地鯖"
        if rm:
            os.remove(config.daily_path)
    elif title == config.weekly_title:
        text += dict_to_shaping_text(weekly_rank()) + "#整地鯖"
        if rm:
            os.remove(config.weekly_path)
    elif title == config.monthly_title:
        text += dict_to_shaping_text(monthly_rank()) + "#整地鯖"
        if rm:
            os.remove(config.monthly_path)
    else:
        text += dict_to_shaping_text(rank)
    print(text)
    api.update_status(text) # ツイート


def update_ranking():
    b_daily_rank = daily_rank()

    # 日間整地ランキングを取得(100位まで)
    r_get = requests.get(url, params=payload)
    if r_get.status_code != requests.codes.ok:
        return
    r_json = r_get.json()
    ranks = r_json["ranks"].copy()

    # 日間整地ランキングの全データを取得(100位以降)
    while len(r_json["ranks"]) > 99:
        next_p = {"type": "break", "offset": str(len(ranks) - 1), "duration": "daily"}
        r_get = requests.get(url, params=next_p)
        r_json = r_get.json()
        ranks.extend(r_json["ranks"].copy())

    daily_rank_ = {}
    # uuidと整地量を対応させて保存(mcid変更に対応できるように)
    for rank in ranks:
        daily_rank_[rank["player"]["uuid"].replace("-", "")] = int(rank["data"]["raw_data"])

    diff_daily = sort_dict(sub_dict(daily_rank_, b_daily_rank))  # 更新前との差分

    # 各ランキング更新
    write_file(config.daily_path, sort_dict(daily_rank_))
    write_file(config.weekly_path, sort_dict(add_dict(weekly_rank(), diff_daily)))
    write_file(config.monthly_path, sort_dict(add_dict(monthly_rank(), diff_daily)))

    tweet(config.min30_title, rank=diff_daily)
    print_ranking(daily_rank())


def monthly_job():
    # scheduleだと毎月の処理ができない
    if datetime.datetime.today().day != 1:
        return
    tweet(config.monthly_title)


listener = Listener()
stream = tweepy.Stream(auth, listener, secure=True)
stream.filter(track=["@seichi_ranking"], is_async=True)

# 設定した時間に実行
schedule.every(30).minutes.do(update_ranking)
schedule.every().day.at("23:59").do(update_ranking)
schedule.every().day.at("00:00").do(monthly_job)
schedule.every().sunday.at("00:00").do(tweet, title=config.weekly_title)
schedule.every().day.at("00:00").do(tweet, title=config.daily_title)

while True:
    schedule.run_pending()
    time.sleep(1)
