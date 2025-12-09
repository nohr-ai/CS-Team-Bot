import discord
from datetime import datetime, timedelta
from discord import app_commands
from discord.ext import commands
from helperfunctions import DiscordString, load_state
from csgo import get_active_duty
from team import roll_teams
from mapdict import MapDict


class Match:
    def __init__(self, date, team) -> None:
        self.date = date
        self.team = team
        self.status = "active"

    def set_active(self):
        self.status = "active"

    def set_passive(self):
        self.status = "inactive"


class MatchHandler(commands.Cog):
    @load_state
    def __init__(self, bot) -> None:
        self.bot = bot
        self.players = {}
        self.participating_players = {}
        self.playday = "Wednesday"
        self.weekdays = {
            "Monday": 0,
            "Tuesday": 1,
            "Wednesday": 2,
            "Thursday": 3,
            "Friday": 4,
            "Saturday": 5,
            "Sunday": 6,
        }
        self.set_next_playdate()
        self.banned_maps = []
        self.picked_maps = []
        self.shared_banorder = []
        self.available_maps = get_active_duty()
        self.registration_message = None
        self.banorder_msg = None
        self.status = "ready"
        self.veto = "inactive"

    async def reset_state(self):
        self.veto = "inactive"
        self.teams = None
        self.banned_maps = []
        self.picked_maps = []
        self.available_maps = get_active_duty()
        self.status = "ready"
        self.participating_players = {}
        if self.registration_message:
            try:
                await self.registration_message.delete()
            except discord.errors.HTTPException as he:
                self.bot.log.warning(he)
            finally:
                self.registration_message = None
        if self.banorder_msg:
            try:
                await self.banorder_msg.delete()
            except discord.errors.HTTPException as he:
                self.bot.log.warning(he)
            finally:
                self.banorder_msg = None

    @app_commands.command(
        name="start_registration_match",
        description="Send a message to start the registration process for a new match day.",
    )
    async def start_registration(
        self, interaction: discord.Interaction, number_of_matches: int = 2
    ):
        if not self.bot.is_member(interaction.user):
            return
        load_state(self)
        await self.reset_state()
        self.number_of_matches = int(number_of_matches)
        await interaction.response.send_message(
            f"<@&{self.bot.config['team_role_ID']}> Please react to this message to sign up for the [{number_of_matches}] matches on {self.date.strftime('%A %d.%m.%Y at %H:%M')}. We roll teams at {(self.date-timedelta(hours=0, minutes=30)).strftime('%H:%M')}"
        )
        self.registration_message = await interaction.original_response()
        await self.registration_message.add_reaction("✅")
        self.status = "open"

    @app_commands.command(
        name="set_playday",
        description="Set the playday for the next match.",
    )
    async def playday(self, interaction: discord.Interaction, day: str):
        if not self.bot.is_member(interaction.user):
            return
        await interaction.response.send_message(f"Playday set to {day}")
        self.playday = day
        self.set_next_playdate()

    @playday.autocomplete("day")
    async def playday_autocomplete(
        self, interaction: discord.Interaction, day: str
    ) -> list[app_commands.Choice[str]]:
        return [
            app_commands.Choice(name=day, value=day) for day in self.weekdays.keys()
        ]

    @app_commands.command(
        name="set_playtime",
        description="Set the playtime for the next match.",
    )
    async def playtime(self, interaction: discord.Interaction, hour: int, minute: int):
        if not self.bot.is_member(interaction.user):
            return
        self.date = self.date.replace(hour=hour, minute=minute)
        await interaction.response.send_message(
            f"Playtime set to {self.date.strftime('%H:%M')}"
        )

    @playtime.autocomplete("hour")
    async def playtime_hour_autocomplete(
        self, interaction: discord.Interaction, hour: str
    ) -> list[app_commands.Choice[str]]:
        return [app_commands.Choice(name=str(i), value=str(i)) for i in range(0, 24)]

    @playtime.autocomplete("minute")
    async def playtime_minute_autocomplete(
        self, interaction: discord.Interaction, minute: str
    ) -> list[app_commands.Choice[str]]:
        return [app_commands.Choice(name=str(i), value=str(i)) for i in range(0, 60, 5)]

    def set_next_playdate(self):
        days_in_week = len(self.weekdays.keys())
        today = datetime.today()
        days_to = self.weekdays[self.playday] - datetime.weekday(today)
        if days_to < 0:  # we are past playday this week
            days_to += days_in_week
        self.date = today + timedelta(days_to)

    @app_commands.command(
        name="next_match",
        description="Get the date and time for the next match.",
    )
    async def next_match(self, interaction: discord.Interaction):
        if not self.bot.is_member(interaction.user):
            return
        await interaction.response.send_message(
            f"The next match is on {self.date.strftime('%A %d/%m/%Y at %H:%M')}"
        )

    def add_player(self, player):
        self.participating_players[player.id] = self.players[player.id]

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, reaction: discord.RawReactionActionEvent):
        if reaction.member.id == self.bot.user.id:
            return
        if (
            not self.registration_message
            or reaction.message_id != self.registration_message.id
        ):
            return
        self.bot.log.debug(
            f"{__class__.__qualname__} Raw reaction add from {reaction.user_id}"
        )
        reaction.member = self.bot.get_member(reaction.user_id)
        if not reaction.member:
            return
        self.add_player(reaction.member)

    def remove_player(self, player):
        try:
            del self.participating_players[player.id]
        except KeyError:
            pass

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, reaction: discord.RawReactionActionEvent):
        if reaction.user_id == self.bot.user.id:
            return
        if (
            not self.registration_message
            or reaction.message_id != self.registration_message.id
        ):
            return
        self.bot.log.debug(f"Raw reaction remove from: {reaction.user_id}")
        reaction.member = self.bot.get_member(reaction.user_id)
        if not reaction.member:
            return
        self.remove_player(reaction.member)

    @app_commands.command(
        name="end_registration_match",
        description="End the registration for the upcoming match.",
    )
    async def close_registration(self, interaction: discord.Interaction):
        if not self.bot.is_member(interaction.user):
            return
        match self.status:
            case "open":
                self.status = "closed"
                self.teams = roll_teams(
                    self.participating_players, self.number_of_matches
                )
                self.matches = [Match(self.date, team) for team in self.teams]
                msg = "Registration closed."
                msg += self.get_teamlist()
                msg += self.banorder()
                await interaction.response.send_message(msg)
                self.banorder_msg = await interaction.original_response()
            case _:
                await interaction.response.send_message(f"No open registration.")

    @app_commands.command(
        name="cancel_registration_match",
        description="Cancel the registration for the upcoming match.",
    )
    async def cancel_registration(self, interaction: discord.Interaction):
        if not self.bot.is_member(interaction.user):
            return
        match self.status:
            case "open":
                await self.reset_state()
        await interaction.response.send_message(f"Registration cancelled.")

    def get_teamlist(self) -> str:
        teams = DiscordString("")
        for i, team in self.teams.items():
            teams += team.get_info()
        teams = teams.to_code_block("arm")
        return teams

    def teams_private_banorder_copy(self):
        preferences = MapDict()
        for teamID, team in self.teams.items():
            prefs = team.map_preference.copy()
            preferences[teamID] = prefs

        return preferences

    def shared_weighted_preference(self, private_preferences):
        shared_preference = MapDict()
        for map in get_active_duty():
            shared_preference[map] = 0
            for preference in private_preferences.values():
                shared_preference[map] += preference[map]

        return shared_preference

    def get_shared_banorder(self):
        private_banorders = self.teams_private_banorder_copy()
        for banorder in private_banorders.values():
            banorder.remove_banned_maps(self.banned_maps)
            banorder.remove_picked_maps(self.picked_maps)
            banorder.amplify_most_wanted()

        shared_banorder = self.shared_weighted_preference(
            private_banorders
        ).to_list_sorted()

        return shared_banorder

    def team_to_map_fit(self):
        scores = {}
        for map in self.picked_maps:
            scores[map] = {}
            for id, team in self.teams.items():
                scores[map][id] = 0
                for player in team.players:
                    scores[map][id] += player.maps[map]
                try:
                    scores[map][id] /= len(team.players)
                except ZeroDivisionError:
                    pass
        for map in self.available_maps:
            scores[map] = {}
            for id, team in self.teams.items():
                scores[map][id] = 0
                for player in team.players:
                    scores[map][id] += player.maps[map]
                try:
                    scores[map][id] /= len(team.players)
                except ZeroDivisionError:
                    pass
        pprint = ""
        for map, teams in scores.items():
            pprint += f"{map}: "
            for team, score in teams.items():
                pprint += f"Team{team}[{score}] "
            pprint += "\n"
        return pprint

    def _get_banorder_info(self) -> dict:
        """
        Returns  dictionary with formatting:
        'private_banorders': dict{teamID<int> : Banorder<DiscordString>),..} empty or more messages with teamID and their private banorder
        'shared_banorder': <DiscordString> empty or one message with shared banorder for  all teams in  current  veto
        'banned_maps': <DiscordString> empty or one  message with currently banned maps  in this veto
        'picked_maps': <DiscordString> empty or one  message with currently picked   in this veto
        'team_fit':  <DiscordString> empty or one message with team score for each map picked in veto
        """
        messages = {
            "private_banorders": {},
            "shared_banorder": "",
            "banned_maps": "",
            "picket_maps": "",
        }
        for team_num, team in self.teams.items():
            messages["private_banorders"][team_num] = DiscordString(
                f"Team {team_num}: {[player.display_name for player in team.players]}\nbanorder -> {team.get_banorder()}"
            )
        self.shared_banorder = self.get_shared_banorder()
        messages["shared_banorder"] = DiscordString(f"{self.shared_banorder}")
        messages["banned_maps"] = DiscordString(f"{[map for map in self.banned_maps]}")
        messages["picked_maps"] = DiscordString(f"{[map for map in self.picked_maps]}")
        messages["team_fit"] = DiscordString(f"{self.team_to_map_fit()}")
        return messages

    def update_banmsg(self):
        msg = DiscordString("")
        msg += self.get_teamlist()
        msg += self.banorder()
        return msg

    def banorder(self) -> DiscordString:
        reply = DiscordString("")
        match self.status:
            case "open":
                raise AttributeError("open")
            case "closed":
                if not self.teams:
                    raise AttributeError("teams not rolled")
                banorder_info = self._get_banorder_info()
                reply += f"Shared banorder: {banorder_info['shared_banorder'].to_code_block('ml')}"
                reply += DiscordString(
                    f"Banned maps -> {banorder_info['banned_maps'].to_code_inline()}\n"
                )
                reply += DiscordString(
                    f"Picked maps -> {banorder_info['picked_maps'].to_code_inline()}\n"
                )
                reply += DiscordString(f"{banorder_info['team_fit'].to_code_inline()}")
            case "ready":
                raise AttributeError("ready")
            case _:
                raise NameError()
        return reply

    @app_commands.command(
        name="pick",
        description="Pick a map.",
    )
    async def pick(self, interaction: discord.Interaction, map: str):
        if not self.bot.is_member(interaction.user):
            return
        if self.banorder_msg:
            self.available_maps.remove(map)
            self.picked_maps.append(map)
            await self.banorder_msg.edit(content=self.update_banmsg())
            await interaction.response.send_message(f"Picked {map}", ephemeral=True)
        else:
            pass

    @pick.autocomplete("map")
    async def pick_autocomplete(self, interaction: discord.Interaction, map: str):
        return [app_commands.Choice(name=map, value=map) for map in self.available_maps]

    @app_commands.command(
        name="unpick",
        description="Unpick a map.",
    )
    async def unpick(self, interaction: discord.Interaction, map: str):
        if not self.bot.is_member(interaction.user):
            return
        if self.banorder_msg:
            self.picked_maps.remove(map)
            self.available_maps.append(map)
            await self.banorder_msg.edit(content=self.update_banmsg())
            await interaction.response.send_message(f"Unpicked {map}", ephemeral=True)
        else:
            pass

    @unpick.autocomplete("map")
    async def unpick_autocomplete(self, interaction: discord.Interaction, map: str):
        return [app_commands.Choice(name=map, value=map) for map in self.picked_maps]

    @app_commands.command(
        name="ban",
        description="Ban a map.",
    )
    async def ban(self, interaction: discord.Interaction, map: str):
        if not self.bot.is_member(interaction.user):
            return
        if self.banorder_msg:
            self.available_maps.remove(map)
            self.banned_maps.append(map)
            await self.banorder_msg.edit(content=self.update_banmsg())
            await interaction.response.send_message(f"Banned {map}", ephemeral=True)
        else:
            # TODO: log
            pass

    @ban.autocomplete("map")
    async def ban_autocomplete(
        self, interaction: discord.Interaction, map: str
    ) -> list[app_commands.Choice[str]]:
        return [app_commands.Choice(name=map, value=map) for map in self.available_maps]

    @app_commands.command(
        name="unban",
        description="Unban a map.",
    )
    async def unban(self, interaction: discord.Interaction, map: str):
        if not self.bot.is_member(interaction.user):
            return
        if self.banorder_msg:
            self.banned_maps.remove(map)
            self.available_maps.append(map)
            await self.banorder_msg.edit(content=self.update_banmsg())
            await interaction.response.send_message(f"Unbanned {map}", ephemeral=True)
        else:
            pass

    @unban.autocomplete("map")
    async def unban_autocomplete(self, interaction: discord.Interaction, map: str):
        return [app_commands.Choice(name=map, value=map) for map in self.banned_maps]


async def setup(bot):
    await bot.add_cog(
        MatchHandler(bot), guild=discord.Object(id=bot.config["server_ID"])
    )
