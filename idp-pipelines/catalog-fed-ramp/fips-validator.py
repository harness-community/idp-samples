import os
import re
import argparse
from datetime import datetime, timezone
from common import updateCatalogAttributes, extract_image_and_tag, fetch_catalog_attributes
import sys
import requests
import yaml
import docker
import subprocess


def extract_images_from_chart (chart_full_path: str):
    """extract images from the chart

    Args:
        chart_full_path (str): specify the path to the chart

    Returns:
        _type_: array of image path
    """    
    with open(chart_full_path, "r") as f:
        data = yaml.safe_load(f)

    #assuming chart has an annotation format
    #annotations:
    #acme.com/images: |
    #    - name: account-lifecycle-api
    #      image: docker.io/acme/account-lifecycle-api:{{ .Chart.AppVersion }}
    image_regex = r"([a-zA-Z0-9\-\.]+\/[a-zA-Z0-9\-\.]+\/[a-zA-Z0-9\-\.]+)(?=:|\{\{)"

    # Find all image repository paths
    try :
        image_matches = re.findall(image_regex, data['annotations']['acme.com/images'])
    except KeyError as e:
        print(f"No image annotations found! {e}")
        return None

    # Output the results
    #for name in image_names:
    #    print("Image repository full name:", name)        
    for image in image_matches:
        print("Image repository full path:", image)    
    
    return image_matches 


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
        if image != None and "python" in image :
            return "python", image, tag
        if image != None and "go" in image:
            return "go", image, tag
        if image != None and "node" in image:
            return "nodejs", image, tag
        if image != None and ("java" in image or "jre" in image or "jdk" in image):
            return "java", image, tag

    return None, None, None


def docker_md5_test(language, registry_path:str, tag:str="latest"):
    """tried to run fips check using md5

    Args:
        registry_path (str): registry path to image
        tag (str, optional): tag to use Defaults to "latest".
        returns True to pass the test
    """

    if language=="python": 
        print ("docker_md5_test for python")

        client = docker.from_env()
        image_pull = f"{registry_path}:{tag}"
        try:
            # pull the image
            image = client.images.pull(image_pull)
            print(f"Successfully pulled {image_pull}")

            # grab image config and lables
            image = client.images.get(image_pull)
            labels = image.attrs.get("Config", {}).get("Labels", {})

            print ("Labels found")
            for label_key, label_value in labels.items():
                print(f"{label_key}: {label_value}")                

            print("Testing md5")

            docker_command = [
                "docker",
                "run",
                "--rm",
                "--entrypoint",
                "python3",
                image_pull,
                "-u",
                "-c",
                "import hashlib;print('Attempting to hash');print(hashlib.md5(b'blah').hexdigest());"
            ]

            result = subprocess.run(docker_command, capture_output=True, text=True)

            print (f"Results: {result.returncode}, output: {result.stdout}, stderr:{result.stderr}, additional debugging : {result.check_returncode}, result: {result}")

            if "UnsupportedDigestmodError" in result.stderr:
                # only return true if UnsupportedDigestmodError is found in error output
                return True
            else: 
                return False
     


        except docker.errors.APIError as e:
            print(f"Error pulling image: {e}")
            #raise "Unable to run docker"
        except docker.errors.ImageNotFound:
            print(f"Image '{image_pull}' not found.")
            #raise "Unable to run docker"
        except Exception as e:
            print(f"An error occurred while retrieving image labels: {e}")
            #raise "Unable to run docker"

            
    if language=="go" or language=="java": 
        print ("docker_md5_test for go / java")       

        client = docker.from_env()
        image_pull = f"{registry_path}:{tag}"
        try:
            # pull the image
            image = client.images.pull(image_pull)
            print(f"Successfully pulled {image_pull}")

            # grab image config and labels
            image = client.images.get(image_pull)
            labels = image.attrs.get("Config", {}).get("Labels", {})
            print ("Labels found")
            for label_key, label_value in labels.items():
                print(f"{label_key}: {label_value}")                
                if (label_key=="com.acme.mirror.pipeline.name" and ( label_value =="mirror_chainguard_acme.com_go-fips" or label_value=="mirror_chainguard_acme.com_jdk-fips")) :
                    print ("label matched!")
                    return True
                    
            return False
        except docker.errors.APIError as e:
            print(f"Error pulling image: {e}")
            #raise "Unable to run docker"
        except docker.errors.ImageNotFound:
            print(f"Image '{image_pull}' not found.")
            #raise "Unable to run docker"
        except Exception as e:
            print(f"An error occurred while retrieving image labels: {e}")
            #raise "Unable to run docker"                

            
    if language=="nodejs" : 

        print ("docker crypto check for nodejs")

        client = docker.from_env()
        image_pull = f"{registry_path}:{tag}"
        try:
            # pull the image
            image = client.images.pull(image_pull)
            print(f"Successfully pulled {image_pull}")

            # grab image config and lables
            image = client.images.get(image_pull)
            labels = image.attrs.get("Config", {}).get("Labels", {})

            print ("Labels found")
            for label_key, label_value in labels.items():
                print(f"{label_key}: {label_value}")                

            print (" Checking ")
            docker_command = [
                "docker",
                "run",
                "--rm",
                "--entrypoint",
                "node",
                image_pull,
                "-e",
                "const crypto = require('crypto'); crypto.getFips() ? process.exit(0):process.exit(1)"
            ]


            result = subprocess.run(docker_command, capture_output=True, text=True)

            print (f"Results: {result.returncode}, output: {result.stdout}, stderr:{result.stderr}, additional debugging : {result.check_returncode}, result: {result}")

            #return code 1 = false , no fips support
            if result.returncode :
                return False
            else: 
                return True
     
        except docker.errors.APIError as e:
            print(f"Error pulling image: {e}")
            #raise "Unable to run docker"
        except docker.errors.ImageNotFound:
            print(f"Image '{image_pull}' not found.")
            #raise "Unable to run docker"
        except Exception as e:
            print(f"An error occurred while retrieving image labels: {e}")
            #raise "Unable to run docker"  

    # no language found 
    return None


