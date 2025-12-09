import os
import discord
import asyncio
from masterblaster import MasterBlaster
from discord.ext import commands
from discord import app_commands, Embed
from datetime import timedelta
from dateutil import parser

MASTERBLASTER_URL = "https://app.masterblaster.gg/"
PUBLIC_API = "api/external/v1/"
INTERNAL_API = "api/"
TEAMS = "team/"
RESULT = "results/"
STANDING = "standings/"
MATCH = "match/"
ORGANIZAITON = "organization/"
PLAYERS = "players/"


class MasterblasterHandler(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot
        loop = asyncio.get_event_loop()
        asyncio.ensure_future(self.setup(), loop=loop)

    async def setup(self):
        self.mb = MasterBlaster(os.getenv("MB_TOKEN"))

    @app_commands.command(
        name="get_members",
        description="Get the members of an organisation",
    )
    async def get_members(self, interaction: discord.Interaction, org: str):
        await interaction.response.send_message("Getting members", ephemeral=False)
        async with self.mb:
            organisation = await self.mb.get_org_by_name(org)
            members = await organisation.get_members()
            embed = Embed(title="Members", color=0x00FF00)
            for member in members:
                embed.add_field(
                    name=member, value=member.player.nick_name, inline=False
                )
            await interaction.followup.send(embed=embed, ephemeral=True)

    @get_members.autocomplete("org")
    async def get_members_autocomplete(
        self, interaction: discord.Interaction, org: str
    ) -> list[app_commands.Choice[str]]:
        async with self.mb:
            orgs = await self.mb.get_all_orgs()
            return [app_commands.Choice(name=org.name, value=org.name) for org in orgs]

    async def next_match_autocomplete_org(
        self, interaction: discord.Interaction, org: str
    ) -> list[app_commands.Choice[str]]:
        async with self.mb:
            orgs = await self.mb.get_all_orgs()
            return [app_commands.Choice(name=org.name, value=org.name) for org in orgs]

    async def next_match_autocomplete_team(
        self, interaction: discord.Interaction, team: str
    ) -> list[app_commands.Choice[str]]:
        async with self.mb:
            org = None
            try:
                org = interaction.namespace["org"]
            except KeyError:
                return [
                    app_commands.Choice(name="No team found", value="No team found")
                ]
            org = await self.mb.get_org_by_name(org)
            teams = await org.get_teams()
            return [
                app_commands.Choice(name=team.name, value=team.name) for team in teams
            ]

    @app_commands.command(
        name="next_mb",
        description="Get info for next match",
    )
    @app_commands.autocomplete(
        org=next_match_autocomplete_org, team=next_match_autocomplete_team
    )
    async def next_match(self, interaction: discord.Interaction, org: str, team: str):
        async with self.mb:
            org = await self.mb.get_org_by_name(org)
            await asyncio.sleep(1)
            teams = await org.get_teams()
            for t in teams:
                if t.name == team:
                    schedule = await t.get_schedule()
                    next_match = schedule.get_next_match()
                    embed = Embed(title="Next Match", color=0x00FF00)
                    date = parser.isoparse(next_match.get_date_and_time())
                    date = date + timedelta(hours=2)
                    embed.add_field(
                        name="Date",
                        value=f"{date.day}.{date.month} at {date.hour}:{date.minute}",
                        inline=False,
                    )
                    embed.add_field(name="Home", value=next_match.teams[0].name)
                    embed.add_field(name="", value="vs")
                    embed.add_field(name="Visiting", value=next_match.teams[1].name)
                    await interaction.response.send_message(
                        embed=embed, ephemeral=False
                    )

    @app_commands.command(
        name="get_schedule",
        description="Get the schedule of a team",
    )
    @app_commands.autocomplete(
        org=next_match_autocomplete_org, team=next_match_autocomplete_team
    )
    async def get_schedule(self, interaction: discord.Interaction, org: str, team: str):
        async with self.mb:
            org = await self.mb.get_org_by_name(org)
            await asyncio.sleep(1)
            teams = await org.get_teams()
            for t in teams:
                if t.name == team:
                    schedule = await t.get_schedule()
                    embed = Embed(title="Schedule", color=0x00FF00)
                    for match in schedule.matches:
                        date = parser.isoparse(match.get_date_and_time())
                        date = date + timedelta(hours=2)
                        embed.add_field(
                            name=f"{date.day}.{date.month} at {date.hour}:{date.minute}",
                            value=f"{match.teams[0].name} vs {match.teams[1].name}",
                            inline=False,
                        )
                    await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    if not os.getenv("MB_TOKEN"):
        raise LookupError("No Masterblaster token found")
    await bot.add_cog(
        MasterblasterHandler(bot), guild=discord.Object(id=bot.config["server_ID"])
    )
