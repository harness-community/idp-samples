import os
import re
import argparse
from datetime import datetime, timezone
from common import updateCatalogAttributes, extract_image_and_tag, fetch_service_path
import sys
import requests
import yaml
import docker
import subprocess


def determine_image_language(dockerfile_path: str, fromstages: list):
    """
    Determine the language from the matching stages
    :param dockerfile_path (str): Path to the Dockerfile
    :param fromstages (list): list of strings to filter
    :return: Boolean if crypto program executed successfully
    """
    for stage in fromstages:
        image, tag = extract_image_and_tag(dockerfile_path, stage)
        print(f"   stage: {stage} image: {image} tag: {tag}")
        # return first match
        if image != None and image.startswith("datarobotdev/platform-base-python"):
            return "python", image, tag
        if image != None and image.startswith("datarobotdev/platform-base-go"):
            return "go", image, tag
        if image != None and image.startswith("datarobotdev/platform-base-node"):
            return "nodejs", image, tag
        if image != None and image.startswith("datarobotdev/platform-base-java"):
            return "java", image, tag

    return None, None, None


def fips_build_check(language: str, image: str, tag: str, base_path: str):
    """
    An example to build docker in docker to run crypto test
    :param language (str): Programming language (go, nodejs, python)
    :param image (str): The image to test
    :param tag (str): The tag to pull
    :param base_path (str): The basedirectory holding the harness-infra repo
    :return: Boolean if crypto program executed successfully
    """
    client = docker.from_env()
    image_pull = f"{image}:{tag}"
    try:
        # pull the image
        image = client.images.pull(image_pull)
        print(f"Successfully pulled {image_pull}")

        # grab image config and lables
        image = client.images.get(image_pull)
        labels = image.attrs.get("Config", {}).get("Labels", {})
        configs = image.attrs.get("Config", {})
        print(f"Configs: {configs}")
        print(f"Labels: {labels}")

        # execute building image with test program
        print("Running docker build...")
        docker_command = [
            "docker",
            "build",
            "--build-arg",
            f"BASE_IMAGE={image_pull}",
            "-t",
            "fips-test",
            f"{base_path}/harness-infra/idp/fips/{language}/.",
        ]
        exit_code = subprocess.call(docker_command)
        if exit_code == 0:
            print("Docker build succeeded.")
        else:
            print(f"Error occurred during Docker build. Exit code: {exit_code}")

        # attempt to execute the built image
        print("Running docker container...")
        docker_command_run = ["docker", "run", "--rm", "fips-test"]
        exit_code = subprocess.call(docker_command_run)
        print(f"Docker run exited with code {exit_code}")

        if exit_code == 0:
            print("The container ran successfully.")
            return True

        print(f"An error occurred during Docker run. Exit code: {exit_code}")
        return False

    except docker.errors.APIError as e:
        print(f"Error pulling image: {e}")
    except docker.errors.ImageNotFound:
        print(f"Image '{image_pull}' not found.")
    except Exception as e:
        print(f"An error occurred while retrieving image labels: {e}")


def main():

    parser = argparse.ArgumentParser(
        description="Process a Dockerfile for FIPS checks."
    )
    parser.add_argument(
        "--dockerfile_path",
        type=str,
        help="Absolute path to the Default docker path file (usually root dir of repo)",
    )

    parser.add_argument(
        "--catalog_entity", type=str, help="example: component:default/demo-catalog-svc"
    )

    parser.add_argument("--harness_account_id", type=str, help="harness account id")

    parser.add_argument("--harness_api_token", type=str, help="API Token")

    parser.add_argument(
        "--base_repo_path",
        type=str,
        help="Path to base folder holding repos",
        default="/harness",
    )

    args = parser.parse_args()
    base_path = args.base_repo_path
    catalog_entity = args.catalog_entity
    dockerfile_path = args.dockerfile_path
    service_components = catalog_entity.split("/")
    catalog_svc = service_components[1]

    # check for custom configure path in catalog-info.yaml
    print(f"BASE PATH: {base_path}  for SERVICE : {catalog_svc}")
    relative_path, language_tag = fetch_service_path(base_path, catalog_svc)
    dockerfile_path_cfg = f"/{base_path}/{catalog_svc}/{relative_path}"

    # if the configure path exists for dockerfile use it instead
    if relative_path != None and os.path.exists(dockerfile_path_cfg):
        dockerfile_path = dockerfile_path_cfg
    else:
        print(f" configurepath not found using  default instead")

    print(f"catalog_entity: {catalog_entity}   dockerfilePath: {dockerfile_path}")

    # determine the language based on docker base tag
    language, image, tag = determine_image_language(
        dockerfile_path, ["build-release-stage", "runtime-stage", "runner", "base"]
    )

    print(f"    Image supporting language {language} {image} {tag}")

    # test the image with crypto test
    fips_compliance = fips_build_check(language, image, tag, base_path)

    # use for local testing
    # fips_compliance = fips_build_check ("python", "python", "slim-bullseye", base_path)

    # prepare to update the catalog
    harness_account_id = args.harness_account_id
    harness_api_token = args.harness_api_token
    properties_array = [
        {"property": "metadata.fips.compliance", "value": fips_compliance}
    ]

    # update the catalog
    # updateCatalogAttributes (harness_account_id,
    #                        harness_api_token,
    #                        catalog_entity,
    #                        "metadata.fips.compliance",
    #                        properties_array)


if __name__ == "__main__":
    main()
