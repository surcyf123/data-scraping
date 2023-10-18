
# %%
ids_seen = []
# %%
"""_summary_
Todo:
1. Multiprocessing? How to handle continue token if it cant be done in parallel
2. Duplicate checker from id
3.
"""
from typing import Dict, List, Tuple
import requests
import time
from datetime import datetime

# permitted: 'top', 'latest', 'people', 'photos', 'videos'"
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

"""



New Function with Continuation Token: 
1. X number of tweets requested
2. Chunk it into pieces of 20 requests
3. Use response.json()['continuation_token] to get the continuation
4. return full list

posts : List[Dict] = resp['results']
continuation_token : str = resp['continuation_token']

"""
def get_number_of_posts(hashtag: str, amount: int) -> List[Dict]:
    all_posts = []  # This will store all the posts collected
    continuation_token = None  # Initialize continuation token to None for the first call

    # Continue to fetch posts until the desired number is reached
    while amount > 0:
        # Decide on the number of posts to fetch in this iteration
        fetch_count = min(amount, 20)  # Either the remaining amount or 20, whichever is lesser

        # Fetch the posts
        resp = get_posts(hashtag, fetch_count, continuation_token)
        posts: List[Dict] = resp['results']
        continuation_token: str = resp['continuation_token']

        # Append the fetched posts to the all_posts list
        all_posts.extend(posts)

        # Reduce the number of posts still needed
        amount -= fetch_count

    return all_posts




def get_single_response_no_dup(hashtag: str) -> Dict[str,str]:
    found = False
    continuation_token = None
    while not found:
        resp = get_posts(hashtag=hashtag, amount=20,continuation_token=continuation_token)
        resp_list = resp['results']
        for post in resp_list:
            if post['tweet_id'] in ids_seen:
                continue
            else:
                ids_seen.append(post['tweet_id'])
                dt_object = datetime.utcfromtimestamp(post['timestamp'])
                formatted_str = dt_object.strftime('%Y-%m-%dT%H:%M:%S.000Z')


                return {'text': post['text'], 'id': post['tweet_id'], 'created_at': formatted_str}
        continuation_token = resp['continuation_token']


def get_multiple_tweets_no_dup(hashtag: str, amount:int) -> List[Dict[str,str]]:
    amount_left = amount
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


 
# %%