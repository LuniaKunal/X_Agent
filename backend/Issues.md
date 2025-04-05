# Fix 

Sentiment_Service.py file 
-> Tweet['sentiment'] is not subscribed object.

This file need to be updated to fix the issue.

Please Refer Image.png file of the Last result.

The Full Result - Test_output.json


Attempt 1:
After adding 10 Tweets and 100 replies --> 2918.34 Sec
Some Issues are there are multiple tweets with same id mentioned as Replys

Attempt 2:
After adding 10 Tweets and 100 replies --> 116.54 Sec

Attempt 3:
After adding 10 Tweets and 1250 replies --> 350.23 Sec

Remove tweet_model.py , analysis_model.py  --> Done 

sentiment_service.py --> fix point No. 8


# In Twitter_Service.py file 
--> Not using get_tweet function
--> fetch_tweet_and_replies function The issue was of waiting until batch.next  || For now it has been removed.


# Update fetch_user_tweets_and_replies function ::
--> This for now only fetch tweets and not replies there are functions made for replies use that.
--> Also while calling this function the issue is that while loop not working correctly. eg - When asked of 5 tweets max it gives 16 tweets or some random len of tweets.
        ---> Check Line:: 208 tweet_batch fetch more no. of tweets than required.

--> Fix Line:: 221 --> ERROR:service.twitter_service:Error in fetch_user_tweets_and_replies: {'code': '22007', 'details': None, 'hint': None, 'message': 'invalid input syntax for type timestamp with time zone: ""'} The issue is with the date format of the tweet


# Analysis @get route Update summary and remove tweets from response check schemas To Update Response Schema.
--> Analysis get routes has been made clear just need to solve the summery data issue as we are unable to get this --> check check.json file


# Check the analysis @get pipeline We are unable to fetch top positive and negative tweets.

## Now Create Frontend of the application Check Previous history in Claude as we have already given the prompt.

# Check twitter_service file  as we are unable to fetch replies.
--> One of the approach is that don't check replies['id'] for the replies.