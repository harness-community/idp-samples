import requests

def list_directories(repo_name, token):
    # GitHub username
    username = ""
    path = "services"

    # Base URL for GitHub API
    base_url = f"https://api.github.com/repos/{username}/{repo_name}/contents/{path}"

    # Headers for authentication
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }

    print("base_url {}", base_url)
    # Get the list of contents (directories and files) in the repository
    response = requests.get(base_url, headers=headers)
    if response.status_code != 200:
        print("Failed to retrieve contents from the repository. Status code:", response.status_code)
        return []

    contents = response.json()

    # Filter out directories
    directories = [content for content in contents if content["type"] == "dir"]
    return directories

def delete_files_in_directory(repo_name, directory_path, token):
    # GitHub username
    username = ""

    # Base URL for GitHub API
    base_url = f"https://api.github.com/repos/{username}/{repo_name}/contents"

    # Headers for authentication
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }

    # Get the list of contents (directories and files) in the directory
    response = requests.get(base_url + "/" + directory_path, headers=headers)
    if response.status_code != 200:
        print(f"Failed to retrieve contents from the directory '{directory_path}'. Status code:", response.status_code)
        return

    contents = response.json()

    # Delete each file within the directory
    for content in contents:
        if content["type"] == "file":
            file_path = content["path"]
            delete_file(repo_name, file_path, token)

def delete_file(repo_name, file_path, token):
    # GitHub username
    username = "vikyathharekal"

    # Base URL for GitHub API
    base_url = f"https://api.github.com/repos/{username}/{repo_name}/contents"

    # Headers for authentication
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }

    # Get the file details
    print(base_url + "/" + file_path)
    response = requests.get(base_url + "/" + file_path, headers=headers)

    if response.status_code != 200:
        print(f"Failed to retrieve file '{file_path}'. Status code:", response.status_code)
        return

    file_details = response.json()

    # Delete the file
    delete_url = base_url + "/" + file_path
    delete_data = {
        "message": f"Delete file '{file_path}'",
        "sha": file_details["sha"]  # Use the sha of the file
    }
    delete_response = requests.delete(delete_url, headers=headers, json=delete_data)
    if delete_response.status_code == 200:
        print(f"File '{file_path}' deleted successfully.")
    else:
        print(f"Failed to delete file '{file_path}'. Status code: {delete_response.status_code}")

# Replace "your_repository_name" with the name of your GitHub repository
repository_name = "book-my-tickets"

# Replace "<your_personal_access_token>" with your personal access token
token = ""

# List all directories in the repository
directories = list_directories(repository_name, token)

print(f"Found {len(directories)} directories")

# Delete all files inside each directory
for directory in directories:
    directory_path = directory["path"]
    delete_files_in_directory(repository_name, directory_path, token)
