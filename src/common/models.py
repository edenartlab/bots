from dataclasses import dataclass
from typing import List

import discord


@dataclass
class SignInCredentials:
    apiKey: str
    apiSecret: str


@dataclass
class SourceSettings:
    author_id: int
    author_name: str
    guild_id: int
    guild_name: str
    channel_id: int
    channel_name: str
    origin: str = "discord"


@dataclass
class StableDiffusionConfig:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


@dataclass
class MarsBotMetadata:
    name: str
    token_env: str
    command_prefix: str
    intents: List[str]


@dataclass
class MarsBotCommand:
    name: str
    is_listener: bool
    allowed_guilds: List[int]
    allowed_channels: List[int]
    allowed_in_dm: bool
    allowed_users: List[int]


@dataclass
class MarsBot:
    metadata: MarsBotMetadata
    commands: List[MarsBotCommand]


@dataclass
class ChatMessage:
    content: str
    sender: str
    deliniator_left: str = "**["
    deliniator_right: str = "]**:"

    def __str__(self) -> str:
        return (
            f"{self.deliniator_left}{self.sender}{self.deliniator_right} {self.content}"
        )


@dataclass
class GenerationLoopInput:
    api_url: str
    start_bot_message: str
    source: SourceSettings
    config: any
    message: discord.Message
    is_video_request: bool = False
    prefer_gif: bool = True
    refresh_interval: int = 2
    parent_message: discord.Message = None
