import requests


def request_logos_assistant(api_url: str, assistant: dict, interaction: dict):
    response = requests.post(
        f"{api_url}/interact",
        json={
            "assistant": assistant,
            "interaction": interaction,
        },
    )
    print(response.json())

    return response.json()
