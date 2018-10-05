import re
import sys
import praw
import time
import pprint
import operator
import datetime
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
	ticklist = []
	total_dict = Counter({})
	blacklist_words = ["YOLO", "TOS", "CEO", "CFO", "CTO", "DD", "BTFD", "WSB", "OK", "RH",
							 "KYS", "FD", "TYS", "US", "USA", "IT", "ATH", "RIP", "BMW", "GDP",
							 "OTM", "ATM", "ITM", "IMO", "LOL", "DOJ", "BE", "PR", "PC", "ICE",
							 "TYS", "ISIS", "PRAY", "PT", "FBI", "SEC", "GOD", "NOT", "POS", "COD",
							 "AYYMD", "FOMO", "TL;DR", "EDIT", "STILL", "LGMA", "WTF", "RAW", "PM",
							 "LMAO", "LMFAO", "ROFL", "EZ", "RED", "BEZOS", "TICK", "IS", "DOW"
							 "AM", "PM", "LPT", "GOAT", "FL", "CA", "IL", "PDFUA", "MACD", "HQ",
							 "OP", "DJIA", "PS", "AH", "TL", "DR", "JAN", "FEB", "JUL", "AUG",
							 "SEP", "SEPT", "OCT", "NOV", "DEC", "FDA", "IV", "ER", "SPX", "IPO",
							 "IPA", "URL"]

	if ('$' in body):
		index = body.find('$') + 1
		ticker = extract_ticker(body, index)
		
		if (ticker):
			if ticker in total_dict:
				total_dict[ticker] += 1
			else:
				total_dict[ticker] = 1
	
		# to avoid printing None
		if (ticker and ticker not in ticklist):
			ticklist.append(ticker)
	
	# checks for non-$ formatted comments
	word_list = re.sub("[^\w]", " ",  body).split()
	# print(word_list)
	for count, word in enumerate(word_list):
		if word.isupper() and len(word) != 1 and (word.upper() not in blacklist_words) and len(word) <= 5 and word.isalpha():
			try:
				# if the previous word is uppercase as well and doesn't have a length == 1, don't add it to the ticker list
				if word_list[count-1].isupper() and not len(word_list[count-1]) == 1:
					continue
				# if the next word is uppercase as well and doesn't have a length == 1, don't add it to the ticker list
				if word_list[count+1].isupper() and not len(word_list[count+1]) == 1:
					continue
			except:
				continue
		
			if (word):
				if word in total_dict:
					total_dict[word] += 1
				else:
					total_dict[word] = 1
		
			# to avoid printing None
			if (word and word not in ticklist):
				ticklist.append(word)

	return ticklist, total_dict

def get_url(key, value):
	mention = ("mentions", "mention") [value == 1]
	if (key == "ROPE"):
		return "${0}: [{1} {2}](https://www.homedepot.com/b/Hardware-Chains-Ropes-Rope/N-5yc1vZc2gr)".format(key, value, mention)
	else:
		return "${0}: [{1} {2}](https://finance.yahoo.com/quote/{0}?p={0})".format(key, value, mention)

def final_post(subreddit, reply):
	# finding the daily discussino thread to post
	title = get_date + " | Today's Top WSB Tickers"

	print("\nPosting...")
	subreddit.submit(title, selftext=reply)
	sys.stderr.write("Limit Reached. Try again in 10 minutes.\n")

def get_date():
	now = datetime.datetime.now()
	return now.strftime("%d-%m-%Y")

def setup(sub):
	if (sub == ""):
		sub = "wallstreetbets"

	# create a reddit instance
	reddit = praw.Reddit(client_id="your_id", client_secret="your_secret",
								username="wsbtickerbot", password="Re08.31!99", user_agent="wsbtickerbot")
	# create an instance of the subreddit
	subreddit = reddit.subreddit(sub)
	return subreddit


def main(mode, sub, num_submissions):
	ticklist = []
	total_dict = Counter({})
	reply = ""

	subreddit = setup(sub)
	new_posts = subreddit.new(limit=num_submissions)

	for count, post in enumerate(new_posts):
		# if we have not already viewed this post thread
		if (not post.clicked):
			# parse the post's title's text
			temp_list, temp_dict = parse_section(post.title)
			ticklist += temp_list
			total_dict += temp_dict
			
			comments = post.comments
			if (len(comments) > 0):
				for comment in comments:
					# without this, would throw AttributeError since the instance in this represents the "load more comments" option
					if isinstance(comment, MoreComments):
						continue
					temp_list, temp_dict = parse_section(comment.body)
					ticklist += temp_list
					total_dict += temp_dict

					# iterate through the comment's replies
					replies = comment.replies
					for rep in replies:
						# without this, would throw AttributeError since the instance in this represents the "load more comments" option
						if isinstance(rep, MoreComments):
							continue
						temp_list, temp_dict = parse_section(rep.body)
						ticklist += temp_list
						total_dict += temp_dict
			
			sys.stdout.write("\rProgress: {0} / {1} posts".format(count + 1, num_submissions))
			sys.stdout.flush()
			
			# ticklist = []

	# removes duplicates
	ticklist = set(ticklist)
	reply = "To help you YOLO your money away, here are all of the tickers mentioned in all the posts within the past 24 hours (and links to their Yahoo Finance page):"

	# will only iterate through the top 20 mentioned tickers
	for key, value in sorted(total_dict.items(), key=operator.itemgetter(1))[::-1][:20]:
		# ensures there aren't huge strings
		if len(key) > 5:
			continue

		url = get_url(key, value)
		reply += "\n\n" + url

	# post to the subreddit if it is in bot mode (i.e. not testing)
	if (not mode):
		final_post(subreddit, reply)
	else:
		print()
		print("Not posting to reddit because you're in test mode")
		print(reply)
		# sorted_dict = sorted(total_dict.items(), key=operator.itemgetter(1))[::-1]
		# pprint.pprint(sorted_dict)

if (__name__ == "__main__"):
	# USAGE: wsbtickerbot.py [ subreddit ] [ num_submissions ]
	mode = 0
	num_submissions = 250
	sub = "wallstreetbets"

	if (len(sys.argv) > 1):
		mode = 1
		sub = sys.argv[1]
	if (len(sys.argv) > 2):
		num_submissions = int(sys.argv[2])

	main(mode, sub, num_submissions)


# RIGHT NOW, THIS WILL ONLY POST THAT COMMENT ON THE DAILY DISCUSSION THREAD

# TO-DO:
# It will only scan each comment once for $, so you gotta fix this