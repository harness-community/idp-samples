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
  tags:
    - auto-generated
  name: {repo_name}
  annotations:
    backstage.io/source-location: url:{repo_path}
spec:
  type: service
  system: {orgName}
  lifecycle: experimental
  owner: Harness_Account_All_Users
"""

def get_repositories_api(organization, token, current_directory=None, repo_pattern=None, per_page=100):
    url = f"https://api.github.com/orgs/{organization}/repos"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    
    all_repos_info = []
    page = 1
    while True:
        params = {"page": page, "per_page": per_page}
        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            print(f"Error: Unable to fetch repositories from page {page}.")
            break
        repos = response.json()
        if not repos:
            break
        # print(f"Fetching repositories from page {page}...")
        for repo in repos:
            repo_name = repo['name'].lower()
            if repo_name == current_directory:
                continue
            repo_path = repo['html_url']
            if repo_pattern is None or re.match(repo_pattern, repo_name):
                all_repos_info.append({"name": repo_name, "html_url": repo_path})
        page += 1
    
    return all_repos_info

def list_repositories(organization, token, repo_pattern=None):

    yaml_files_created = 0

    print(f"Repositories in {organization}:")

    repos = get_repositories_api(organization, token)
    for repo in repos:
        repo_name = repo['name'].lower()
        if repo_name == current_directory:
            continue
        repo_path = repo['html_url']
        if repo_pattern is None or re.match(repo_pattern, repo_name):
            print(repo_name)
            create_or_update_catalog_info(organization, repo_name, repo_path)
            yaml_files_created += 1
    print("----------")
    print(f"Total YAML files created or updated: {yaml_files_created}")

def create_or_update_catalog_info(organization, repo_name, repo_path):
    directory = f"services/{repo_name}"
    if not os.path.exists(directory):
        os.makedirs(directory)
    
    yaml_file_path = f"{directory}/catalog-info.yaml"

    if os.path.exists(yaml_file_path):
        # Update existing YAML file
        with open(yaml_file_path, "r") as file:
            existing_content = file.read()
        updated_content = yaml_content_template.format(repo_name=repo_name, repo_path=repo_path)
        updated_content = yaml_content_template.replace("{orgName}", organization)
        with open(yaml_file_path, "w") as file:
            file.write(updated_content)
    else:
        # Create new YAML file
        with open(yaml_file_path, "w") as file:
            file.write(yaml_content_template.format(repo_name=repo_name, repo_path=repo_path))

def register_yamls(organization, account, x_api_key):
    # Placeholder function for registering YAML files
    print("Registering YAML files...")
    count = 0
    api_url = f"https://idp.harness.io/{account}/idp/api/catalog/locations"

    repos = [name for name in os.listdir("./services") if os.path.isdir(os.path.join("./services", name))]
    for repo_name in repos:
        if repo_name != current_directory:
            directory = f"services/{repo_name}"
            api_payload = {
                "target": f"https://github.com/{organization}/{current_directory}/blob/{branch}/{directory}/catalog-info.yaml",
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
                    print(f"Location registered for file: {repo_name}")
                    count += 1
                elif api_response.status_code == 409:
                    refresh_payload = {
                        "entityRef":f"component:default/{repo_name}"
                    }
                    refresh_url = f"https://idp.harness.io/{account}/idp/api/catalog/refresh"
                    api_response = session.post(refresh_url, json=refresh_payload, headers=api_headers)
                    print(f"Location already exists for file: {repo_name}. Refreshing it")
                    count += 1
                else:
                    print(f"Failed to register location for file: {repo_name}. Status code: {api_response.status_code}")
            except requests.exceptions.RequestException as e:
                print(f"Failed to make API call for file: {repo_name}. Error: {str(e)}")

def push_yamls():
    print("Pushing YAMLs...")
    subprocess.run(["git", "add", "services/"])
    commit_message = "Adding YAMLs"
    subprocess.run(["git", "commit", "-m", commit_message])
    subprocess.run(["git", "push", "-f"])

def parse_arguments():
    parser = argparse.ArgumentParser(description="List repositories in a GitHub organization and manage catalog-info.yaml files")
    parser.add_argument("--org", help="GitHub organization name")
    parser.add_argument("--token", help="GitHub personal access token")
    parser.add_argument("--repo-pattern", help="Optional regex pattern to filter repositories")
    parser.add_argument("--create-yamls", action="store_true", help="Create or update catalog-info.yaml files")
    parser.add_argument("--register-yamls", action="store_true", help="Register existing catalog-info.yaml files")
    parser.add_argument("--run-all", action="store_true", help="Run all operations: create, register, and run")
    parser.add_argument("--x_api_key", help="Harness x-api-key")
    parser.add_argument("--account", help="Harness account")
    return parser.parse_args()

def main():
    args = parse_arguments()
    
    if not (args.create_yamls or args.register_yamls or args.run_all):
        print("Error: One of --create-yamls, --register-yamls or --run_all must be used.")
        return
    
    if args.create_yamls:
        if args.org == None or args.token == None:
            print("Provide GitHub org name using --org and GitHub token using --token flags.")
            exit()
        list_repositories(args.org, args.token, args.repo_pattern)
    elif args.register_yamls:
        if args.org == None or args.x_api_key == None or args.account == None:
            print("Provide GitHub org name, Harness account ID and Harness x_api_key to create the YAMLs")
            exit()
        register_yamls(args.org, args.account, args.x_api_key)
    elif args.run_all:
        if args.x_api_key == None or args.account == None or args.org == None or args.token == None:
            print("Provide GitHub org name, GitHub Token, Harness account ID and Harness x_api_key to create the YAMLs")
            exit()
        list_repositories(args.org, args.token, args.repo_pattern)
        push_yamls()
        register_yamls(args.org, args.account, args.x_api_key)

if __name__ == "__main__":
    main()