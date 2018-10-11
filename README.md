# wsbtickerbot

wsbtickerbot is a Reddit bot, developed utilizing the Reddit PRAW API, that scrapes the entirety of r/wallstreetbets over a 24 hour period, collects all the tickers mentioned, and then performs sentiment analysis on the context. The sentiment analysis is used to classify the stocks into three categories: bullish, neutral, and bearish.

While the intention of this bot was to simply create another talking point within the subreddit, it has evolved into much more. Future plans include, but are not limited to:
- storing all collected data in a SQLite database
- utilize this data to perform simple linear regression to determine market trends from mentions and sentiment from r/wallstreetbets
