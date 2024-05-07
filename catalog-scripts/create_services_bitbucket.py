import requests
import random
from requests.auth import HTTPBasicAuth
import nltk

def create_directory_and_yaml(repo_name, num_directories, yaml_filename, yaml_content_template):
    
    username = ""  # Your Bitbucket username
    app_password = ""  # Your Bitbucket app password
    workspace = "" # Your Bitbucket workspace
    prefix_path = "mock_rserver_root/configs/services/" # Your prefix_path
    suffix_path = "/.ownership/" # Your suffix_path

    base_url = f"https://api.bitbucket.org/2.0/repositories/{workspace}/test/src"

    english_words = set(nltk.corpus.words.words())

    for i in range(num_directories):
        url = f"{base_url}"
        files = []
        directory_name = random.choice(list(english_words)).lower() + "-service"
        directory_path = prefix_path + directory_name + suffix_path

        updated_yaml_content = yaml_content_template.replace("<replace with directory_name>", directory_name)
        updated_yaml_content = updated_yaml_content.replace("<replace with source-location>", f"url:https://bitbucket.org/{workspace}/{repository_name}/src/main/{directory_path}")

        # Create YAML file
        yaml_file_content = updated_yaml_content.strip()
        yaml_file_path = directory_path + yaml_filename

        yaml_file_data = {
            "message": f"Create YAML file '{yaml_file_path}'",
           f"/{yaml_file_path}": yaml_file_content,
        }

        response = requests.post(url, auth=HTTPBasicAuth(username, app_password), files=files, data=yaml_file_data)
        if response.status_code == 201:
            print(f"Created {directory_name}")

    if response.status_code == 201:
        print("Files created successfully!")
    else:
        print("Failed to upload file. Status code:", response.status_code)
        print("Error message:", response.text)

repository_name = ""
num_directories = 50
yaml_filename = ""

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

create_directory_and_yaml(repository_name, num_directories, yaml_filename, yaml_content_template)
