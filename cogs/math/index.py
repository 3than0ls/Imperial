import numbers
import re
from decimal import MAX_EMAX, MIN_EMIN, Decimal, DivisionByZero

from cogs.math.helper import funcs, simple_eval, symbols  # pylint: disable=import-error
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
        if message.author.id == self.bot.user.id or message.author.bot:
            return

        if "automath" not in self.cache[message.guild.id]:
            self.cache[message.guild.id]["automath"] = to_client.automath(
                {}, firecord.get_guild_data(message.guild.id)["automath"]
            )[0]

        if self.cache[message.guild.id]["automath"] == "Yes":
            try:
                ctx = await self.bot.get_context(message)
                expression, output = self.eval(message.content)

                # a silly emoticon-ish thing that needs to be an exception
                if expression == "0-0":
                    return

                await ctx.send(
                    embed=EmbedFactory(
                        self.command_info["commands"]["calculate"]["embed"],
                        formatting_data={
                            "raw": message.content,
                            "author": message.author.mention,
                            "expression": expression,
                            "output": output,
                        },
                    )
                )
            except:
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
