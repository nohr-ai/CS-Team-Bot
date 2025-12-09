import os
import math
import csgo
import pickle
import discord
import constants
from pathlib import Path


class DiscordString(str):
    def __new__(self, value):
        obj = str.__new__(self, value)
        return obj

    def __add__(self, __s: str) -> str:
        return DiscordString(super().__add__(__s))

    def to_code_block(self, format_type="ml"):
        return f"```{format_type}\n{self.__str__()}```\n"

    def to_code_inline(self):
        return f"`{self.__str__()}`"


async def do_nothing(*args, **kwargs):
    return


def disable(func):
    return do_nothing


def hide(func):
    def inner(*args, **kwargs):
        return func(*args, **kwargs)

    inner.hidden = True
    return inner


def is_hidden(func):
    return getattr(func, "hidden", False)


def infinite_sequence_gen():
    num = 0
    while True:
        yield num
        num += 1


def euclidean_distance(val1, val2):
    """
    Calculates the euclidean distance between two values.
    """
    return math.sqrt((val1 - val2) ** 2)


def log_request(function):
    async def inner(self, message):
        if isinstance(message, discord.RawReactionActionEvent):
            self.log.info(f"{message.user_id} calling: {function.__name__}")
        elif isinstance(message, discord.Message):
            self.log.info(f"{message.author} calling: {function.__name__}")
            self.log.debug(f"Message content: {message.content}")
        await function(self, message)
        self.log.debug("OK")

    return inner


def persist_state(function):
    async def persist_state(self, *args, **kwargs):
        await function(self, *args, **kwargs)
        with open(f"{Path.home()}/.csbot/state", "wb") as f:
            pickle.dump(self.players, f)

    return persist_state


def load_state(function):
    def load_state(self, *args, **kwargs):
        function(self, *args, **kwargs)
        try:
            with open(f"{Path.home()}/.csbot/state", "rb") as f:
                self.players = pickle.load(f)
        except FileNotFoundError:
            self.players = {}

    return load_state
