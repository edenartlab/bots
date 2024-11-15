import logging
import re
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from typing import List
from typing import Optional

import discord
from discord.ext import commands

from common.constants import COMMAND_NOT_FOUND_MESSAGE
from common.models import SourceSettings


def is_mentioned(message: discord.Message, user: discord.User) -> bool:
    """
    Checks if a user is mentioned in a message.
    :param message: The message to check.
    :param user: The user to check.
    :return: True if the user is mentioned, False otherwise.
    """
    bot_name = message.guild.me.name
    # name_mentioned = bot_name.lower() in message.content.lower()
    name_mentioned = re.search(rf"\b{re.escape(bot_name.lower())}\b", message.content.lower()) is not None
    return name_mentioned or user.id in [m.id for m in message.mentions]


def role_is_mentioned(message: discord.Message, role_name: str) -> bool:
    return role_name in [r.name for r in message.role_mentions]


async def process_mention_as_command(
    ctx: str,
    cog: commands.Cog,
    command_not_found_response: str = COMMAND_NOT_FOUND_MESSAGE,
):
    try:
        split_message = ctx.message.content.split(" ")
        message_text, args = split_message[1], split_message[2:]
        cmd = getattr(cog, message_text)
        await cmd(ctx, *args)
    except Exception as e:
        logging.error(e)
        await ctx.message.channel.send(command_not_found_response)


async def get_discord_messages(
    channel: discord.TextChannel,
    limit: int,
    after: Optional[timedelta] = None,
) -> list:
    """
    Gets the last x messages from a channel.
    :param channel: The channel to get the messages from.
    :param limit: The number of messages to get.
    :return: The last x messages from the channel.
    """
    if after is not None:
        time = datetime.now(timezone.utc) - after
    else:
        time = None

    raw_messages = await channel.history(
        limit=limit,
        oldest_first=False,
        after=time,
    ).flatten()

    raw_messages.reverse()

    return raw_messages


def replace_bot_mention(
    message_text: str,
    only_first: bool = True,
    replacement_str: str = "",
) -> str:
    """
    Removes all mentions from a message.
    :param message: The message to remove mentions from.
    :return: The message with all mentions removed.
    """
    if only_first:
        return re.sub(r"<@\d+>", replacement_str, message_text, 1)
    else:
        return re.sub(r"<@\d+>", replacement_str, message_text)


def remove_role_mentions(message_text: str) -> str:
    """
    Removes all role mentions from a message.
    :param message_text: The message to remove role mentions from.
    :return: The message with all role mentions removed.
    """
    return re.sub(r"<@&\d+>", "", message_text)


async def get_reply_chain(
    ctx,
    message: discord.Message,
    depth: int,
) -> List[discord.Message]:
    messages = []
    count = 0
    while message and message.reference and count < depth:
        message = await ctx.fetch_message(message.reference.message_id)
        messages.append(message)
        count += 1
    messages.reverse()
    return messages


def replace_mentions_with_usernames(
    message_content: str,
    mentions,
    prefix: str = "",
    suffix: str = "",
) -> str:
    """
    Replaces all mentions with their usernames.
    :param message_content: The message to replace mentions in.
    :return: The message with all mentions replaced with their usernames.
    """
    for mention in mentions:
        message_content = re.sub(
            f"<@!?{mention.id}>",
            f"{prefix}{mention.display_name}{suffix}",
            message_content
        )
    return message_content.strip()


def replace_usernames_with_mentions(
    message_content: str,
    user_lookup: dict,
) -> str:
    """
    Replaces all usernames with mentions of their ID.
    :param message_content: The message to replace usernames in.
    :return: The message with all usernames replaced with their mentions.
    """
    for user in user_lookup:
        message_content = message_content.replace(user, f"<@!{user_lookup[user]}>")
    return message_content.strip()


def in_channels(channel_ids: List[int]) -> commands.check:
    async def predicate(ctx):
        if ctx.channel.id in channel_ids:
            return True
        print("command not valid in channel")

    return commands.check(predicate)


async def wait_for_user_reply(bot: commands.Bot, sender_id: int) -> discord.Message:
    """
    Waits for a user to reply to a message.
    :return: The message the user replied to.
    """

    def check(message: discord.Message) -> bool:
        return sender_id == message.author.id

    return await bot.wait_for("message", check=check)


async def update_message(
    message: discord.Message,
    content: Optional[str] = None,
    files: Optional[List[discord.File]] = None,
    clear_previous_images: bool = True,
) -> discord.Message:
    if content:
        await message.edit(content=content)
    if files:
        if clear_previous_images:
            await message.edit(files=files, attachments=[])
        else:
            await message.edit(files=files)


def filter_application_command_messages(
    messages: List[discord.Message],
) -> List[discord.Message]:
    return [m for m in messages if m.type != discord.MessageType.application_command]


def get_channel_id_by_channel_name(channel_name: str, ctx) -> int:
    try:
        channel = next(
            filter(lambda x: x.name == channel_name, ctx.guild.text_channels),
        )
        return channel.id
    except StopIteration:
        raise Exception("No text channel found matching the given name.")


def get_nick(member):
    if hasattr(member, "nick") and member.nick is not None:
        return member.nick
    else:
        return member.name


def remove_empty_lines(response):
    response = re.sub(r"[\n]+", "\\n", response)
    return response


def include_preface(response, settings):
    if settings.preface:
        response = settings.preface + response
    return response


def get_source(ctx):
    source = SourceSettings(
        author_id=int(ctx.author.id),
        author_name=str(ctx.author),
        guild_id=int(ctx.guild.id),
        guild_name=str(ctx.guild),
        channel_id=int(ctx.channel.id),
        channel_name=str(ctx.channel),
    )
    return source
