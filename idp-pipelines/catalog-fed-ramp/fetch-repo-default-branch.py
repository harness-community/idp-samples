import sys
import argparse
import datetime
import requests
import os

# The following script will request the default branch of a repo
def main():

    parser = argparse.ArgumentParser(description="Determine default branch")

    parser.add_argument(
        "--ghpattoken", type=str
    )

    parser.add_argument(
        "--ghrepo", type=str, help="acme/test-service"
    )    

    args = parser.parse_args()
    gh_pat_token = args.ghpattoken
    gh_repo = args.ghrepo
    
    # Construct the API URL
    url = f'https://api.github.com/repos/{gh_repo}'

    print(f'uRL {url}')

    headers = {'Authorization': f'token {gh_pat_token}'}

    # Send a GET request to the GitHub API with headers for authentication
    response = requests.get(url, headers=headers)

    # Check if the response is successful (status code 200)
    if response.status_code == 200:
        # Parse the response JSON to get the default branch
        repo_data = response.json()
        default_branch = repo_data.get('default_branch')
        print(f"The default branch of {gh_repo} is: {default_branch}")
        os.environ["SERVICE_DEFAULT_BRANCH"] = default_branch
        with open("default_branch.txt", "w") as file:
            file.write(default_branch)        
        sys.exit(0)
    else:
        print(f"Error: Unable to fetch data for {gh_repo}. Status Code: {response.status_code}")
        sys.exit(1)

if __name__ == "__main__":
    main()
