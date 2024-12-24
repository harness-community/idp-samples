import requests
import json
import subprocess

# Function to fetch user groups from Harness
def fetch_user_groups():
    url = "https://app.harness.io/ng/api/user-groups"
    headers = {
        "x-api-key": "YOUR_API_KEY_HERE"
    }
    params = {
        "accountIdentifier": "string",
        "orgIdentifier": "string",
        "projectIdentifier": "string",
        "searchTerm": "string",
        "filterType": "INCLUDE_INHERITED_GROUPS",
        "pageToken": "string"
    }

    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to fetch user groups. Status code: {response.status_code}")
        return None

# Function to fetch users for a specific user group
def fetch_users_for_user_group(user_group_id):
    url = "https://app.harness.io/ng/api/user/aggregate"
    headers = {
        "Content-Type": "application/json",
        "x-api-key": "YOUR_API_KEY_HERE"
    }
    params = {
        "accountIdentifier": "string",
        "orgIdentifier": "string",
        "projectIdentifier": "string",
        "searchTerm": "string",
        "pageToken": "string"
    }
    data = {
        "resourceGroupIdentifiers": [
            user_group_id
        ],
        "roleIdentifiers": []
    }

    response = requests.post(url, headers=headers, params=params, json=data)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to fetch users for user group {user_group_id}. Status code: {response.status_code}")
        return None

# Function to fetch Jira teams and users
def fetch_jira_data():
    url = "https://your-jira-instance/rest/api/2/team"
    headers = {
        "Authorization": "Basic YOUR_API_TOKEN",
        "Content-Type": "application/json"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        teams = json.loads(response.text)
        # Extract team names and users
        team_names = [team['name'] for team in teams]
        users = []
        for team in teams:
            for member in team['members']:
                users.append(member['emailAddress'])
        return team_names, users
    else:
        print("Failed to fetch Jira data")
        return None, None

# Function to compare Jira data with current state in Harness
def compare_data_with_harness(jira_team_names, jira_users, harness_user_groups):
    new_teams = [team_name for team_name in jira_team_names if team_name not in harness_user_groups]
    return new_teams, jira_users

# Function to generate Terraform configuration for changes
def generate_terraform_config(new_teams, jira_users):
    terraform_config = ""
    for team_name in new_teams:
        # Fetch users for the new team from Jira
        team_users = [user for user in jira_users if user.endswith("@yourdomain.com")] # Filter users if necessary
        terraform_config += f'''
resource "harness_platform_usergroup" "{team_name}_group" {{
  identifier         = "{team_name.lower().replace(" ", "_")}"
  name               = "{team_name}"
  org_id             = "your_org_id"
  project_id         = "your_project_id"
  externally_managed = false
  user_emails        = {json.dumps(team_users)}
}}
'''
    return terraform_config

# Function to apply Terraform configuration to update Harness
def apply_terraform_config(terraform_config):
    # Write Terraform configuration to a file
    with open("terraform_config.tf", "w") as f:
        f.write(terraform_config)

    # Run Terraform commands to apply the configuration
    try:
        subprocess.run(["terraform", "init"])
        subprocess.run(["terraform", "apply", "-auto-approve"])
        return True
    except Exception as e:
        print(f"Error applying Terraform configuration: {str(e)}")
        return False

# Main function for periodic synchronization
def main():
    # Fetch data from Jira
    jira_team_names, jira_users = fetch_jira_data()

    if jira_team_names and jira_users:
        # Fetch user groups from Harness
        harness_user_groups = fetch_user_groups()
        if harness_user_groups:
            harness_user_group_names = [group['name'] for group in harness_user_groups]

            # Compare Jira data with current state in Harness
            new_teams, jira_users_for_new_teams = compare_data_with_harness(jira_team_names, jira_users, harness_user_group_names)

            # Generate Terraform configuration for changes
            terraform_config = generate_terraform_config(new_teams, jira_users_for_new_teams)

            # Apply Terraform configuration to update Harness
            success = apply_terraform_config(terraform_config)

            if success:
                print("Harness configuration updated successfully")
            else:
                print("Failed to update Harness configuration")
        else:
            print("Failed to fetch user groups from Harness")
    else:
        print("Failed to fetch Jira data or no data available")

if __name__ == "__main__":
    main()
