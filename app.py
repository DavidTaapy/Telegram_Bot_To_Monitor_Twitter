# Importing Required Libraries
import requests
import json
import time
import keyring

# Setting Twitter API Credentials
ApiKey = keyring.get_password("twitter", "apikey")
Secret = keyring.get_password("twitter", "secret")
BearerToken = keyring.get_password("twitter", "bearertoken")
AccessToken = keyring.get_password("twitter", "accesstoken")
AccessTokenSecret = keyring.get_password("twitter", "accesstokensecret")

# Telegram Bot Details
botUsername = "GimmeThemTweets_Bot"
chatID = "-641613358"
botAPI = keyring.get_password("Telegram", "API")

# List of users to follow
usernames = [
    "DataSerenity"  # @DataSerenity without the @
]

# List of user IDs
userIDs = {}

# List of user URLs
userURLs = {}

# Dict to contain last broadcasted tweet
broadcasted = {}

# Create_URL using user ID
def create_url(user_id):
    return "https://api.twitter.com/2/users/{}/tweets".format(user_id)

# Get list of user URLs
def generate_URLs():
    for username in usernames:
        user_id = userIDs[username]
        url = create_url(user_id)
        # Add url to a list to be used in the future to reduce overhead
        userURLs[username] = url

# Get parameters to filter tweets
def get_params():
    # Tweet fields are adjustable:
    # Options include:
    # attachments, author_id, context_annotations,
    # conversation_id, created_at, entities, geo, id,
    # in_reply_to_user_id, lang, non_public_metrics, organic_metrics,
    # possibly_sensitive, promoted_metrics, public_metrics, referenced_tweets,
    # source, text, and withheld
    return {"tweet.fields": "created_at"}

# Method required by bearer token authentication
def bearer_oauth(r):
    r.headers["Authorization"] = f"Bearer {BearerToken}"
    r.headers["User-Agent"] = "v2UserTweetsPython"
    return r

# Connect to the endpoint
def connect_to_endpoint(url, params):
    response = requests.request("GET", url, auth=bearer_oauth, params=params)
    if response.status_code != 200:
        raise Exception(
            "Request returned an error: {} {}".format(
                response.status_code, response.text
            )
        )
    return response.json()

# Get last tweeted messages
def get_last_tweeted():
    for username in usernames:
        params = get_params()
        url = userURLs[username]
        json_response = connect_to_endpoint(url, params)
        # Stores the created_at time for the users' last tweets
        broadcasted[url] = json_response['data'][0]['created_at']

# Send a telegram message
def send_notification(username, tweet):
    date, time = tweet['created_at'].split("T")
    time = time[:8]  # Get the time up to seconds precision
    message = "{} on {} at {}\n{}".format(username, date, time, tweet['text'])
    url = f"https://api.telegram.org/bot{botAPI}/sendMessage?chat_id={chatID}&text={message}"
    # Call URL
    requests.get(url)

# Create URL for ID retrieval
def create_ID_url(username, user_fields):
    userName = f"usernames={username}"
    url = "https://api.twitter.com/2/users/by?{}&{}".format(
        userName, user_fields)
    return url

# Endpoint for ID retrieval
def connect_to_ID_endpoint(url):
    response = requests.request("GET", url, auth=bearer_oauth,)
    if response.status_code != 200:
        raise Exception(
            "Request returned an error: {} {}".format(
                response.status_code, response.text
            )
        )
    return response.json()

# Get user IDs
def generate_IDs():
    for username in usernames:
        user_fields = "user.fields=description,created_at,public_metrics"
        url = create_ID_url(username, user_fields)
        json_response = connect_to_ID_endpoint(url)
        # print(json_response)
        userIDs[username] = int(json_response['data'][0]["id"])

# To run on program start
def main():
    startTime = time.time()  # Time the program was started
    # Generate a dict with user ID
    generate_IDs()
    # print(userIDs)
    # Generate a list of URLs
    generate_URLs()
    # print(userURLs)
    # Get last tweeted tweets for each users
    get_last_tweeted()
    # Run every 60 seconds
    while True:
        # Iterate through the list of users
        for username in usernames:
            params = get_params()
            url = userURLs[username]
            json_response = connect_to_endpoint(url, params)
            # print(json.dumps(json_response, indent = 4, sort_keys = True))
            # Filter out new Tweets
            tweets = [x for x in json_response["data"]
                      if x["created_at"] > broadcasted[url]]
            # Update last tweet time in broadcasted
            if tweets:
                broadcasted[url] = tweets[0]["created_at"]
            # Broadcast new tweet in telegram group
            for tweet in tweets:
                send_notification(username, tweet)
        # Sleep for remaining time left in three minutes
        # Three minutes interval to ensure that number of calls is within API limits
        time.sleep(180.0 - (time.time() - startTime) % 180.0)

# Execute on running program
if __name__ == "__main__":
    main()
