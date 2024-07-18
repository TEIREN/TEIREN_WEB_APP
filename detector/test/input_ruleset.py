import requests

def get_user_input(index_choice):
    # 사용자로부터 룰셋 정보를 입력받습니다.
    name = input("Enter the name of the ruleset: ")
    severity = int(input("Enter the severity (e.g., 1, 2, 3, 4): "))

    must_clauses = []

    while True:
        # 사용자로부터 프러퍼티와 벨류를 입력받습니다.
        property_name = input("Enter the property name (e.g., message, programname, EventID, SourceName): ")
        property_value = input(f"Enter the value for {property_name}: ")

        # 입력받은 프러퍼티와 벨류를 쿼리에 추가합니다.
        must_clauses.append({
            "match": {
                property_name: property_value
            }
        })

        # 추가 프러퍼티 입력 여부를 확인합니다.
        add_more = input("Do you want to add more properties? (y/n): ").strip().lower()
        if add_more != 'y':
            break

    query = {
        "query": {
            "bool": {
                "must": must_clauses
            }
        }
    }

    # index_choice에 따라 system을 자동으로 매핑합니다.
    system_mapping = {
        1: "linux",
        2: "windows",
        3: "genian",
        4: "fortigate"
    }
    system = system_mapping.get(index_choice, "unknown")

    return {
        "name": name,
        "system": system,
        "query": query,
        "severity": severity
    }

def select_index():
    print("Select the index to save the ruleset:")
    print("1. linux_ruleset")
    print("2. window_ruleset")
    print("3. genian_ruleset")
    print("4. fortigate_ruleset")
    choice = int(input("Enter your choice (1-4): "))
    if choice not in [1, 2, 3, 4]:
        raise ValueError("Invalid choice, please select a number between 1 and 4.")
    return choice

def main():
    index_choice = select_index()

    ruleset = get_user_input(index_choice)

    index_mapping = {
        1: "linux_ruleset",
        2: "window_ruleset",
        3: "genian_ruleset",
        4: "fortigate_ruleset"
    }
    
    index_name = index_mapping.get(index_choice)
    
    if not index_name:
        print("Invalid index choice.")
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

if __name__ == "__main__":
    main()
