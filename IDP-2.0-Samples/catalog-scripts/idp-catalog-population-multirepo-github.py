from dotenv import load_dotenv
import requests
import json
import os
import base64
import re
import secrets

load_dotenv()

# === CONFIGURATION ===
# Your GitHub token.
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
# Your GitHub organization name
GITHUB_ORG = os.getenv("GITHUB_ORG")
# The name of the central GitHub repository where IDP entities will be stored
CENTRAL_REPO = os.getenv("CENTRAL_REPO")
# Your Harness API key. You can generate it by visiting https://app.harness.io/ng/#/account/security
HARNESS_API_KEY = os.getenv("HARNESS_API_KEY")
# Your Harness account ID. You can find it in the URL of your Harness account
HARNESS_ACCOUNT_ID = os.getenv("HARNESS_ACCOUNT_ID")
# The reference to the Harness Git connector depening on the level of scope
CONNECTOR_REF = os.getenv("CONNECTOR_REF")
# The identifier of the Harness organization where the IDP entities should be created
ORG_IDENTIFIER = os.getenv("ORG_IDENTIFIER")
# The identifier of the Harness project where the IDP entities should be created
PROJECT_IDENTIFIER = os.getenv("PROJECT_IDENTIFIER")
# === HEADERS ===
GITHUB_HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}
HARNESS_HEADERS = {
    "Content-Type": "application/json",
    "Harness-Account": HARNESS_ACCOUNT_ID,
    "x-api-key": HARNESS_API_KEY
}
# === HARNESS ENTITY CREATION FUNCTION ===

# === IDENTIFIER SANITIZATION FUNCTION ===
def generate_harness_identifier(repo_name):
    name = repo_name.lower()

    # Replace invalid characters with underscore
    name = re.sub(r"[^a-z0-9_$]", "_", name)

    # Ensure it starts with a letter or underscore
    if not re.match(r"^[a-z_]", name):
        name = f"idp_{name}"
    # Add random suffix to ensure uniqueness
    suffix = secrets.token_hex(3)  # 6 hex characters
    name = f"{name}_{suffix}"
    # Truncate to 128 characters max (as per Harness spec)
    return name[:128]
# This function creates a Harness IDP entity for a given repository
def create_harness_entity(repo_name, repo_description):
    print(f"Creating entity for: {repo_name}")
    identifier = generate_harness_identifier(repo_name)

    idp_yaml = f"""
apiVersion: harness.io/v1
kind: component
orgIdentifier: {ORG_IDENTIFIER}
projectIdentifier: {PROJECT_IDENTIFIER}
type: Service
identifier: {identifier}
name: {repo_name}
owner: group:account/IDP_Test
spec:
  lifecycle: production
metadata:
  description: "{repo_description}"
  annotations:
    backstage.io/source-location: url:https://github.com/{GITHUB_ORG}/{repo_name}
    backstage.io/techdocs-ref: dir:.
  tags:
    - auto-onboarded
"""

    # The Harness API endpoint for creating entities
    harness_url = (
        f"https://qa.harness.io/v1/entities"
        f"?convert=false&dry_run=false"
        f"&orgIdentifier={ORG_IDENTIFIER}&projectIdentifier={PROJECT_IDENTIFIER}"
    )
    # The payload for the Harness API request
    payload = {
        "yaml": idp_yaml,
        "git_details": {
            "branch_name": "main",
            "file_path": f"{repo_name}/idp.yaml",
            "commit_message": f"{repo_description}",
            "connector_ref": CONNECTOR_REF,
            "store_type": "REMOTE",
            "repo_name": CENTRAL_REPO,
            "is_harness_code_repo": False
        }
    }
    # Send the request to the Harness API
    response = requests.post(harness_url, headers=HARNESS_HEADERS, data=json.dumps(payload))
    # Check the response status code
    if response.status_code >= 200 and response.status_code < 300:
        print(f"[:heavy_check_mark:] Registered in Harness: {repo_name}")
    else:
        print(f"[Harness ERROR] {repo_name}: {response.status_code} - {response.text}")
# === MAIN FLOW ===
# This function fetches all repositories from the GitHub organization and creates a Harness IDP entity for each one
def main():
    print("Fetching repositories...")
    # The GitHub API endpoint for listing repositories
    url = f"https://api.github.com/orgs/{GITHUB_ORG}/repos?per_page=100"
    # The list of repositories
    repos = []
    # Loop until all repositories are fetched
    while url:
        # Send the request to the GitHub API
        res = requests.get(url, headers=GITHUB_HEADERS)
        # Check the response status code
        if res.status_code != 200:
            print(f"[ERROR] GitHub list failed: {res.status_code}")
            break
        # Extract the list of repositories along with its description from the response
        data = res.json()
        repos.extend([
            {"name": r["name"], "description": r.get("description") or ""}
            for r in data
        ])
        # Get the next page URL from the response headers
        url = res.links.get("next", {}).get("url")
    # Print the number of repositories found
    print(f"Found {len(repos)} repositories.")
    # Loop through the list of repositories and create a Harness IDP entity for each one
    for repo in repos:
        try:
            create_harness_entity(repo["name"], repo["description"])
        except Exception as e:
            print(f"[ERROR] {repo}: {e}")
if __name__ == "__main__":
    main()