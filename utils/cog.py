import inspect
import asyncio
import os

from discord.ext import commands

from utils.info import get_module_info  # pylint: disable=import-error


class ExtendedCog(commands.Cog):
    """extension of discord.ext.commands.Cog that has some pre-built features, mainly the ability to access module info"""

    DEFAULT_CMD_CD_SECONDS = 3
    DEFAULT_CMD_CD_TYPE = "user"

    def __init__(self, bot, cog_path=None, hidden=False):
        self.bot = bot

        curframe = inspect.currentframe()
        calframe = inspect.getouterframes(curframe, 2)
        self.cog_path = cog_path or os.path.dirname(calframe[1][1])

        self.hidden = hidden  # hidden cogs will not show up in list of cog modules, and won't show up when requested in help commands
        self._module_info = {}

    @commands.Cog.listener(name="on_ready")
    async def set_cooldowns(self):
        cooldowned_commands = []
        for _command in self.get_commands():
            command = self.bot.remove_command(_command.name)
            cooldown_info = self.module_info["commands"][command.name].get(
                "cooldown",
                {
                    "seconds": ExtendedCog.DEFAULT_CMD_CD_SECONDS,
                    "type": ExtendedCog.DEFAULT_CMD_CD_TYPE,
                },
            )

            self.bot.add_command(
                commands.cooldown(
                    1,
                    cooldown_info.get("seconds", ExtendedCog.DEFAULT_CMD_CD_SECONDS),
                    getattr(
                        commands.BucketType,
                        cooldown_info.get("type", ExtendedCog.DEFAULT_CMD_CD_TYPE),
                    ),
                )(command)
            )

        # for command in cooldowned_commands:
        #     self.bot.add_command(command)

        self.__cog_commands__ = cooldowned_commands

    @property
    def module_info(self):
        """fetches the entire info.json for this cog"""
        self._module_info = get_module_info(cog_dir_path=self.cog_path)
        return self._module_info

    @property
    def commands_info(self):
        """get commands from module_info"""
        return self.module_info["commands"]

    @property
    def command_info(self):
        """get command info from this cog based on the caller"""
        curframe = inspect.currentframe()
        calframe = inspect.getouterframes(curframe, 2)
        command = calframe[1][3]

        try:
            return self.module_info["commands"][command]
        except KeyError:
            return None
