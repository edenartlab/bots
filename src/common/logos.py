import requests


def request_logos_assistant(api_url: str, assistant: dict, interaction: dict):
    
    print("----")
    print(assistant)
    print(interaction)
    print(api_url)
    print("----")
    print("--> 1")
    print("GET KEYS")
    print(assistant.keys())
    print(interaction.keys())
    print("--> 2")
    response = requests.post(
        f"{api_url}/interact",
        json={
            "assistant": assistant,
            "interaction": interaction,
        },
    )
    print("--> 3")
    print(response.json())

    return response.json()
