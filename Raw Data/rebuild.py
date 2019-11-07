# coding=utf-8
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import sys
import os
import re
import json
import yaml
import time
import requests
from time import sleep
from datetime import timedelta
from tweepy import OAuthHandler
from tweepy.api import API as Twitter
from tweepy.error import TweepError
from tweepy.parsers import JSONParser

tweets = []
twits = []
source_tweets = []
source_twits = []

def read(path):
    with open(path, "r") as f:
        return json.load(f)


def dump(data, path):
    with open(path, "w") as f:
        json.dump(data, f)


def load_conf(path="config.yml"):
	#TODO if no/broken config
    stream = open(os.path.expanduser(path), "r")
    conf = yaml.load(stream)
    return conf


def rebuild(source_tweets):
	conf = load_conf()
	auth = OAuthHandler(conf["twitter"]["api"]["app"]["key"], conf["twitter"]["api"]["app"]["secret"])
	auth.set_access_token(conf["twitter"]["api"]["app"]["token"], conf["twitter"]["api"]["app"]["token_secret"])
	twitter = Twitter(auth, parser=JSONParser())
	try:
		for tweet in source_tweets:
			try:
				tw = rebuilt_tweet(tweet, twitter)
				if tw is not None:
					tweets.append(tw)
				if (len(tweets) % 20) == 0:
					print("Downloaded %d Tweets" % len(tweets))
			except TweepError as e:
				print("Error retrieving tweet #%s: %s" % (tweet["id"], str(e)))
			sleep(conf["twitter"]["api"]["pause"])
	except KeyboardInterrupt:
		print("Exit forced...")
	
# def rebuilt_twit(twit):
# 	conf = load_conf()
# 	#if no config/ids
# 	try:
# 		temptwit = requests.get('https://api.stocktwits.com/api/2/messages/show/' + str(twit["id"]) + '.json?access_token=' + conf["stocktwits"]["api"]["app"]["token"]).json()
# 		twit.update(temptwit)
# 		return twit

# 	except ValueError:
# 		return None

	
def rebuilt_tweet(tweet, client):
    status = client.get_status(tweet["id"])
    tweet.update(status)
    return tweet

def do_all(source_path):	
	#Read JSON and divide input into stocktwits and tweets
	conf = load_conf()
	source = read(source_path)
	print("%d tweets/twits found" % len(source))

	for inputdocument in source:
		if inputdocument["source"] == "twitter":
			source_tweets.append(inputdocument)
		elif inputdocument["source"] == "stocktwits":
			source_twits.append(inputdocument)


	#Twitter download
	estimated = (conf["twitter"]["api"]["pause"] * len(source_tweets)) + (conf["stocktwits"]["api"]["pause"] * len(source_twits))
	print("Dataset rebuilding will require about %s..." % timedelta(seconds=estimated))
	rebuild(source_tweets)
	

	# #Stocktwits download
	# for twit in source_twits:
	# 	twits.append(rebuilt_twit(twit))
	# 	if (len(twits) % 20) == 0:
	# 		print("Downloaded %d Twits" % len(twits))
	# 	sleep(conf["stocktwits"]["api"]["pause"])
		
	#Create new document
	#Merge twits and tweets
	# mergedlist = tweets + twits
	mergedlist = tweets
	target_path = re.sub("\.json$", "-twitter_full.json", source_path)
	dump(mergedlist, target_path)
	print("Finished!")


if __name__ == "__main__":
	if len(sys.argv) > 1:
		path = sys.argv[1]
		#source_path = path
		do_all(path)
	else:
		print("Usage: python rebuild.py <FILE.json>")

