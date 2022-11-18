import pandas as pd
from dotenv import load_dotenv
import tweepy as tw
import time
load_dotenv()
import os
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
analyzer = SentimentIntensityAnalyzer()

from my_pyfunctions import functions

consumer_key=os.environ.get("sWH8ijde98DqHvQRgp7XPZyJw")
consumer_secret=os.environ.get("pC9hcMPj9eA283OFWzgC1tLxLSdJxAm0xG3EP0oknPqykBQKKM")
access_token=os.environ.get("2360728153-oYdm2KeZ9Dqcybn7hAlvzSLEfbvXyW4UbPnGe8q")
access_token_secret=os.environ.get("0WxOZ7apjf8lodRY0IK5FihB5QS0adf3G38oq3CQNkgfT")
output_file=os.environ.get("tweet.csv")

# Tweeter API
auth = tw.OAuthHandler('sWH8ijde98DqHvQRgp7XPZyJw', 'pC9hcMPj9eA283OFWzgC1tLxLSdJxAm0xG3EP0oknPqykBQKKM')
auth.set_access_token('2360728153-oYdm2KeZ9Dqcybn7hAlvzSLEfbvXyW4UbPnGe8q', '0WxOZ7apjf8lodRY0IK5FihB5QS0adf3G38oq3CQNkgfT')
api = tw.API(auth)

# create empty df
tesla_df = pd.DataFrame(columns=['datetime','id', 'username', 'followers_count','verified_status','text','retweets','tweet_url','location'])

#print(tesla_df)
tweets_list = []
#st = time.time()
st = time.time()
class MyListener(tw.Stream):
    def on_status(self, status):
        # Dont store retweets
        global st
        end = time.time()
        lapsed_time = (end-st)/60
        #print(f"CALLED AGAIN: {len(tweets_list)} {lapsed_time}")
        
        if status.retweeted or 'RT @' in status.text:
            return
        
        if status.truncated:
            # fetch full text
            text = status.extended_tweet['full_text']
        else:
            text = status.text
        location = status.coordinates
        if location:
            location = str(status.coordinates['coordinates'])
        tweet_url = f"https://twitter.com/twitter/statuses/{status.id}"
        while True:
            try:
                if 'tesla' in text.lower():
                    #print("tesla found")
                    tweets_list.append([status.created_at,status.id,status.user.name,status.user.followers_count,
                    status.user.verified,text,status.retweet_count,tweet_url,location])

                    if len(tweets_list) >= 100 and lapsed_time >= 30:
                        st = time.time()
                        for item in tweets_list:
                            tesla_df.loc[len(tesla_df)] = item

                        # create a copy of the df as the original df's data is to be deleted. pass every copy to a diff function
                        tesla_df_copy = tesla_df.copy()
                        
                        # call functions to process tweets
                        start_time = time.time()
                        functions.write_raw_tweets_to_s3(tesla_df_copy,output_file)    
                        
                        # clear both df and original tweets list
                        end_time = time.time()
                        print("PROCESSING TIME IS: ", end_time - start_time)
                        tesla_df.drop(tesla_df.index, inplace=True)
                        tweets_list.clear()               
                                           
                return True 
                    
            except BaseException as e:
                print("Error on_data: %s" % str(e))
            return True

    def on_error(self, status):
        print('Disconnected...')
        if status.status_code == 420:
            return False
        print('Streaming error (status code {})'.format(status.status_code))

        return True

if __name__=='__main__': 
    twitter_stream = MyListener(
    consumer_key, consumer_secret,
    access_token, access_token_secret
    )   
    twitter_stream.filter(track=['layoffs'],languages=['en'])



