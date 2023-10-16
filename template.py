import argparse
import os
import time
import json
import random
from datetime import datetime
import requests
from dotenv import load_dotenv
import praw
import wandb
import pandas as pd

# Load environment variables
load_dotenv()

# Twitter scraping configurations
bearer_token = os.getenv("BEARER_TOKEN")

# Reddit scraping configurations
reddit = praw.Reddit(
    client_id=os.getenv("CLIENT_ID"),
    client_secret=os.getenv("CLIENT_SECRET"),
    password=os.getenv("REDDIT_PASSWORD"),
    user_agent=os.getenv("USER_AGENT"),
    username=os.getenv("REDDIT_USERNAME")
)

def scrapTwitter(max_limit=100, key="tao"):
    url = f"https://api.twitter.com/2/tweets/search/recent?query={key}&tweet.fields=created_at&max_results={max_limit}"
    headers = {'Authorization': f'Bearer {bearer_token}'}
    try:
        response = requests.get(url, headers=headers)
        returnData = response.json()['data']
        if len(returnData) == 0:
            print("No tweets found.")
            return
        for twitterPost in returnData:
            store_data_wandb(twitterPost)  
    except Exception as e:
        print('Invalid Key or other error:', e)

def random_line(afile="keywords.txt"):
    if not os.path.exists(afile):
        print(f"Keyword file not found at location: {afile}")
        quit()
    lines = open(afile).read().splitlines()
    return random.choice(lines)

def scrape_reddit(subreddit_name='all', limit=100):
    try:
        subreddit = reddit.subreddit(subreddit_name)
        for submission in subreddit.new(limit=limit):
            store_data_wandb(submission) 
        print("Remaining Requests:", reddit.auth.limits['remaining'])
        print("Rate Limit Resets At:", reddit.auth.limits['reset_timestamp'])
    except Exception as e:
        print(f"Error occurred: {e}")

def get_config():
    parser = argparse.ArgumentParser(description="Parse command-line arguments.")
    parser.add_argument('--wandb.username', default='username_here', help='Wandb username')
    parser.add_argument('--wandb.project', default='data_scraping', help='Wandb project name')
    parser.add_argument('--model_server_url', default='http://localhost:5000/query', help='URL of the Flask server hosting the model')
    config = parser.parse_args()

    config.full_path = os.path.expanduser(f"{config.wandb.username}/{config.wandb.project}")
    os.makedirs(config.full_path, exist_ok=True)
    return config

def score_response(response, source, username='username_here', project='data_scraping', run_id='hvs7wdk8'):
    total_time_diff = 0
    exist_count = 0
    wrong_count = 0
    total_length = len(response)

    # Fetch historical data
    history = storeWB.returnData(username=username, project=project, id=run_id)

    # Choose 50 random posts from the response for sampling
    sampled_response = random.sample(response, min(50, total_length))

    for post in sampled_response:
        try:
            # Calculate total time difference from current time
            given_time = datetime.fromisoformat(post['created_at'])
            current_time = datetime.now()
            total_time_diff += (current_time - given_time).total_seconds()

            # Check for uniqueness of the post based on its ID
            if not history.empty:
                filtered_data = history[history['id'] == post['id']]
                if not filtered_data.empty:
                    exist_count += 1
                    if filtered_data.iloc[0]['created_at'] != post['created_at']:
                        wrong_count += 1
        except:
            continue

    avg_time_diff = total_time_diff / len(sampled_response)
    timeScore = min(avg_time_diff / 864000, 1)
    unique_score = exist_count / len(sampled_response)
    wrong_score = wrong_count / len(sampled_response)

    final_score = max(1 - 0.1 * timeScore - 0.3 * unique_score - 0.2 * wrong_score - min(0.2, 20 / total_length), 0)
    return final_score

def store_data_wandb(all_data, data_type, config, wandb_params):
    function_map = {
        "reddit": storeWB.store_reddit,
        "twitter": storeWB.store_twitter
    }
    function_map[data_type](all_data=all_data, username=config.wandb.username, projectName=config.wandb.project, run_id=wandb_params[data_type])

