import io
import os

import aiohttp
import discord
import requests

from common.models import SourceSettings
from common.models import SignInCredentials


async def request_creation(
    api_url: str, credentials: SignInCredentials, source: SourceSettings, config
):
    generator_name = config.generator_name
    config_dict = config.__dict__
    config_dict.pop("generator_name", None)

    header = {
        "x-api-key": credentials.apiKey,
        "x-api-secret": credentials.apiSecret,
    }

    attributes = await build_eden_task_attributes(api_url, source.author_id)
    print("attributes", attributes)

    request = {
        "generatorName": generator_name,
        "config": config_dict,
        "attributes": attributes,
    }

    response = requests.post(
        f"{api_url}/admin/tasks/create", json=request, headers=header
    )

    print("config")
    print(config_dict)

    check, error = await check_server_result_ok(response)

    if not check:
        raise Exception(error)

    result = response.json()
    task_id = result["taskId"]

    return task_id


async def poll_creation_queue(
    api_url: str,
    credentials: SignInCredentials,
    task_id: str,
    is_video_request: bool = False,
    prefer_gif: bool = True,
):
    header = {
        "x-api-key": credentials.apiKey,
        "x-api-secret": credentials.apiSecret,
    }

    response = requests.get(f"{api_url}/tasks/{task_id}", headers=header)

    check, error = await check_server_result_ok(response)
    if not check:
        raise Exception(error)

    result = response.json()
    if not result:
        message_update = "_Server error: task ID not found_"
        raise Exception(message_update)

    task = result["task"]

    file, file_url = await get_file_update(task, is_video_request, prefer_gif)

    return task, file, file_url


async def get_file_update(result, is_video_request=False, prefer_gif=True):
    status = result["status"]
    file = None
    output = None
    if status == "completed" and is_video_request:
        output = result["creation"]["uri"]
        file = await get_video_clip_file(output, gif=prefer_gif)
    elif status == "completed":
        output = result["creation"]["uri"]
        file = await get_discord_file_from_url(output, "output.jpg")
    elif result["intermediateOutputs"]:
        output = result["intermediateOutputs"][-1]["files"][0]
        file = await get_discord_file_from_url(output, "output.jpg")
    else:
        pass
    return file, output


async def get_discord_file_from_url(url, filename):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status != 200:
                return None
            data = io.BytesIO(await resp.read())
            discord_file = discord.File(data, filename)
            return discord_file


async def get_video_clip_file(output_url, gif):
    output_name = output_url.split("/")[-1]
    if not output_name.endswith(".mp4"):
        output_name += ".mp4"
    output_gif = output_name.replace(".mp4", ".gif")

    # get_discord_file_from_url is giving a blank mp4 for some reason, so fall back to writing to disk
    res = requests.get(output_url)
    with open(output_name, "wb") as f:
        f.write(res.content)
    if gif:
        os.system(f"ffmpeg -i {output_name} {output_gif}")
        file_update = discord.File(output_gif, output_gif)
    else:
        file_update = discord.File(output_name, output_name)

    delete_file(output_name)
    delete_file(output_gif)

    return file_update


async def check_server_result_ok(result):
    if result.status_code != 200:
        error_message = result.content.decode("utf-8")
        error = f"_Server error: {error_message}_"
        return False, error
    return result.status_code == 200, None


def delete_file(path):
    if os.path.isfile(path):
        os.remove(path)


async def get_eden_user(api_url: str, discord_user_id: str):
    response = requests.get(
        f"{api_url}/creators", params={"discordId": discord_user_id}
    )
    if response.status_code != 200:
        return None
    docs = response.json().get("docs")
    if not docs:
        return None
    return docs[0]["_id"]


async def build_eden_task_attributes(api_url: str, discord_user_id: str):
    eden_user = await get_eden_user(api_url, discord_user_id)
    attributes = {
        "discordId": str(discord_user_id),
        "delegateUserId": eden_user,
    }
    return attributes
