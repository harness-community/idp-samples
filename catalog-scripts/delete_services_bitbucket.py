import requests
import re
from requests.auth import HTTPBasicAuth

username = "" # Your Bitbucket username
workspace = "" # Your Bitbucket workspace
app_password = "" # Your Bitbucket app_password
repository = "" # Your Bitbucket repo
branch =  "" # Your Bitbucket branch
service_path = r"mock_rserver_root/configs/services/(.*?-service)"
suffix_path = ".ownership/catalog-info.yaml"
url = f"https://api.bitbucket.org/2.0/repositories/{workspace}/{repository}/src"

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

	payload = {'files': f'/{prefix_path}/{directory}/{suffix_path}'}
	files=[]

	response = requests.post(url,data=payload, files=files, auth=HTTPBasicAuth(username, app_password))
	if response.status_code == 201:
		count += 1

print(f"{count} files deleted successfully")
