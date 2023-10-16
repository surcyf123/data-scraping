import argparse
import os
import time
import json
import wandb
from datetime import datetime
import storeWB
import requests

def get_config():
    parser = argparse.ArgumentParser(description="Parse command-line arguments.")
    parser.add_argument('--wandb.username', default='aureliojafer', help='Wandb username')
    parser.add_argument('--wandb.project', default='scraping_subnet-neurons', help='Wandb project name')
    parser.add_argument('--model_server_url', default='http://localhost:5000/query', help='URL of the Flask server hosting the model')
    config = parser.parse_args()

    config.full_path = os.path.expanduser(f"{config.wandb.username}/{config.wandb.project}")
    os.makedirs(config.full_path, exist_ok=True)
    return config

def score_function(response, data_type, username, project, run_id):
    if data_type == "reddit":
        return redditScore(response, username, project, run_id)
    else:
        return twitterScore(response, username, project, run_id)

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
