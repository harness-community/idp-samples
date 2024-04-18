import requests
import base64
import uuid
import random
import nltk
import time

def create_directory_and_yaml(repo_name, num_directories, yaml_filename, yaml_content_template):
    # GitHub username and personal access token
    username = ""
    token = ""
    prefix_path = "mock_rserver_root/configs/services/"
    suffix_path = ".ownership/"

    # Base URL for GitHub API
    base_url = "https://api.github.com/repos/{}/{}/contents/{}".format(username, repo_name, prefix_path)

    # Headers for authentication
    headers = {
        "Authorization": "token {}".format(token)
    }

    # Load the NLTK words corpus
    english_words = set(nltk.corpus.words.words())

    for i in range(num_directories):
        # Generate random directory name from valid English words ending with "-service"
        directory_name = random.choice(list(english_words)).lower() + "-service"

        # Create directory
        directory_path = directory_name + suffix_path
        directory_data = {
            "message": "Create directory '{}'".format(directory_path)
        }

        # Replace directory name in YAML content template
        updated_yaml_content = yaml_content_template.replace("<replace with directory_name>", directory_name)
        updated_yaml_content = updated_yaml_content.replace("<replace with source-location>", "url:https://github.com/vikyathharekal/book-my-tickets/blob/main/{}{}".format(prefix_path, directory_name))

        # Create YAML file
        yaml_file_content = updated_yaml_content.strip()
        yaml_file_path = directory_path + yaml_filename
        url = base_url + yaml_file_path
        
        yaml_file_data = {
            "message": "Create YAML file '{}'".format(yaml_file_path),
            "content": base64.b64encode(yaml_file_content.encode()).decode(),
            "branch": "main"
        }
        yaml_file_response = requests.put(url, headers=headers, json=yaml_file_data)
        if yaml_file_response.status_code != 201:
            print("Failed to create YAML file '{}'. Status code: {}".format(yaml_file_path, yaml_file_response.status_code))

        print("Created '{}' services".format(i + 1))

# Replace these values with your repository name and specify the number of directories you want to create
repository_name = ""
num_directories = 10  # Specify the number of directories you want to create
yaml_filename = "catalog-info.yaml"

# YAML content template with placeholder for directory name and source location
yaml_content_template = """
apiVersion: backstage.io/v1alpha1
kind: Component
metadata:
  tags:
    - java
    - map-my-trip
  name: <replace with directory_name>
  annotations:
    backstage.io/source-location: <replace with source-location>
    backstage.io/techdocs-ref: dir:.
    jira/project-key: IDP
    backstage.io/kubernetes-label-selector: 'app=idp-ui'
    backstage.io/kubernetes-namespace: '63feee14cbf66e3c798c4bdc'
spec:
  type: service
  system: movie
  lifecycle: experimental
  owner: Harness_Account_All_Users
"""

# Call the function to create directories and YAML files
create_directory_and_yaml(repository_name, num_directories, yaml_filename, yaml_content_template)
