import argparse
import requests
import os
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
    - auto
  name: <repo_name>
  annotations:
    backstage.io/source-location: url:<repo_path>
spec:
  type: service
  domian: <workspace_name>
  system: <project>
  service: <repo_name>
  lifecycle: experimental
  owner: Harness_Account_All_Users
"""

prefix_path = "services"
page_size = 50
def list_repositories(workspace, project_key, username, app_password, repo_pattern=None):
        
    page = 1
    names = []
    if(project_key == None):
        url = f"https://api.bitbucket.org/2.0/repositories/{workspace}?"
    else:
        url = f"https://api.bitbucket.org/2.0/repositories/{workspace}?q=project.key%3D%22{project_key}%22&"

    while True:

        paginated_url = f'{url}page={page}&pagelen={page_size}'
        response = requests.get(paginated_url, auth=HTTPBasicAuth(username, app_password))
        if response.status_code == 200:
            repositories = response.json()['values']

            for entry in repositories:
                if entry['name'] != current_directory:
                    names.append(entry['name'])
            if 'next' in response.json():
                page += 1
            else:
                break
        else:
            print(f"Error: {response.json()}")
            return None

    for name in names:
        name = name.lower()
        directory = f"services/{name}"
        directory_path = os.path.join(prefix_path, name)
        file_path = os.path.join(f"{directory_path}/", "catalog-info.yaml")

        os.makedirs(directory_path, exist_ok=True)

        updated_yaml_content = yaml_content_template.replace("<repo_name>", name)
        updated_yaml_content = updated_yaml_content.replace("<repo_path>", f"https://bitbucket.org/{workspace}/{current_directory}/src/{branch}/{directory}/catalog-info.yaml")
        updated_yaml_content = updated_yaml_content.replace("<workspace_name>", workspace)
        if project_key is not None:
            updated_yaml_content = updated_yaml_content.replace("<project>", project_key.lower())

        with open(file_path, "w") as file:
            file.write(updated_yaml_content)

def register_yamls(workspace, account, x_api_key):
    
    print("Registering YAML files...")
    count = 0
    api_url = f"https://idp.harness.io/{account}/idp/api/catalog/locations"

    repos = [name for name in os.listdir("./services") if os.path.isdir(os.path.join("./services", name))]

    for repo_name in repos:
        if repo_name != current_directory:
            directory = f"services/{repo_name}"
            print(f"https://bitbucket.org/{workspace}/{current_directory}/src/{branch}/{directory}/catalog-info.yaml")
            api_payload = {
                "target": f"https://bitbucket.org/{workspace}/{current_directory}/src/{branch}/{directory}/catalog-info.yaml",
                "type": "url"
            }
            api_headers = {
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
    subprocess.run(["git", "add", f"{prefix_path}/"])
    commit_message = "Adding YAMLs"
    subprocess.run(["git", "commit", "-m", commit_message])
    subprocess.run(["git", "push"])

def parse_arguments():
    parser = argparse.ArgumentParser(description="List repositories in a Bitbucket organization and manage catalog-info.yaml files")
    parser.add_argument("--workspace", help="Bitbucket workspace name")
    parser.add_argument("--username", help="Bitbucket username")
    parser.add_argument("--password", help="Bitbucket app password token")
    parser.add_argument("--project_key", help="Bitbucket project-key")
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
        if args.workspace == None or args.password == None or args.username == None:
            print(args.workspace + " " + args.password + " " + args.username)
            print("Provide Bitbucket (workspace name) or (workspace and project-key), Bitbucket username using --username and Bitbucket app_password using --password flags.")
            exit()
        list_repositories(args.workspace, args.project_key, args.username, args.password)
    elif args.register_yamls:
        if args.workspace == None or args.x_api_key == None or args.account == None:
            print("Provide Bitbucket workspace name, Harness account ID and Harness x_api_key to create the YAMLs")
            exit()
        register_yamls(args.workspace, args.account, args.x_api_key)
    elif args.run_all:
        if args.x_api_key == None or args.account == None or args.workspace == None or args.password == None or args.username == None:
            print("Provide either Bitbucket (workspace name) or (workspace and project-key), Bitbucket username, Bitbucket app-password, Harness account ID and Harness x_api_key to create the YAMLs")
            exit()
        list_repositories(args.workspace, args.project_key, args.username, args.password)
        push_yamls()
        register_yamls(args.workspace, args.account, args.x_api_key)

if __name__ == "__main__":
    main()