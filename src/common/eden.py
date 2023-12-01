import asyncio
import io
import os
from typing import Optional

import aiohttp
import discord
import requests

from common.models import GenerationLoopInput, SourceSettings
from common.models import SignInCredentials

from discord import ui, ButtonStyle


class LinkButton(ui.Button):
    def __init__(self, label, url):
        super().__init__(label=label, url=url, style=ButtonStyle.link)


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

    request = {
        "generatorName": generator_name,
        "config": config_dict,
        "attributes": attributes,
    }

    # response = requests.post(f"{api_url}/tasks/create", json=request, headers=header)
    response = requests.post(
        f"{api_url}/admin/tasks/create", json=request, headers=header
    )

    check, error = await check_server_result_ok(response)

    if not check:
        raise Exception(error)

    result = response.json()
    task_id = result["taskId"]

    return task_id


async def query_user_discord_connection(
    api_url: str, credentials: SignInCredentials, discord_user_id: str
):
    header = {
        "x-api-key": credentials.apiKey,
        "x-api-secret": credentials.apiSecret,
    }

    response = requests.get(
        f"{api_url}/creators", params={"discordId": discord_user_id}, headers=header
    )

    check, error = await check_server_result_ok(response)
    if not check:
        raise Exception(error)

    result = response.json()
    if not result:
        return False

    is_connected = result.get("docs") and len(result["docs"]) > 0

    return is_connected


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


async def generation_loop(
    loop_input: GenerationLoopInput,
    eden_credentials: SignInCredentials,
):
    api_url = loop_input.api_url
    frontend_url = loop_input.frontend_url
    start_bot_message = loop_input.start_bot_message
    parent_message = loop_input.parent_message
    message = loop_input.message
    source = loop_input.source
    config = loop_input.config
    refresh_interval = loop_input.refresh_interval
    is_video_request = loop_input.is_video_request
    prefer_gif = loop_input.prefer_gif

    try:
        task_id = await request_creation(api_url, eden_credentials, source, config)
        current_output_url = None
        while True:
            result, file, output_url = await poll_creation_queue(
                api_url,
                eden_credentials,
                task_id,
                is_video_request,
                prefer_gif,
            )
            if output_url != current_output_url:
                current_output_url = output_url
                message_update = get_message_update(result)
                await edit_message(
                    message,
                    start_bot_message,
                    message_update,
                    file_update=file,
                )
            if result["status"] == "completed":
                is_connected = await query_user_discord_connection(
                    api_url, eden_credentials, source.author_id
                )
                file, output_url = await get_file_update(
                    result, is_video_request, prefer_gif
                )
                view = ui.View()
                view.add_item(
                    LinkButton(
                        "View this on Eden",
                        f"{frontend_url}/creations/{result['creation']['_id']}",
                    )
                )

                if not is_connected:
                    view.add_item(
                        LinkButton(
                            "Link your Discord account to Eden",
                            f"{frontend_url}/tools",
                        )
                    )

                if parent_message:
                    await parent_message.reply(
                        start_bot_message,
                        files=[file],
                        view=view,
                    )
                else:
                    await message.channel.send(
                        start_bot_message,
                        files=[file],
                        view=view,
                    )
                await message.delete()
                return
            await asyncio.sleep(refresh_interval)

    except Exception as e:
        await edit_message(message, start_bot_message, f"Error: {e}")


def get_message_update(result):
    status = result["status"]
    if status == "failed":
        return "_Server error: Eden task failed_"
    elif status in "pending":
        return "_Warming up, please wait._"
    elif status in "starting":
        return "_Creation is starting_"
    elif status == "running":
        progress = int(100 * result["progress"])
        return f"_Creation is **{progress}%** complete_"
    elif status == "complete":
        return "_Creation is **100%** complete_"


async def edit_message(
    message: discord.Message,
    start_bot_message: str,
    message_update: str,
    file_update: Optional[discord.File] = None,
) -> discord.Message:
    if message_update is not None:
        message_content = f"{start_bot_message}\n{message_update}"
        await message.edit(content=message_content)
    if file_update:
        await message.edit(files=[file_update], attachments=[])
