import requests

# Define the base API endpoint and headers
base_api_url = 'https://idp.harness.io/ACCOUNT_ID/idp/api/catalog/entities/by-query?filter=kind%3Dlocation&limit=200'
delete_api_url = 'https://idp.harness.io/ACCOUNT_ID/idp/api/catalog/entities/by-uid/{uid}'
headers = {
    'x-api-key': 'Harness PAT',
    'Harness-Account': 'Account ID'
}

def fetch_all_pages(base_api_url, headers):
    all_items = []
    next_cursor = None

    while True:
        # Append the cursor to the URL if it exists
        api_url = base_api_url
        if next_cursor:
            api_url += f'&cursor={next_cursor}'
        
        # Fetch data from the API
        response = requests.get(api_url, headers=headers)
        data = response.json()

        # Add items to the all_items list
        all_items.extend(data.get('items', []))

        # Check if there is a next page
        next_cursor = data.get('nextCursor')
        if not next_cursor:
            break

    return all_items

# Function to extract uids of entities with specific error
def get_not_found_error_entities(items):
    not_found_error_entities = []
    for item in items:
        if 'status' in item and 'items' in item['status']:
            for status_item in item['status']['items']:
                if status_item.get('level') == 'error' and status_item.get('error', {}).get('name') == 'NotFoundError':
                    not_found_error_entities.append(item['metadata']['uid'])  # Use the uid directly
    return not_found_error_entities

# Function to delete entities by UID
def delete_entities(uids, delete_api_url, headers):
    for uid in uids:
        delete_url = delete_api_url.format(uid=uid)
        response = requests.delete(delete_url, headers=headers)
        if response.status_code == 204:
            print(f"Deleted entity with UID: {uid}")
        else:
            print(f"Failed to delete entity with UID: {uid}, Status Code: {response.status_code}, Response: {response.text}")

# Fetch all pages
all_items = fetch_all_pages(base_api_url, headers)

# Get the uids of entities with NotFoundError
not_found_error_entities_uids = get_not_found_error_entities(all_items)

# Print the UIDs of the entities to be deleted
print('Entities with NotFoundError status to be deleted (UIDs):')
for uid in not_found_error_entities_uids:
    print(uid)

# Delete the entities
delete_entities(not_found_error_entities_uids, delete_api_url, headers)
