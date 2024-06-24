import requests

def create_ruleset(system, ruleset):
    index_mapping = {
        "linux": "linux_ruleset",
        "windows": "window_ruleset",
        "genian": "genian_ruleset",
        "fortigate": "fortigate_ruleset"
    }

    index_name = index_mapping.get(system)
    
    if not index_name:
        print("Invalid system choice.")
        return
    
    url = f"http://3.35.81.217:9200/{index_name}/_doc"
    headers = {
        "Content-Type": "application/json"
    }
    
    response = requests.post(url, headers=headers, json=ruleset)
    
    if response.status_code == 201:
        print("Ruleset created successfully.")
    else:
        print(f"Failed to create ruleset. Status code: {response.status_code}")
        print("Response:", response.json())