def testing_docker_image (registry_url:str, language: str):
    """Testing registry image manually
    Args:
        registry_url (str): registry url such as docker.io/acmedev/mirror_chainguard_acme.com_python-fips:3.12-dev
        language (str): python, go, java, nodejs
    """
    print(f"Using test url: {registry_url}")
    
    # Use a regular expression to extract both repository and tag
    match = re.match(r'^(.*?):([^:]+)$', registry_url)
    if match:
        repository = match.group(1)
        tag = match.group(2)
        language = language
        test_result = docker_md5_test(language, repository, tag)
        print (f"Image passing FIP testing : {test_result}")



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

    parser.add_argument(
        "--test_registry_url", type=str, help="example: docker.io/acmedev/mirror_chainguard_acme.com_python-fips:3.12-dev", default="None"
    )    

    parser.add_argument(
        "--test_language", type=str, help="python,go,java,nodejs", default="None"
    )        

    parser.add_argument("--harness_account_id", type=str, help="harness account id")

    parser.add_argument("--harness_api_token", type=str, help="API Token")

    parser.add_argument(
        "--base_dir",
        type=str,
        help="Path to base folder holding repos",
        default="/harness",
    )

    args = parser.parse_args()
    base_path = args.base_dir
    catalog_entity = args.catalog_entity
    dockerfile_path = args.dockerfile_path
    service_components = catalog_entity.split("/")
    servicename = service_components[1]

    harness_account_id = args.harness_account_id
    harness_api_token = args.harness_api_token

    # fetch catalog-info values for relative Dockerfile path and language label
    print(f"BASE PATH: {base_path}  for SERVICE : {servicename}")
    relative_path, language_tag = fetch_catalog_attributes(base_path, servicename)  or (None, None)
    dockerfile_path_override = f"/{base_path}/{servicename}/{relative_path}"

    # if the configure path exists for dockerfile use it instead
    if relative_path != None and os.path.exists(dockerfile_path_override):
        dockerfile_path = dockerfile_path_override
    else:
        print(f" configurepath not found using  default instead")

    print(f"catalog_entity: {catalog_entity}   dockerfilePath: {dockerfile_path}")

    # determine the language based on docker base tag
    language, image, tag = determine_image_language(
        dockerfile_path, ["build-release-stage", "runtime-stage", "runner", "base"]
    )

    if args.test_registry_url !="None" :
        # this block if only for manual testing of an image
        testing_docker_image(args.test_registry_url, args.test_language)
       
    #extract register url from the service's chart
    chart_path = f"{base_path}/{servicename}/charts/Chart.yaml"
    registry_url = extract_images_from_chart(chart_path)

    # set the language based on its tag if cannot decipher from Dockerfile
    if language==None: 
        print ("Could not decipher language from dockerfile tag, using configured label from catalog-info")
        language = language_tag

    print(f"    Image supporting language {language},  {image} {tag}, chart path: {chart_path}, registry: {registry_url}")

    # only allow one image in the chart annotations
    try: 
        if registry_url != None and len(registry_url)==1:
            for url in registry_url:
                print (url)
                
                result = docker_md5_test(language, url)
                if result != None:
                    print (f"Pass FIPS test : {result}")
                    if result==True :
                        properties_array = [
                            {"property": "metadata.fips.compliance", "value": True}
                        ]
                    else:
                        properties_array = [
                            {"property": "metadata.fips.compliance", "value": False}
                        ]
                    print (f"Updating catalog with {properties_array}")
                    updateResultFlag = updateCatalogAttributes (harness_account_id,
                                    harness_api_token,
                                    catalog_entity,
                                    "metadata.fips.compliance",
                                    properties_array)
                    if (updateResultFlag==False):
                        raise ValueError("Failed to update catalog")
                else:
                    print ("No matching language... skipping")
        else:
            print(f"Only 1 image allowed: {registry_url}" )
            properties_array = [
                {"property": "metadata.fips.compliance", "value": False}
            ]
            print (f"Updating catalog with {properties_array}")
            updateResultFlag = updateCatalogAttributes (harness_account_id,
                            harness_api_token,
                            catalog_entity,
                            "metadata.fips.compliance",
                            properties_array)  
            if (updateResultFlag==False):
                raise ValueError("Failed to update catalog")    
                
    except Exception as e:
        print(f"{e}")
        print("Exiting utility due to fatal error")
        sys.exit(1)            
 

if __name__ == "__main__":
    
        
    main()


