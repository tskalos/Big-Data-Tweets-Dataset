import asyncio
import random
import time
import os
import csv
from datetime import datetime
from configparser import ConfigParser
from twikit import Client, TooManyRequests

# ✅ Φιλτράρουμε tweets ΜΟΝΟ για Bitcoin/BTC από συγκεκριμένους χρήστες
QUERY = '(from:aeyakovenko OR from:rajgokal OR from:SBF_FTX OR from:KyleSamani OR from:cburniske OR from:TusharJain_ OR from:santiagoroel OR from:lawmaster OR from:twobitidiot OR from:Melt_Dem) (Solana OR Sol OR Etherium OR ETH) lang:en until:2025-02-01 since:2020-01-01'
MINIMUM_TWEETS = 1000  # Μπορείς να αυξήσεις το όριο αν θέλεις περισσότερα tweets

# ✅ Φόρτωση διαπιστευτηρίων
config = ConfigParser()
config.read('config.ini')
username = config['X']['username']
email = config['X']['email']
password = config['X']['password']

# ✅ Προσθήκη Headers για αποφυγή ανίχνευσης
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# ✅ Σύνδεση στο Twitter/X
client = Client(language='en-US', headers=headers)

async def authenticate():
    global client

    if os.path.exists('cookies.json'):
        print("✅ Loading saved cookies...")
        client.load_cookies('cookies.json')
    else:
        print("⚠ Cookies file not found. Logging in manually...")
        await client.login(auth_info_1=username, auth_info_2=email, password=password)
        client.save_cookies('cookies.json')
        print("✅ Cookies saved successfully!")

async def get_tweets(tweets):
    wait_time = random.randint(5, 20)  # Καθυστέρηση για αποφυγή blocking
    await asyncio.sleep(wait_time)

    if tweets is None:
        tweets = await client.search_tweet(QUERY, product='Latest')
    else:
        tweets = await tweets.next()

    return tweets

async def scrape_tweets():
    tweet_count = 0
    tweets = None

    # ✅ Δημιουργία αρχείου CSV αν δεν υπάρχει
    with open('tweets.csv', 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['Tweet_count', 'Username', 'Text', 'Created At', 'Retweets', 'Likes'])

    while tweet_count < MINIMUM_TWEETS:
        try:
            tweets = await get_tweets(tweets)
        except TooManyRequests as e:
            rate_limit_reset = datetime.fromtimestamp(e.rate_limit_reset)
            print(f'{datetime.now()} - Rate limit reached. Waiting until {rate_limit_reset}')
            wait_time = (rate_limit_reset - datetime.now()).total_seconds()
            time.sleep(wait_time)
            continue

        if not tweets:
            print(f'{datetime.now()} - No more tweets found')
            break

        for tweet in tweets:
                tweet_count += 1
                tweet_data = [tweet_count, tweet.user.name, tweet.text, tweet.created_at, tweet.retweet_count, tweet.favorite_count]

                with open('tweets.csv', 'a', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file)
                    writer.writerow(tweet_data)

                print(f'{datetime.now()} - Collected tweet {tweet_count}: {tweet.text}')

    print(f'{datetime.now()} - Done! Total tweets collected: {tweet_count}')

async def main():
    await authenticate()
    await scrape_tweets()

# ✅ Εκτέλεση του κώδικα
loop = asyncio.get_event_loop()
loop.run_until_complete(main())
