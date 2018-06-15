import sys
import praw
import operator
from collections import Counter

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
	ticklist   = []
	total_dict = Counter({})

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
	return ticklist, total_dict

def main(mode, sr, num_submissions):
	ticklist = []
	total_dict = Counter({})

	if (sr == ""):
		sr = "wallstreetbets"

	setup = praw.Reddit(client_id = "9uqRzVXVDVTm-Q",
						client_secret = "JItr3NUU7tRXxA8B2pRqvCJrYmU",
						username = "wsbtickerbot",
						password = "Re08.31!99",
						user_agent = "wsbtickerbot")
	subreddit = setup.subreddit(sr)
	new_wsb = subreddit.new(limit=num_submissions)

	print("Progress:")
	sys.stdout.flush()

	for count, submission in enumerate(new_wsb):
		if (not mode and "Daily Discussion Thread - " not in submission.title):
			continue

		# if we have not already viewed this post thread
		if (not submission.clicked):
			comments = submission.comments
			if (len(comments) > 0):
				for comment in comments:
					try:
						temp_list, temp_dict = parse_section(comment.body)
						ticklist   += temp_list
						total_dict += temp_dict
					except:
						continue

					replies = comment.replies
					if (len(replies) > 0):
						for reply in replies:
							try:
								temp_list, temp_dict = parse_section(reply.body)
								ticklist   += temp_list
								total_dict += temp_dict
							except:
								break

			if (ticklist):
				ticklist = set(ticklist)		# removes duplicates
				# print(sorted(ticklist))

				if (not mode):		# if it is in bot mode
					reply = "To help you YOLO your money away, here are all of the tickers mentioned"
					reply += "(and links to their Yahoo Finance page):"

					for key, value in total_dict.items():
						if (key == "ROPE"):
							if (value == 1):
								url = "[{}, {1} mention] (https://suicidepreventionlifeline.org)".format(key, value)
							else:
								url = "[{}, {1} mention] (https://suicidepreventionlifeline.org)".format(key, value)
						elif (key == "AMD"):
							if (value == 1):
								url = "[{0}, {1} mention] (https://finance.yahoo.com/quote/{0}?p={0})".format("AyyMD", value)
							else:
								url = "[{0} : {1} mentions] (https://finance.yahoo.com/quote/{0}?p={0})".format("AyyMD", value)
						else:
							if (value == 1):
								url = "[{0}, {1} mention] (https://finance.yahoo.com/quote/{0}?p={0})".format(key, value)
							else:
								url = "[{0} : {1} mentions] (https://finance.yahoo.com/quote/{0}?p={0})".format(key, value)
						reply += "\n\n" + url

					# print(reply)
					try:
						submission.reply(reply)
					except:
						sys.stderr.write("Limit Reached. Try again in 10 minutes.\n")
					break
			
			sys.stdout.write("\r{0} / {1} submissions".format(count + 1, num_submissions))
			sys.stdout.flush()
			
			ticklist = []

	sorted_dict = sorted(total_dict.items(), key=operator.itemgetter(1))[::-1]
	print()
	print(sorted_dict)

if (__name__ == "__main__"):
	# USAGE: wsbtickerbot.py [ subreddit ] [ num_submissions ]

	mode = 0
	num_submissions = 100
	sr = ""

	if (len(sys.argv) > 1):
		mode = 1
		sr = sys.argv[1]
	if (len(sys.argv) > 2):
		num_submissions = int(sys.argv[2])

	main(mode, sr, num_submissions)


# RIGHT NOW, THIS WILL ONLY POST THAT COMMENT ON THE DAILY DISCUSSION THREAD

# TO-DO:
# It will only scan each comment once for $, so you gotta fix this