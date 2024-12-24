import requests
import re
import json
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

branch = "main"
repository = "nextgen-cd-tests"
organization = "dropbox-internal"
catalog_path = r"mock_rserver_root/configs/services/.*?/.ownership/catalog-info.yaml"
api_url = "https://idp.harness.io/ZPfaaLCGQ6iAdvfJI5eFBw/idp/api/catalog/locations"
account = "ZPfaaLCGQ6iAdvfJI5eFBw"

# Replace with your GitHub token
github_token = ""

# Replace with your x-api-key. Refer https://developer.harness.io/docs/platform/automation/api/api-quickstart/#create-a-harness-api-key-and-token to generate one
x_api_key = ""

count = 0

def find_and_register_catalog_yamls(tree_sha):
    global count

    url = f"https://api.github.com/repos/{organization}/{repository}/git/trees/{tree_sha}?recursive=1"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"Bearer {github_token}",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()

        for item in data['tree']:
            if item['type'] == 'blob' and re.match(catalog_path, item['path']):
                api_payload = {
                    "target": f"https://github.com/{organization}/{repository}/blob/{branch}/{item['path']}",
                    "type": "url"
                }
                api_headers = {
                    # "Authorization": f"Bearer {bearer_token}",
                    "x-api-key": f"{x_api_key}",
                    "Content-Type": "application/json",
                    "Harness-Account": f"{account}"
                }

                retries = Retry(total=3, backoff_factor=1, status_forcelist=[401, 500, 502, 503, 504])
                session = requests.Session()
                session.mount("http://", HTTPAdapter(max_retries=retries))
                session.mount("https://", HTTPAdapter(max_retries=retries))

                try:
                    api_response = session.post(api_url, json=api_payload, headers=api_headers)
                    if api_response.status_code == 200 or api_response.status_code == 201:
                        print(f"Location registered for file: {item['path']}")
                        count += 1
                    elif api_response.status_code == 409:
                        print(f"Location already exists for file: {item['path']}. Refreshing it")
                        count += 1
                    else:
                        print(f"Failed to register location for file: {item['path']}. Status code: {api_response.status_code}")
                except requests.exceptions.RequestException as e:
                    print(f"Failed to make API call for file: {item['path']}. Error: {str(e)}")
    else:
        print(f"Failed to fetch contents. Status code: {response.status_code}")

    print(f"Registered/Refreshed {count} locations")

# Get the latest commit SHA
commit_url = f"https://api.github.com/repos/{organization}/{repository}/commits/{branch}"
headers = {
    "Accept": "application/vnd.github.v3+json",
    "Authorization": f"Bearer {github_token}",
    "X-GitHub-Api-Version": "2022-11-28"
}
response = requests.get(commit_url, headers=headers)

if response.status_code == 200:
    commit_data = response.json()
    tree_sha = commit_data['commit']['tree']['sha']
    find_and_register_catalog_yamls(tree_sha)
else:
    print(f"Failed to fetch the latest commit. Status code: {response.status_code}")