def query_single_model(query_type, server_url):
    response_data = None
    try:
        response = requests.post(server_url, json={"type": query_type})
        if response.status_code == 200:
            response_data = response.json()["data"]
    except Exception as e:
        print(f"Failed to query model server due to: {e}")

    return response_data

def store_reddit(all_data, username, projectName, run_id):
    """
    This function stores all responses from all miners to wandb.

    Args:
        all_data (list): The list of all data.
        projectName (str): The name of the project.
        run_id (str): The id of the run.
    """

    # Initialize wandb run
    run = wandb.init(project=projectName,  resume="allow",  id=run_id)
    
    # Collect registered post ids
    historyData = returnData(username=username, project=projectName, id=run_id)
    
    # Iterate over all data
    for data in all_data:
        if data is not None:
            for item in data:
                # Check if miner's response already exists in storage
                if historyData.empty or historyData is None:
                    wandb.log({
                        "id": item['id'],
                        "title": item['title'],
                        "text": item['text'],
                        "url": item['url'],
                        "created_at": item['created_at'],
                        "type": item['type']
                    })
                else:
                    filtered_data = historyData[historyData['id'] == item['id']]
                    # Log the data to wandb
                    if filtered_data.empty or filtered_data is None:
                        wandb.log({
                            "id": item['id'],
                            "title": item['title'],
                            "text": item['text'],
                            "url": item['url'],
                            "created_at": item['created_at'],
                            "type": item['type']
                        })
    # Finish the run
    run.finish()

def store_twitter(all_data, username, projectName, run_id):
    """
    This function stores all responses from all miners to wandb for Twitter data.

    Args:
        all_data (list): The list of all data.
        projectName (str): The name of the project.
        run_id (str): The id of the run.
    """

    # Initialize wandb run
    run = wandb.init(project=projectName, resume="allow", id=run_id)
    
    # Collect registered post ids
    historyData = returnData(username=username, project=projectName, id=run_id)

    # Iterate over all data
    for data in all_data:
        if data is not None:
            for item in data:
                # Check if miner's response already exists in storage
                if historyData.empty or historyData is None:
                    wandb.log({
                        "id": item['id'],
                        "text": item['text'],
                        "url": item['url'],
                        "created_at": item['created_at'],
                        "type": item['type']
                    })
                else:
                    filtered_data = historyData[historyData['id'] == item['id']]
                    if filtered_data.empty or filtered_data is None:
                        wandb.log({
                            "id": item['id'],
                            "text": item['text'],
                            "url": item['url'],
                            "created_at": item['created_at'],
                            "type": item['type']
                        })
    # Finish the run
    run.finish()

def returnData(username, project, id):
    """
    This function returns all data in storage for Twitter data.

    Args:
        project (str): The name of the project.
        id (str): The id of the run.

    Returns:
        DataFrame: The DataFrame of the history data.
    """
    api = wandb.Api()
    run = api.run(f"{username}/{project}/{id}")
    historyData = run.history()
    return historyData

def main(config):
    alpha = 0.9
    score = 0
    wandb_params = {}

    if os.path.exists('wandb_config.json'):
        with open('wandb_config.json', 'r') as f:
            wandb_params = json.load(f)
    else:
        with open('wandb_config.json', 'w') as f:
            wandb_params = {
                'username': config.wandb.username,
                'project': config.wandb.project,
                'twitter': wandb.init(project=config.wandb.project, resume="allow", name="twitter").id,
                'reddit': wandb.init(project=config.wandb.project, resume="allow", name="reddit").id
            }
            json.dump(wandb_params, f)

    while True:
        query_type = "twitter" if random.randint(0, 1) == 0 else "reddit"
        response = query_single_model(query_type, config.model_server_url)

        if response:
            new_score = score_function(response, query_type, config.wandb.username, config.wandb.project, wandb_params[query_type])
            score = alpha * score + (1 - alpha) * new_score

            store_data_wandb([response], query_type, config, wandb_params)

        time.sleep(10)

if __name__ == "__main__":
    config = get_config()
    main(config)