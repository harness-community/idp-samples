import os
import re
import argparse
from datetime import datetime, timezone
import sys
import requests
import yaml
import docker
import subprocess


def extract_image_and_tag(dockerfile_path: str, stage_name: str):
    """
    Extracts the image name and tag for a specific stage from a Dockerfile.

    Args:
        dockerfile_path (str): Path to the Dockerfile
        stage_name (str): Name of the stage to extract image and tag from

    Returns:
        Tuple: A tuple of (image_name, tag) or (None, None) if not found
    """

    stage_pattern = rf"(?i)^FROM\s+(?P<image>\S+)(?:\s+AS\s+{stage_name})"

    build_arg_pattern = r"\$\{(?P<arg_name>\w+):-(?P<default_value>[^}]+)\}"

    with open(dockerfile_path, "r") as dockerfile:
        lines = dockerfile.readlines()

    for line in lines:
        match = re.match(stage_pattern, line)
        if match:
            image = match.group("image")
            # Handle build argument with a default value (e.g., ${BASE_IMAGE:-default})
            arg_match = re.match(build_arg_pattern, image)
            if arg_match:
                image = arg_match.group("default_value")
            # Split image into name and tag
            if ":" in image:
                image_name, tag = image.split(":", 1)
            else:
                image_name, tag = image, "latest"  # Default tag
            return image_name, tag

    return None, None


def fetch_catalog_attributes(base_path: str, service: str):
    """
    Read the catalog-info.yaml to determine any override on the relative docker path.

    Args:
        base_path (str): Base path of the folder containing the service repo
        service (str): The name of the repo or service

    Raises:
        FileNotFoundError: No catalog-info yaml was found
        KeyError: Missing expected keys in the YAML file
        yaml.YAMLError: Error parsing the YAML file

    Returns:
        tuple: A tuple containing:
            - string: Relative path to the dockerfile configured
            - string: Language tag if present, None otherwise
    """
    try:
        # Construct the file path
        file_path =  determine_catalog_path (base_path, service)

        print(f"Inspecting catalog file at {file_path}")

        # Check if the file exists
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File {file_path} not found.")

        # Open and read the YAML file
        with open(file_path, "r") as file:
            data = yaml.safe_load(file)

        print(f"yaml data: {data}")

        # Extract docker path from annotations
        docker_path = (
            data.get("metadata", {})
            .get("annotations", {})
            .get("acme/docker-path", None)
        )

        # Extract tags and find the first matching language tag
        tags = data.get('metadata', {}).get('tags', [])
        match_list = {"python", "java", "go", "nodejs"}
        matching_tags = list(set(tags) & match_list)
        
        language = matching_tags[0] if matching_tags else None
        
        print(f"annotations: {docker_path}, language_tag: {language}")
        return docker_path, language

    except FileNotFoundError as fnf_error:
        print(f"{fnf_error}")
        return None, None
    except yaml.YAMLError as yaml_error:
        print(f"Error parsing YAML file: {yaml_error}")
        return None, None
    except KeyError as key_error:
        print(f"Missing expected key: {key_error}")
        return None, None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None, None



def updateCatalogAttributes(
    harness_account_id: str,
    harness_api_key: str,
    service_entity: str,
    properties_array_name: str,
    properties_array: list,
):
    """
    Read Update the IDP catalog attributes

    :param harness_account_id (str): Harness account id
    :param harness_api_key (str): The harness api key
    :param service_entity (str): the component service name
    :param properties_array_name (str): Name of the property group for naming timestamp attribute
    :param properties_array (str): The property array object json format
        properties_array = [
            {
           "property": "metadata.xyz.abc",
            "value": "somevalue"
            }
        ]
    Returns:
        Bool:
    """

    url = "https://app.harness.io/gateway/v1/catalog/custom-properties/entity"

    dateTimeStamp = dateTimeStamp = datetime.now(timezone.utc).isoformat()

    dateTimeStampMetadata = f"{properties_array_name}TimeStamp"

    timestamp = {"property": dateTimeStampMetadata, "value": dateTimeStamp}

    properties_array.append(timestamp)

    headers = {
        "Harness-Account": harness_account_id,
        "Content-Type": "application/json",
        "x-api-key": harness_api_key,
    }

    print(headers)

    data_payload = {"entity_ref": service_entity, "properties": properties_array}

    print(data_payload)

    update_response = requests.post(url, headers=headers, json=data_payload)

    if update_response.status_code == 200:
        print("updated successfully!")
        print("Response:", update_response.json())
        return True
    else:
        print(f"Failed to update . HTTP Status Code: {update_response.status_code}")
        print("Response:", update_response.text)
        return False
        


def determine_catalog_path (base_path:str, servicename:str):
    """Returns the catalog path to use
        checks first the repo path gitreponame/.harness/idp/catalog-info.yaml
        then falls back to 
    Args:
        base_path (str): _description_
        servicename (str): _description_
    """    
    harness_infra_path = f"{base_path}/harness-infra/idp/services/{servicename}/catalog-info.yaml"
    service_path_override = f"{base_path}/{servicename}/.harness/idp/catalog-info.yaml"

    if os.path.exists(service_path_override):
        print (f"Found catalog-info in service repository: {service_path_override}, ignoring one in harness-infra repo")
        return service_path_override   
    return harness_infra_path

