import os
import re
import argparse
from datetime import datetime, timezone
from common import updateCatalogAttributes, extract_image_and_tag, fetch_catalog_attributes
import sys
import requests
import yaml


# Function to check if docker image matches
def compliant_image(image: str, image_tag: str):
    """
    Check to see if the image is in compliance with acme/platform-base or mirror_ironbank
    :param image(str): The image
    :param image_tag(str): The tag
    :return: Boolean
    """
    images_allowed = {
        "image_path": """
            mirror_chainguard_acme.com
            acme/platform-base
            acme/mirror_ironbank
            """,
        "tags": """
            latest
            latest-ironbank
            """            
    }

    image_path_items = [item.strip() for item in images_allowed["image_path"].strip().splitlines()]
    tags_items = [item.strip() for item in images_allowed["tags"].strip().splitlines()]

# add back if need to check image tags
#    if any(partial in image for partial in image_path_items) and any(partial in image_tag for partial in tags_items):
#        return True

    # using image path check only , no need to check the tag for now
    if any(partial in image for partial in image_path_items):
        return True

    return False
    
    

def is_docker_image_compliant(dockerfile_path: str, fromstages: list):
    """
    Loop through all stages and examine the first compliance
    :param dockerfile_path (str): The docker path
    :param fromstages (list): All the matching possible stages
    :return: Boolean
    """
    for stage in fromstages:
        image, tag = extract_image_and_tag(dockerfile_path, stage)
        print(f"   stage: {stage} image: {image} tag: {tag}")
        if image != None and compliant_image(image, tag):
            return True
    return False


def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(
        description="Process a Dockerfile for compliance checks."
    )
    parser.add_argument(
        "--dockerfile_path", type=str, help="Path to the Dockerfile to process"
    )

    parser.add_argument(
        "--catalog_entity", type=str, help="example: component:default/demo-catalog-svc"
    )

    parser.add_argument("--harness_account_id", type=str, help="harness account id")

    parser.add_argument("--harness_api_token", type=str, help="API Token")

    parser.add_argument(
        "--base_path",
        type=str,
        help="Path to base folder holding repos",
        default="/harness",
    )

    args = parser.parse_args()

    catalog_entity = args.catalog_entity

    dockerfile_path = args.dockerfile_path

    base_path = args.base_path

    service_components = catalog_entity.split("/")

    catalog_svc = service_components[1]

    print(f"BASE PATH: {base_path}  for SERVICE : {catalog_svc}")

    # Check the catalog-yaml override to passed default
    relative_path, language_tag = fetch_catalog_attributes(base_path, catalog_svc)  or (None, None)

    dockerfile_path_override = f"/{base_path}/{catalog_svc}/{relative_path}"

    if relative_path != None and os.path.exists(dockerfile_path_override):
        dockerfile_path = dockerfile_path_override

    print(
        f"Catalog_entity: {catalog_entity} Found annotation config path: {dockerfile_path} "
    )
    is_compliant = is_docker_image_compliant(
        dockerfile_path, ["build-release-stage", "runtime-stage", "runner", "base"]
    )
    print(f"    image compliance {is_compliant} found at {dockerfile_path}")

    # prepare to update idp catalog
    harness_account_id = args.harness_account_id
    harness_api_token = args.harness_api_token

    properties_array = [
        {"property": "metadata.baseImage.compliance", "value": is_compliant}
    ]

    try:
        updateResultFlag = updateCatalogAttributes(
            harness_account_id,
            harness_api_token,
            catalog_entity,
            "metadata.baseImage.compliance",
            properties_array,
        )
        if (updateResultFlag==False):
            raise ValueError("Failed to update catalog")
        
    except Exception as e:
        print(f"{e}")
        print("Exiting utility due to fatal error")
        sys.exit(1)            


if __name__ == "__main__":
    main()
