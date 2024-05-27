import requests

def get_user_input():
    # 사용자로부터 룰셋 정보를 입력받습니다.
    name = input("Enter the name of the ruleset: ")
    system = input("Enter the system (e.g., linux, windows): ")
    message_value = input("Enter the message value: ")
    programname_value = input("Enter the programname value: ")
    severity = int(input("Enter the severity (e.g., 1, 2, 3, 4): "))
    
    # 입력받은 정보를 바탕으로 query를 구성합니다.
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
    print("3. genian_rulesets")
    print("4. fortigate_rulesets")
    choice = int(input("Enter your choice (1-4): "))
    if choice not in [1, 2, 3, 4]:
        raise ValueError("Invalid choice, please select a number between 1 and 4.")
    return choice

def main():
    ruleset = get_user_input()
    index_choice = select_index()
    
    url = f"http://localhost:8888/ruleset/?index_choice={index_choice}"
    headers = {
        "Content-Type": "application/json"
    }
    
    response = requests.post(url, headers=headers, json=ruleset)
    
    if response.status_code == 200:
        print("Ruleset created successfully.")
    else:
        print(f"Failed to create ruleset. Status code: {response.status_code}")
        print("Response:", response.json())

if __name__ == "__main__":
    main()
