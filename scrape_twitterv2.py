
ids_seen = []

from typing import Dict, List, Tuple
import requests
import time
from datetime import datetime
def get_posts(hashtag:str, amount: int = 20,continuation_token=None) -> Tuple[List[Dict],str]:
    assert(amount<=20)
    t1 = time.time()
    headers = {
        "X-RapidAPI-Key": "413cd806a8mshc85ff346389169fp16f257jsn54036afc0f4e",
        "X-RapidAPI-Host": "twitter154.p.rapidapi.com"
    }


    if continuation_token:
        url = "https://twitter154.p.rapidapi.com/hashtag/hashtag/continuation"
        querystring = {"hashtag":f"#{hashtag}","continuation_token":continuation_token,"limit":amount,"section":"latest"}

    else:
        url = "https://twitter154.p.rapidapi.com/hashtag/hashtag"
        querystring = {"hashtag":f"#{hashtag}","limit":amount,"section":"latest"}

    response = requests.get(url, headers=headers, params=querystring)
    t2 = time.time() - t1
    print(f"Time taken: {t2}")
    return response.json()

def read_ids_seen_from_file(filename='ids_seen.txt'):
    try:
        with open(filename, 'r') as f:
            return f.read().splitlines()
    except FileNotFoundError:
        return []

def write_id_to_file(tweet_id, filename='ids_seen.txt'):
    with open(filename, 'a') as f:
        f.write(tweet_id + '\n')

def get_multiple_tweets(hashtag: str, desired_count: int = 20) -> List[Dict[str, str]]:
    # We can do any amount of tweet now

    # Initialize ids_seen from file
    ids_seen = read_ids_seen_from_file()  
    amount_left = desired_count
    continuation_token = None
    tweet_responses = []
    while amount_left >= 1:
        resp = get_posts(hashtag=hashtag, amount=20,continuation_token=continuation_token)
        resp_list = resp['results']
        for post in resp_list:
            if post['tweet_id'] in ids_seen:
                continue
            else:
                ids_seen.append(post['tweet_id'])
                dt_object = datetime.utcfromtimestamp(post['timestamp'])
                formatted_str = dt_object.strftime('%Y-%m-%dT%H:%M:%S.000Z')
                payload = {'text': post['text'], 'id': post['tweet_id'], 'created_at': formatted_str, 'url' : f'https://twitter.com/{post["user"]["username"]}/status/{post["tweet_id"]}'}
                tweet_responses.append(payload)
                amount_left -= 1
                if amount_left == 0:
                    return tweet_responses
        continuation_token = resp['continuation_token']
    return tweet_responses

def twitterScrap():
    # fetched_data = twitter_db.fetch_latest_posts(500)
    # print("calling twitterscrap")
    fetched_data = get_multiple_tweets("china")
    print(f"fetched_data is: {fetched_data}")
    return fetched_data

def main():
    twitterScrap()

if __name__ == "__main__":
    main()
