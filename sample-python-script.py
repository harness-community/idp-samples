## Example Script to periodically update a metadata in catalog according to the values fetched from the opensource endpoint
import requests
import random

# Define the API endpoint and headers
url = 'https://app.harness.io/gateway/v1/catalog/custom-properties/entity'
headers = {
    'Harness-Account': 'ACCOUNT_ID',  # Replace with your actual account ID
    'Content-Type': 'application/json',
    'x-api-key': 'X_API_KEY'  # Replace with your actual API key
}

# Fetch the product data from the API
product_url = 'https://dummyjson.com/products'
response = requests.get(product_url)

# Check if the response is successful
if response.status_code == 200:
    data = response.json()

    # Extract stock data
    products = data.get("products", [])
    total_stock = sum(product.get("stock", 0) for product in products)

    # Introduce variability
    random_max_possible_stock = random.randint(500, 2000)  # Randomize max stock
    random_factor = random.uniform(0.5, 1)  # Random multiplier for variation

    # Calculate base score and apply randomness
    base_score = (total_stock / random_max_possible_stock) * 100
    code_coverage_score = min(base_score * random_factor, 100)  # Ensure < 100

    print(f"Code Coverage Score: {code_coverage_score:.2f}")

    # Prepare the data to update the code coverage score
    data_payload = {
        "entity_ref": "warehouse",
        "property": "metadata.codeCoverageScore",
        "value": round(code_coverage_score, 2)  # Send as a number, not a string
    }

    # Make the POST request to update the value
    update_response = requests.post(url, headers=headers, json=data_payload)

    # Check the response from the update request
    if update_response.status_code == 200:
        print("Code coverage score updated successfully!")
        print("Response:", update_response.json())
    else:
        print(f"Failed to update the code coverage score. HTTP Status Code: {update_response.status_code}")
        print("Response:", update_response.text)
else:
    print(f"Failed to fetch product data. HTTP Status Code: {response.status_code}")
