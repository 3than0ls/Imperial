import discord
from discord.ext import commands
from decimal import Decimal, MAX_EMAX, MIN_EMIN

from simpleeval import FunctionNotDefined, NumberTooHigh
from utils.cog import ExtendedCog  # pylint: disable=import-error
from utils.embed import EmbedFactory  # pylint: disable=import-error
from firecord import firecord  # pylint: disable=import-error
from cogs.math.helper import simple_eval  # pylint: disable=import-error
import numbers
import re


class Math(ExtendedCog):
    def __init__(self, bot):
        super().__init__(bot)
        self.seval_obj = simple_eval()
        self.seval = self.seval_obj.eval
        self.without_prefix = None

    @commands.command(require_var_positional=True)
    async def calculate(self, ctx, *args):
        raw = ctx.message.content.split(" ", 1)[1].replace("`", "")
        expression = re.sub(
            r"((?:\d+)|(?:[a-zA-Z]\w*\(\w+\)))((?:[a-zA-Z]\w*)|\()",
            r"\1*\2",
            raw.replace(" ", "").replace("\\", "").replace("x", "*"),
        )
        # turn args into a list of single characters, for cleaning/validation purposes perhaps?
        # args = list("".join(args))

        try:
            output = self.seval(expression)
            if len(str(output)) > 250:
                raise NumberTooHigh()
            print(output)
        except SyntaxError as e:
            err_info = f"```py\n{e.text}{' '*(e.offset-1)}^ Likely a missing operator or parentheses here.```"
            raise commands.BadArgument(
                self.command_info["errors"]["SyntaxError"].format(err_info=err_info)
            )
        except FunctionNotDefined as e:
            print("func not defined", e)
            print(dir(e))
            raise commands.BadArgument(
                self.command_info["errors"]["FunctionNotDefined"].format()
            )
        except KeyError as e:
            print("op not allowed/defined", e)
            print(dir(e))
            return
        except NumberTooHigh as e:
            print("too ranged", e)
            print(dir(e))
            raise commands.BadArgument(
                self.command_info["errors"]["NumberTooHigh"].format()
            )

        if output is None:
            print("error!")
            return
        elif isinstance(output, bool):
            # bools are considered numbers, so we must make this elif case before checking for numbers
            pass
        elif isinstance(output, numbers.Number):
            if MIN_EMIN < output < MAX_EMAX:
                output = Decimal(output).quantize(Decimal("1.00000")).normalize() + 0

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


def setup(bot):
    bot.add_cog(Math(bot))
