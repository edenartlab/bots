import requests


def logos_think(api_url: str, request: dict):
    response = requests.post(
        f"{api_url}/chat/think",
        json=request,
    )
    return response.json()


def logos_speak(api_url: str, request: dict):
    response = requests.post(
        f"{api_url}/chat/speak",
        json=request,
    )
    return response.json()
