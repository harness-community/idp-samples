import requests
import re
from requests.auth import HTTPBasicAuth
from requests.packages.urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

username = "" # Your Bitbucket username
workspace = "" # Your Bitbucket workspace
app_password = "" # Your Bitbucket app_password
repository = "" # Your Bitbucket repo
branch = "" # Your Bitbucket branch
service_path = r"mock_rserver_root/configs/services/(idp-.*?)"
suffix_path = ".ownership/catalog-info.yaml"
account = "" 
# Replace with your x-api-key. Refer https://developer.harness.io/docs/platform/automation/api/api-quickstart/#create-a-harness-api-key-and-token to generate one
x_api_key = ""

api_url = f"https://idp.harness.io/{account}/idp/api/catalog/locations"

match = re.match(r"(.*/)", service_path)
if match:
    prefix_path = match.group(1)

def extract_directories(response):
    if "values" in response:
        for value in response["values"]:
            if "path" in value:
                path = value["path"]
                match = re.search(service_path, path)
                if match:
                    directories.append(match.group(1))
    return directories

directories = []
dir_url = f"https://api.bitbucket.org/2.0/repositories/{workspace}/{repository}/src/{branch}/{prefix_path}"
response = requests.get(dir_url, auth=HTTPBasicAuth(username, app_password))
if response.status_code != 200:
    print(f"Failed to fetch the latest commit. Status code: {response.status_code}")
    exit()

if response.status_code == 200:
    directories.extend(extract_directories(response.json()))

    # Loop until there are no more "next" links
    while "next" in response.json():
        next_url = response.json()["next"]
        response = requests.get(next_url, auth=HTTPBasicAuth(username, app_password))
        if response.status_code == 200:
            directories.extend(extract_directories(response.json()))
        else:
            print("Failed to fetch next page of directories")
            break

count = 0
unique_directories = set(directories)

for directory in unique_directories:
    api_payload = {
            "target": f"https://bitbucket.org/{workspace}/{repository}/src/{branch}/{prefix_path}{directory}/{suffix_path}",
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
            print(f"Location registered for file: {directory}")
            count += 1
        elif api_response.status_code == 409:
            print(f"Location already exists for file: {directory}. Refreshing it")
            count += 1
        else:
            print(f"Failed to register location for file: {directory}. Status code: {api_response.status_code}")
    except requests.exceptions.RequestException as e:
                    print(f"Failed to make API call for file: {directory}. Error: {str(e)}")

print(f"Registered/Refreshed {count} locations")
