import requests

def get_user_input(index_choice):
    # 사용자로부터 룰셋 정보를 입력받습니다.
    name = input("Enter the name of the ruleset: ")
    severity = int(input("Enter the severity (e.g., 1, 2, 3, 4): "))

    query = {}

    if index_choice == 1:
        # Linux 쿼리 입력
        message_value = input("Enter the message value: ")
        programname_value = input("Enter the programname value: ")
        query = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "match": {
                                "message": message_value
                            }
                        },
                        {
                            "match": {
                                "programname": programname_value
                            }
                        }
                    ]
                }
            }
        }
    elif index_choice == 2:
        # Windows 쿼리 입력
        event_id = int(input("Enter the EventID value: "))
        event_type = input("Enter the EventType value: ")
        query = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "term": {
                                "EventID": event_id
                            }
                        },
                        {
                            "term": {
                                "EventType": event_type
                            }
                        }
                    ]
                }
            }
        }
    elif index_choice in [3, 4]:
        # Genian 및 Fortigate의 경우, 아직 쿼리를 개발 중이므로 pass 처리
        pass

    return {
        "name": name,
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

    if index_choice in [1, 2]:
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
    elif index_choice in [3, 4]:
        print("Query development for this system is in progress. Please try again later.")
        pass

if __name__ == "__main__":
    main()
