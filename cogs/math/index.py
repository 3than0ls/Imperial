import numbers
import re
from decimal import MAX_EMAX, MIN_EMIN, Decimal, DivisionByZero
from datetime import datetime
from cogs.math.helper import (  # pylint: disable=import-error
    funcs,
    simple_eval,
    symbols,
)
from cogs.settings.convert import to_client  # pylint: disable=import-error
from discord.ext import commands
from firecord import firecord  # pylint: disable=import-error
from simpleeval import FunctionNotDefined, NumberTooHigh
from utils.cog import ExtendedCog  # pylint: disable=import-error
from utils.embed import EmbedFactory  # pylint: disable=import-error


class Math(ExtendedCog):
    def __init__(self, bot):
        super().__init__(bot)
        self._seval_obj = simple_eval()
        self._seval = self._seval_obj.eval

        self.cache = self.bot.cache
        self.cd_cache = self.bot.cache["math_cd"]

    def eval(self, raw):
        expression = re.sub(
            r"((?:\d+)|(?:[a-zA-Z]\w*\(\w+\)))((?:[a-zA-Z]\w*)|\()",
            r"\1*\2",
            raw.replace(" ", "")
            .replace("`", "")
            .replace("\\", "")
            .replace("x", "*")
            .replace("^", "**"),
        )
        try:
            output = self._seval(expression)
            if len(str(output)) > 250:
                raise NumberTooHigh()
        except SyntaxError as e:
            err_info = f"```py\n{e.text}{' '*(e.offset-1)}^ Error here.```"
            raise commands.BadArgument(
                self.module_info["errors"]["SyntaxError"].format(err_info=err_info)
            )
        except FunctionNotDefined as e:
            raise commands.BadArgument(
                self.module_info["errors"]["FunctionNotDefined"].format(
                    func_name=e.func_name  # pylint: disable=no-member
                )
            )
        except NumberTooHigh:
            raise commands.BadArgument(self.module_info["errors"]["NumberTooHigh"])
        except DivisionByZero:
            raise commands.BadArgument(self.module_info["errors"]["DivisionByZero"])
        except Exception:
            raise commands.BadArgument(self.module_info["errors"]["GeneralError"])

        if output is None:
            raise commands.BadArgument(self.module_info["errors"]["GeneralError"])

        if isinstance(output, bool):
            # bools are considered numbers, so we must make this elif case before checking for numbers
            pass
        elif isinstance(output, numbers.Number):
            if MIN_EMIN < output < MAX_EMAX:
                output = Decimal(output).quantize(Decimal("1.00000")).normalize() + 0
            else:
                # this should already be handled by NumberTooHigh, but do this anyways
                raise commands.BadArgument(self.module_info["errors"]["GeneralError"])

        return expression, output

    @ExtendedCog.listener(name="on_message")
    async def on_message(self, message):
        if (
            message.author.id == self.bot.user.id
            or message.author.bot
            # or message.guild is None
        ):
            return

        # handle DMs. jsut avoid all cooldowns
        if message.guild is None:
            try:
                expression, output = self.eval(message.content)
                # get rid of common exceptions
                if (
                    expression.startswith("0")
                    or expression == "24/7"
                    or expression == "24/7/365"
                    or expression.startswith("'")
                    or expression.startswith('"')
                    or expression.startswith(
                        "..."
                    )  # this needs an actual good fix - it outputs "Ellipses" for gods sake
                ):
                    return

                if str(output) == "True" or str(output) == "False":
                    return

                if expression in funcs.keys() or expression in symbols.keys():
                    return

                try:
                    int(expression)
                    return
                except:
                    pass

                return await message.channel.send(
                    embed=EmbedFactory(
                        self.commands_info["calculate"]["embed"],
                        formatting_data={
                            "raw": message.content,
                            "author": message.author.mention,
                            "expression": expression,
                            "output": output,
                        },
                    )
                )
            except:
                return

        if "automath" not in self.cache[str(message.guild.id)]:
            self.cache[str(message.guild.id)]["automath"] = to_client.automath(
                {}, firecord.get_guild_data(str(message.guild.id))["automath"]
            )[0]

        if self.cache[str(message.guild.id)]["automath"]:
            try:
                # apply a cooldown check
                now_time = datetime.now()
                guild_id = str(message.guild.id)
                if (
                    self.cd_cache[guild_id]
                    and (now_time - self.cd_cache[guild_id]).total_seconds() < 0.2
                ):
                    return
                else:
                    self.cd_cache[guild_id] = now_time

                expression, output = self.eval(message.content)

                # get rid of common exceptions
                if (
                    expression.startswith("0")
                    or expression == "24/7"
                    or expression == "24/7/365"
                    or expression.startswith("'")
                    or expression.startswith('"')
                    or expression
                    == "..."  # this needs an actual good fix - it outputs "Ellipses" for gods sake
                ):
                    return

                if str(output) == "True" or str(output) == "False":
                    return

                if expression in funcs.keys() or expression in symbols.keys():
                    return

                try:
                    int(expression)
                    float(expression)
                    return
                except:
                    pass

                await message.channel.send(
                    embed=EmbedFactory(
                        self.commands_info["calculate"]["embed"],
                        formatting_data={
                            "raw": message.content,
                            "author": message.author.mention,
                            "expression": expression,
                            "output": output,
                        },
                    )
                )
            except Exception:
                pass

    @commands.command(aliases=["math_funcs"])
    async def math_functions(self, ctx):
        math_funcs = "**Math Functions**\nSome functions may require or accept more than one argument.\n"
        for func in funcs.values():
            math_funcs += f"`{func.__name__}`\n"

        math_funcs += "**Math Symbols**\n"
        for symbol, value in symbols.items():
            math_funcs += f"`{symbol}` = `{value}`\n"

        await ctx.send(
            embed=EmbedFactory(
                self.command_info["embed"],
                formatting_data={"math_funcs": math_funcs},
            )
        )

    @commands.command(require_var_positional=True)
    async def calculate(self, ctx, *expression):
        raw = ctx.message.content.split(" ", 1)[1]
        # it should work the same by joining args?
        expression, output = self.eval(raw)

        await ctx.send(
            embed=EmbedFactory(
                self.command_info["embed"],
                formatting_data={
                    "raw": raw,
                    "author": ctx.author.mention,
                    "expression": expression,
                    "output": output,
                },
            )
        )

    @commands.command(aliases=["bin"])
    async def binary(self, ctx, number):
        try:
            binary = format(int(number), "b")
        except ValueError:
            raise commands.BadArgument(
                self.module_info["errors"]["ConversionError"].format(
                    value=number, type="number", convert_type="binary"
                )
            )
        if len(binary) > 800:
            raise NumberTooHigh()
        await ctx.send(
            embed=EmbedFactory(
                self.command_info["embed"],
                formatting_data={"num": number, "binary_num": binary},
            )
        )

    @commands.command(aliases=["unbin"])
    async def unbinary(self, ctx, binary):
        if len(binary) > 800:
            raise NumberTooHigh()
        try:
            number = int(binary, 2)
        except ValueError:
            raise commands.BadArgument(
                self.module_info["errors"]["ConversionError"].format(
                    value=binary, type="binary", convert_type="number"
                )
            )
        await ctx.send(
            embed=EmbedFactory(
                self.command_info["embed"],
                formatting_data={"num": number, "binary_num": binary},
            )
        )

    @commands.command(aliases=["hex"])
    async def hexadecimal(self, ctx, number):
        try:
            hexadecimal = format(int(number), "x")
        except ValueError:
            raise commands.BadArgument(
                self.module_info["errors"]["ConversionError"].format(
                    value=number, type="number", convert_type="hexadecimal"
                )
            )
        if len(hexadecimal) > 800:
            raise NumberTooHigh()
        await ctx.send(
            embed=EmbedFactory(
                self.command_info["embed"],
                formatting_data={"num": number, "hex_num": hexadecimal},
            )
        )

    @commands.command(aliases=["unhex"])
    async def unhexadecimal(self, ctx, hexadecimal):
        if len(hexadecimal) > 800:
            raise NumberTooHigh()
        try:
            number = int(hexadecimal, 16)
        except ValueError:
            raise commands.BadArgument(
                self.module_info["errors"]["ConversionError"].format(
                    value=hexadecimal, type="hexadecimal", convert_type="number"
                )
            )
        await ctx.send(
            embed=EmbedFactory(
                self.command_info["embed"],
                formatting_data={"num": number, "hex_num": hexadecimal},
            )
        )


def setup(bot):
    bot.add_cog(Math(bot))
