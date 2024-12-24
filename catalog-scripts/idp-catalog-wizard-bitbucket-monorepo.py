import argparse
import requests
import os
from requests.auth import HTTPBasicAuth
import argparse
from requests.packages.urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
import subprocess

current_directory = os.path.basename(os.getcwd())

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

import requests

def get_directories(workspace, repo_name, username, app_password, path, branch, repo_pattern=None):

    if(path == ""):
        base_url = f"https://api.bitbucket.org/2.0/repositories/{workspace}/{repo_name}/src/{branch}/"
    else:
        base_url = f"https://api.bitbucket.org/2.0/repositories/{workspace}/{repo_name}/src/{branch}/{path}/"
    auth = HTTPBasicAuth(username, app_password)

    directories = []
    url = base_url

    while url:
        response = requests.get(url, auth=auth)
        if response.status_code != 200:
            print(f"Error: Unable to fetch contents of repo '{repo_name}' at path '{path}'. Status code: {response.status_code}")
            return []

        contents = response.json().get('values', [])
        directories.extend(item['path'] for item in contents if item['type'] == 'commit_directory' and item['path'].split('/')[-1] != 'idp')
        
        if 'next' in response.json():
            url = response.json()['next']
        else:
            url = None

    return directories

def list_directories(workspace, username, app_password, repo_name, path, branch, dir_pattern=None):
                    
    yaml_files_created = 0
    print(f"Directories in {workspace}/{repo_name}:")

    directories = get_directories(workspace, repo_name, username, app_password, path, branch)

    for directory in directories:
        directory_name = directory.lower()
        if directory_name == current_directory:
            continue
        create_or_update_catalog_info(workspace, directory_name, path, branch)
        print(directory)
        yaml_files_created += 1
    
    print("----------")
    print(f"Total YAML files created or updated: {yaml_files_created}")

def create_or_update_catalog_info(workspace, dirName, dirPath, branch):

    last_slash_index = dirName.rfind('/')

    if last_slash_index != -1:
        file_name =  dirName[last_slash_index + 1:]
    else: 
        file_name = dirName

    directory = f"idp/{file_name}"
    if not os.path.exists(directory):
        os.makedirs(directory)
    
    yaml_file_path = f"{directory}/catalog-info.yaml"

    if dirPath != "" :
        dirLocation = f"https://bitbucket.org/{workspace}/{current_directory}/src/{branch}/{dirName}"
    else:
        dirLocation = f"https://bitbucket.org/{workspace}/{current_directory}/src/{branch}/{dirPath}{file_name}"

    if os.path.exists(yaml_file_path):
        
        with open(yaml_file_path, "r") as file:
            existing_content = file.read()
        
        updated_content = yaml_content_template.format(dirName=file_name, dirLocation=dirLocation, orgName=workspace)
        with open(yaml_file_path, "w") as file:
            file.write(updated_content)
    else:
        with open(yaml_file_path, "w") as file:
            file.write(yaml_content_template.format(dirName=file_name, dirLocation=dirLocation, orgName=workspace))

def register_yamls(workspace, account, x_api_key, branch):
    
    print("Registering YAML files...")
    count = 0
    api_url = f"https://idp.harness.io/{account}/idp/api/catalog/locations"

    files = [name for name in os.listdir('./idp')]
    print(f"The service are {files}")
    
    for file_name in files:
        if file_name != current_directory:
            target = f"https://bitbucket.org/{workspace}/{current_directory}/src/{branch}/idp/{file_name}/catalog-info.yaml"
            
            api_payload = {
                "target": target,
                "type": "url"
            }
            api_headers = {
                "x-api-key": f"{x_api_key}",
                "Content-Type": "application/json",
                "Harness-Account": f"{account}"
            }
            print(target)
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
    subprocess.run(["git", "push"])

def parse_arguments():
    parser = argparse.ArgumentParser(description="List repositories in a Bitbucket organization and manage catalog-info.yaml files")
    parser.add_argument("--workspace", help="Bitbucket workspace name")
    parser.add_argument("--username", help="Bitbucket username")
    parser.add_argument("--password", help="Bitbucket app password token")
    parser.add_argument("--project_key", help="Bitbucket project-key")
    parser.add_argument("--repo_name", help="Bitbucket repo-name")
    parser.add_argument("--path", help="Directory path")
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
    branch  = "main"
    path = ""
    if not (args.create_yamls or args.register_yamls or args.run_all):
        print("Error: One of --create-yamls, --register-yamls or --run-all must be used.")
        return
    if args.branch is not None:
        branch = args.branch
    if args.path is not None:
        path = args.path
    if not (args.create_yamls or args.register_yamls or args.run_all):
        print("Error: One of --create-yamls, --register-yamls or --run_all must be used.")
        return
    
    if args.create_yamls:
        if args.workspace == None or args.password == None or args.username == None:
            print("Provide Bitbucket (workspace name) or (workspace and project-key), Bitbucket username using --username and Bitbucket app_password using --password flags.")
            exit()
        list_directories(args.workspace, args.username, args.password, args.repo_name, path, branch)
    elif args.register_yamls:
        if args.workspace == None or args.x_api_key == None or args.account == None:
            print("Provide Bitbucket workspace name, Harness account ID and Harness x_api_key to register the YAMLs")
            exit()
        register_yamls(args.workspace, args.account, args.x_api_key, branch)
    elif args.run_all:
        if args.x_api_key == None or args.account == None or args.workspace == None or args.password == None or args.username == None:
            print("Provide either Bitbucket (workspace name) or (workspace and project-key), Bitbucket username, Bitbucket app-password, Harness account ID and Harness x_api_key to create the YAMLs")
            exit()
        list_directories(args.workspace, args.username, args.password, args.repo_name, path, branch)
        push_yamls()
        register_yamls(args.workspace, args.account, args.x_api_key, branch)

if __name__ == "__main__":
    main()