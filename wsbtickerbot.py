import re
import sys
import praw
import time
import pprint
import operator
import datetime
from iexfinance import Stock as IEXStock
from collections import Counter
from praw.models import MoreComments

def extract_ticker(body, start_index):
	""" Given a starting index and text, this will extract the ticker, return None if it is incorrectly formatted """
	count  = 0
	ticker = ""

	for char in body[start_index:]:
		# if it should return
		if not char.isalpha():
			# if there aren't any letters following the $
			if (count == 0):
				return None

			return ticker.upper()
		else:
			ticker += char
			count += 1

	return ticker.upper()

def parse_section(body):
	""" Parses the body of each comment/reply """
	td_temp = Counter({})
	blacklist_words = ["YOLO", "TOS", "CEO", "CFO", "CTO", "DD", "BTFD", "WSB", "OK", "RH",
							 "KYS", "FD", "TYS", "US", "USA", "IT", "ATH", "RIP", "BMW", "GDP",
							 "OTM", "ATM", "ITM", "IMO", "LOL", "DOJ", "BE", "PR", "PC", "ICE",
							 "TYS", "ISIS", "PRAY", "PT", "FBI", "SEC", "GOD", "NOT", "POS", "COD",
							 "AYYMD", "FOMO", "TL;DR", "EDIT", "STILL", "LGMA", "WTF", "RAW", "PM",
							 "LMAO", "LMFAO", "ROFL", "EZ", "RED", "BEZOS", "TICK", "IS", "DOW"
							 "AM", "PM", "LPT", "GOAT", "FL", "CA", "IL", "PDFUA", "MACD", "HQ",
							 "OP", "DJIA", "PS", "AH", "TL", "DR", "JAN", "FEB", "JUL", "AUG",
							 "SEP", "SEPT", "OCT", "NOV", "DEC", "FDA", "IV", "ER", "IPO",
							 "IPA", "URL", "MILF", "BUT", "SSN", "FIFA", "USD", "CPU"]

	if '$' in body:
		index = body.find('$') + 1
		ticker = extract_ticker(body, index)
		
		if ticker and ticker not in blacklist_words:
			if ticker in td_temp:
				td_temp[ticker] += 1
			else:
				td_temp[ticker] = 1
	
	# checks for non-$ formatted comments, splits every body into list of words
	word_list = re.sub("[^\w]", " ",  body).split()
	for count, word in enumerate(word_list):
		# initial screening of words
		if word.isupper() and len(word) != 1 and (word.upper() not in blacklist_words) and len(word) <= 5 and word.isalpha():
			# sends request to IEX API to determine whether the current word is a valid ticker
			# if it isn't, it'll return an error and therefore continue on to the next word
			try:
				# special case for $ROPE
				if word is not "ROPE":
					price = IEXStock(word).get_price()
			except:
				continue
		
			# add/adjust value of dictionary
			if word in td_temp:
				td_temp[word] += 1
			else:
				td_temp[word] = 1

	return td_temp

def get_url(key, value, total_count):
	# determine whether to use plural or singular
	mention = ("mentions", "mention") [value == 1]
	# special case for $ROPE
	if key == "ROPE":
		return "${0}: [{1} {2} ({3}% of all mentions)](https://www.homedepot.com/b/Hardware-Chains-Ropes-Rope/N-5yc1vZc2gr)".format(key, value, mention, int(value / total_count * 100))
	else:
		return "${0}: [{1} {2} ({3}% of all mentions)](https://finance.yahoo.com/quote/{0}?p={0})".format(key, value, mention, int(value / total_count * 100))

def final_post(subreddit, text):
	# finding the daily discussino thread to post
	title = get_date + " | Today's Top WSB Tickers"

	print("\nPosting...")
	subreddit.submit(title, selftext=text)
	sys.stderr.write("Limit Reached. Try again in 10 minutes.\n")

def get_date():
	now = datetime.datetime.now()
	return now.strftime("%d-%m-%Y")

def setup(sub):
	if sub == "":
		sub = "wallstreetbets"

	# create a reddit instance
	reddit = praw.Reddit(client_id="client_id", client_secret="client_secret",
								username="username", password="password", user_agent="wsbtickerbot")
	# create an instance of the subreddit
	subreddit = reddit.subreddit(sub)
	return subreddit


def main(mode, sub, num_submissions):
	total_dict = Counter({})
	text = ""
	total_count = 0
	within24_hrs = False

	subreddit = setup(sub)
	new_posts = subreddit.new(limit=num_submissions)

	for count, post in enumerate(new_posts):
		# if we have not already viewed this post thread
		if not post.clicked:
			# parse the post's title's text
			temp_dict = parse_section(post.title)
			total_dict += temp_dict

			# to determine whether it has gone through all posts in the past 24 hours
			if "Daily Discussion Thread - " in post.title:
				if not within24_hrs:
					within24_hrs = True
				else:
					print("\nTotal posts searched: " + str(count) + "\nTotal ticker mentions: " + str(total_count))
					break
			
			# search through all comments and replies to comments
			comments = post.comments
			for comment in comments:
				# without this, would throw AttributeError since the instance in this represents the "load more comments" option
				if isinstance(comment, MoreComments):
					continue
				temp_dict = parse_section(comment.body)
				total_dict += temp_dict

				# iterate through the comment's replies
				replies = comment.replies
				for rep in replies:
					# without this, would throw AttributeError since the instance in this represents the "load more comments" option
					if isinstance(rep, MoreComments):
						continue
					temp_dict = parse_section(rep.body)
					total_dict += temp_dict
			
			# update the progress count
			sys.stdout.write("\rProgress: {0} / {1} posts".format(count + 1, num_submissions))
			sys.stdout.flush()

	text = "To help you YOLO your money away, here are all of the tickers mentioned at least 10 times in all the posts within the past 24 hours (and links to their Yahoo Finance page):"

	# will break as soon as it hits a ticker with fewer than 10 mentions
	for key, value in sorted(total_dict.items(), key=operator.itemgetter(1))[::-1]:
		if value < 10:
			break
		
		url = get_url(key, value, sum(total_dict.values()))
		text += "\n\n" + url

	# post to the subreddit if it is in bot mode (i.e. not testing)
	if not mode:
		final_post(subreddit, text)
	# testing
	else:
		print("\nNot posting to reddit because you're in test mode\n")
		# print(text)
		sorted_dict = sorted(total_dict.items(), key=operator.itemgetter(1))[::-1]
		pprint.pprint(sorted_dict)

if __name__ == "__main__":
	# USAGE: wsbtickerbot.py [ subreddit ] [ num_submissions ]
	mode = 0
	num_submissions = 250
	sub = "wallstreetbets"

	if len(sys.argv) > 2:
		mode = 1
		num_submissions = int(sys.argv[2])

	main(mode, sub, num_submissions)