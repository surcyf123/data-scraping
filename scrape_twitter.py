
# %%
from typing import Dict, List
import requests
import time

def get_posts_by_hashtag(hashtag:str, amount: int = 20) -> List[Dict]:
    assert(amount<=20)
    t1 = time.time()
    url = "https://twitter154.p.rapidapi.com/hashtag/hashtag"

    querystring = {"hashtag":f"#{hashtag}","limit":amount,"section":"top"}

    headers = {
        "X-RapidAPI-Key": "413cd806a8mshc85ff346389169fp16f257jsn54036afc0f4e",
        "X-RapidAPI-Host": "twitter154.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring)
    t2 = time.time() - t1
    print(f"Time taken: {t2}")
    return response.json()['results']




 
# %%
