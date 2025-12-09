import os
import logging
import discord
import json
from dotenv import load_dotenv
from discord.ext import commands


class CSBot(commands.Bot):
    """
    The main bot class
    """

    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(command_prefix="!", intents=intents)
        self.setup_logging()
        with open("config.json", "r") as f:
            self.config = json.load(f)
        self.handlers = [
            "cogs." + cog.removesuffix(".py")
            for cog in os.listdir("cogs")
            if cog.endswith(".py")
        ]

    def setup_logging(self):
        log_format = "%(levelname)s %(name)s %(asctime)s - %(message)s"
        formatter = logging.Formatter(log_format)
        normal_handler = logging.FileHandler(
            f"{self.__class__.__name__}.log", mode="a", encoding="utf-8"
        )
        normal_handler.setFormatter(formatter)
        normal_handler.setLevel(logging.WARNING)

        debug_handler = logging.FileHandler(
            f"{self.__class__.__name__}.debug.log", mode="a", encoding="utf-8"
        )
        debug_handler.setFormatter(formatter)
        debug_handler.setLevel(logging.DEBUG)

        self.log = logging.getLogger(self.__class__.__qualname__)
        self.log.setLevel(logging.DEBUG)
        self.log.propagate = False
        self.log.addHandler(normal_handler)
        self.log.addHandler(debug_handler)

    def get_member(self, id: int) -> discord.member.Member:
        """
        Given a member id, return the member object

        PARAMETERS
        ----------
        id : int
            The id of the member to return

        RETURNS
        -------
        discord.member.Member
            The member object
        """
        member = None
        for m in self.get_all_members():
            if m.id == id:
                member = m
                break

        return member

    async def setup_hook(self) -> None:
        """
        Setup the extension for the bot
        Sync without specifying a guild to get all guilds
        this might take a while!
        """
        try:
            for handler in self.handlers:
                await self.load_extension(handler)
        except Exception as e:
            self.log.error("Error loading %s: %s", handler, e)
        await self.tree.sync(guild=discord.Object(id=int(self.config["server_ID"])))

    async def on_ready(self):
        self.setup_logging()
        for channel in self.get_all_channels():
            if channel.name == self.config["broadcast_channel"]:
                self.broadcast_channel = channel

    def is_member(self, id: int):
        """
        Check if the id is a member of the server
        """
        if id:
            if self.broadcast_channel.permissions_for(id).administrator:
                return True
            elif self.broadcast_channel.permissions_for(id).manage_roles:
                return True
        return False

    async def unload_all(self):
        """
        Unload all cogs
        """
        for c in self.handlers:
            await self.unload_extension(c)


if __name__ == "__main__":
    load_dotenv(os.getenv("ENV_FILE"))
    client = CSBot()
    client.run(os.getenv("DISCORD_TOKEN"))
