import argparse
import requests
import os
# import yaml
import re
from requests.auth import HTTPBasicAuth
import argparse
from requests.packages.urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
import subprocess

current_directory = os.path.basename(os.getcwd())
branch  = "main"

yaml_content_template = """
apiVersion: backstage.io/v1alpha1
kind: Component
metadata:
  name: {dirName}
  tags:
    - auto-generated
  annotations:
    backstage.io/source-location: url:{dirLocation}
spec:
  type: service
  lifecycle: experimental
  owner: Harness_Account_All_Users
  system: {orgName}
"""

def get_directories(organization, repo_name, token, path):
    base_url = f"https://api.github.com/repos/{organization}/{repo_name}/contents/{path}"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28"
    }

    directories = []
    url = base_url

    while url:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"Error: Unable to fetch contents of repo '{repo_name}' at path '{path}'.")
            return []

        contents = response.json()
        directories.extend(item['name'] for item in contents if item['type'] == 'dir' and item['name'] != 'idp')
        
        if 'Link' in response.headers:
            links = response.headers['Link']
            next_link = None
            for link in links.split(','):
                if 'rel="next"' in link:
                    next_link = link[link.find('<') + 1:link.find('>')]
                    break
            url = next_link
        else:
            url = None

    return directories

def list_directories(organization, token, path, repo_name, dir_pattern=None):
    yaml_files_created = 0
    print(f"Directories in {organization}:")

    directories = get_directories(organization, repo_name, token, path)

    for directory in directories:
        directory_name = directory.lower()
        if directory_name == current_directory:
            continue
        create_or_update_catalog_info(organization, directory_name, path)
        print(directory + '\n')
        yaml_files_created += 1
    
    print("----------")
    print(f"Total YAML files created or updated: {yaml_files_created}")

def create_or_update_catalog_info(organization, dirName, dirPath):
    directory = f"idp/{dirName}"
    if not os.path.exists(directory):
        os.makedirs(directory)
    
    yaml_file_path = f"{directory}/catalog-info.yaml"

    if dirPath != "" :
        dirLocation = f"https://github.com/{organization}/{current_directory}/tree/{branch}/{dirName}"
    else:
        dirLocation = f"https://github.com/{organization}/{current_directory}/tree/{branch}/{dirPath}{dirName}"

    if os.path.exists(yaml_file_path):
        
        with open(yaml_file_path, "r") as file:
            existing_content = file.read()
        
        updated_content = yaml_content_template.format(dirName=dirName, dirLocation=dirLocation, orgName=organization)
        with open(yaml_file_path, "w") as file:
            file.write(updated_content)
    else:
        
        with open(yaml_file_path, "w") as file:
            file.write(yaml_content_template.format(dirName=dirName, dirLocation=dirLocation, orgName=organization))

def register_yamls(organization, account, x_api_key):
    
    print("Registering YAML files...")
    count = 0
    api_url = f"https://idp.harness.io/{account}/idp/api/catalog/locations"

    files = [name for name in os.listdir("./idp") if os.path.isfile(os.path.join("./idp", name))]
    
    for file_name in files:
        if file_name != current_directory:
            file_name = f"services/{file_name}"
            api_payload = {
                "target": f"https://github.com/{organization}/{current_directory}/blob/{branch}/{file_name}",
                "type": "url"
            }
            api_headers = {
                # "Authorization": f"Bearer {bearer_token}",
                "x-api-key": f"{x_api_key}",
                "Content-Type": "application/json",
                "Harness-Account": f"{account}"
            }
            print(f"https://github.com/{organization}/{current_directory}/blob/{branch}/{file_name}")
            retries = Retry(total=3, backoff_factor=1, status_forcelist=[401, 500, 502, 503, 504])
            session = requests.Session()
            session.mount("http://", HTTPAdapter(max_retries=retries))
            session.mount("https://", HTTPAdapter(max_retries=retries))

            try:
                api_response = session.post(api_url, json=api_payload, headers=api_headers)
                if api_response.status_code == 200 or api_response.status_code == 201:
                    print(f"Location registered for file: {file_name}")
                    count += 1
                elif api_response.status_code == 409:
                    refresh_payload = {
                        "entityRef":f"component:default/{file_name}"
                    }
                    refresh_url = f"https://idp.harness.io/{account}/idp/api/catalog/refresh"
                    api_response = session.post(refresh_url, json=refresh_payload, headers=api_headers)
                    print(f"Location already exists for file: {file_name}. Refreshing it")
                    count += 1
                else:
                    print(f"Failed to register location for file: {file_name}. Status code: {api_response.content}")
            except requests.exceptions.RequestException as e:
                print(f"Failed to make API call for file: {file_name}. Error: {str(e)}")

def push_yamls():
    print("Pushing YAMLs...")
    subprocess.run(["git", "add", "idp/"])
    commit_message = "Adding YAMLs"
    subprocess.run(["git", "commit", "-m", commit_message])
    subprocess.run(["git", "push", "-f"])

def parse_arguments():
    parser = argparse.ArgumentParser(description="List repositories in a GitHub organization and manage catalog-info.yaml files")
    parser.add_argument("--org", help="GitHub organization name")
    parser.add_argument("--token", help="GitHub personal access token")
    parser.add_argument("--path", help="Directries path")
    parser.add_argument("--repo_name", help="GitHub repo name")
    parser.add_argument("--repo-pattern", help="Optional regex pattern to filter repositories")
    parser.add_argument("--create-yamls", action="store_true", help="Create or update catalog-info.yaml files")
    parser.add_argument("--register-yamls", action="store_true", help="Register existing catalog-info.yaml files")
    parser.add_argument("--run-all", action="store_true", help="Run all operations: create, register, and run")
    parser.add_argument("--x_api_key", help="Harness x-api-key")
    parser.add_argument("--account", help="Harness account")
    parser.add_argument("--branch", help="Your git branch")
    return parser.parse_args()

def main():
    args = parse_arguments()
    global branch
    if not (args.create_yamls or args.register_yamls or args.run_all):
        print("Error: One of --create-yamls, --register-yamls or --run_all must be used.")
        return
    if args.branch is not None:
        branch = args.branch
    if args.create_yamls:
        if args.org == None or args.token == None or args.repo_name == None or args.path == None:
            print("Provide GitHub org name using --org, GitHub token using --token, Directories path using --path and GitHub repo_name using --repo_name flags.")
            exit()
        list_directories(args.org, args.token, args.path, args.repo_name)
    elif args.register_yamls:
        if args.org == None or args.x_api_key == None or args.account == None:
            print("Provide GitHub org name using --org, Harness account ID using --account and Harness x_api_key using --x_api_key to register the YAMLs")
            exit()
        register_yamls(args.org, args.account, args.x_api_key)
    elif args.run_all:
        if args.x_api_key == None or args.account == None or args.org == None or args.token == None:
            print("Provide GitHub org name using --org, GitHub Token using --token, Harness account ID using --account, Harness x_api_key using --x_api_key, Directories path using --path and GitHub repo_name using --repo_name flags to create and register the YAMLs")
            exit()
        list_directories(args.org, args.token, args.path, args.repo_name)
        push_yamls()
        register_yamls(args.org, args.account, args.x_api_key)

if __name__ == "__main__":
    main()