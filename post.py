from instabot import Bot
import tweepy
import os
import json
import sys
import geocoder
import random
from PIL import Image, ImageDraw, ImageFont

# API Keys and Tokens
consumer_key = os.environ['API_KEY']
consumer_secret = os.environ['API_SECRET_KEY']
access_token = os.environ['ACCESS_TOKEN']
access_token_secret = os.environ['ACCESS_TOKEN_SECRET']

# Authorization and Authentication
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth)

LOCATION = 'France'

TWEETS_PER_TREND = 3


class TweetTrendsAnalyzer(object):
    """
    Get the trends and pick the most popular tweets for a random trend
    """

    def __init__(self):
        self.trends = []
        self.final_tweets = []

    def displayTweet(self, tweetToDisplay):
        print("--------------------------")
        print(f"Tweet ID : {tweetToDisplay.id}")
        print(tweetToDisplay.full_text)
        print(
            f"{tweetToDisplay.favorite_count} FAV & {tweetToDisplay.retweet_count} RT")

    def containsLink(self, tweet):
        return "https" in tweet.full_text

    def getTrends(self):
        available_loc = api.trends_available()
        # writing a JSON file that has the available trends around the world
        with open("available_locs_for_trend.json", "w") as wp:
            wp.write(json.dumps(available_loc, indent=1))

        # Trends for Specific Country
        loc = LOCATION    # location as argument variable
        # getting object that has location's latitude and longitude
        g = geocoder.osm(loc)

        closest_loc = api.trends_closest(g.lat, g.lng)
        self.trends = api.trends_place(closest_loc[0]['woeid'])
        # writing a JSON file that has the latest trends for that location
        with open("twitter_{}_trend.json".format(loc), "w") as wp:
            wp.write(json.dumps(self.trends, indent=1))

    def getPopularTweetsInRandomTrend(self):

        random_trend = random.choice(self.trends[0]['trends'])

        print(f"Trend : {random_trend['name']}")

        # Get the tweets related to the trend chosen
        tweets = api.search(random_trend['query'], result_type="popular",
                            tweet_mode="extended", include_entities=True, count=100, lang='fr')

        for tweet in tweets:
            if self.containsLink(tweet):
                continue

            tweet_popularity = tweet.retweet_count + tweet.favorite_count

            if len(self.final_tweets) < TWEETS_PER_TREND:  # Populate the final_tweets list
                self.final_tweets.append(tweet)
            else:
                # Only keep the most popular tweets
                for _tweet in self.final_tweets:
                    _tweet_pop = _tweet.retweet_count + _tweet.favorite_count
                    if tweet_popularity > _tweet_pop:
                        self.final_tweets.remove(_tweet)
                        self.final_tweets.append(tweet)
                        break


def text_wrap(text, font, max_width):
    """Wrap text base on specified width. 
    This is to enable text of width more than the image width to be display
    nicely.
    @params:
        text: str
            text to wrap
        font: obj
            font of the text
        max_width: int
            width to split the text with
    @return
        lines: list[str]
            list of sub-strings
    """
    lines = []

    # If the text width is smaller than the image width, then no need to split
    # just add it to the line list and return
    if font.getsize(text)[0] <= max_width:
        lines.append(text)
    else:
        # split the line by spaces to get words
        words = text.split(' ')
        i = 0
        # append every word to a line while its width is shorter than the image width
        while i < len(words):
            line = ''
            while i < len(words) and font.getsize(line + words[i])[0] <= max_width:
                line = line + words[i] + " "
                i += 1
            if not line:
                line = words[i]
                i += 1
            lines.append(line)
    return lines


if __name__ == "__main__":

    # 1. Pick a random trend x
    # 2. Pick 3 tweets from it x
    # 3. Tweet to Picture x
    # 4. Upload the Pic to Instagram x

    TA = TweetTrendsAnalyzer()
    TA.getTrends()
    while len(TA.final_tweets) == 0:
        TA.getPopularTweetsInRandomTrend()

    for tweet in TA.final_tweets:
        TA.displayTweet(tweet)

    tweetToDisplay = TA.final_tweets[-1]

    colorBackground = "white"
    colorText = "black"
    fontPath = "C:/Users/Lenovo/Documents/insta-bot/fonts/Roboto-Bold.ttf"
    width, height = 1080, 1080

    text = tweetToDisplay.full_text

    image = Image.new('RGB', (width, height), colorBackground)

    # Resize the image

    img_w = image.size[0]
    img_h = image.size[1]
    wpercent = (width/float(img_w))
    hsize = int((float(img_h)*float(wpercent)))
    rmg = image.resize((width, hsize), Image.ANTIALIAS)

    font = ImageFont.truetype(font=fontPath, size=60)
    lines = text_wrap(text, font, rmg.size[0]-50)
    line_height = font.getsize('hg')[1]

    # Create draw object
    draw = ImageDraw.Draw(rmg)
    # Draw text on image
    color = 'rgb(0,0,0)'  # Black color
    y = 10
    for line in lines:
        # w, h = draw.textsize(line, font=font)
        draw.text((50, 50+y), line, fill=color, font=font)
        y = y + line_height  # update y-axis for new line

    rmg.save(
        f"C:/Users/Lenovo/Documents/insta-bot/tweets/{tweetToDisplay.id}.jpg", "JPEG")

    bot = Bot()

    bot.login(username=os.environ['INSTA_USER'],
              password=os.environ['INSTA_PASS'])
    bot.upload_photo(f"C:/Users/Lenovo/Documents/insta-bot/tweets/{tweetToDisplay.id}.jpg",
                     caption="Suivez nous pour plus de tweets ! @francetoptweet #twitter #trends #toptweets")
