import logging

import discord
from discord.ext import commands

from config import TRANSFER_TAX
from messages.economy import *
from objects.economy.account import EconomyAccount


class Economy(commands.Cog):
    def  __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["$",])
    async def gil(self, ctx, target: discord.Member=None):
        """Returns current account's balance."""
        if target is None:
            target = ctx.author
        # Get current economy account
        account = EconomyAccount.get_economy_account(target, self.bot.db_session)
        await ctx.send(CMD_GIL.format(target, account.get_balance()))

    @commands.command()
    @commands.is_owner()
    async def admingive(self, ctx, amount: float, target: discord.Member=None):
        if amount < 0:
            await ctx.send(CMD_GIVE_INVALID_AMOUNT)
            return
        if target is None:
            target = ctx.author
        target_account = EconomyAccount.get_economy_account(target, self.bot.db_session)
        target_account.add_credit(self.bot.db_session, amount, "Admin grant.")
        await ctx.send(CMD_ADMIN_GIVE.format(target, amount))

    @commands.command()
    @commands.is_owner()
    async def admintake(self, ctx, amount: float, target: discord.Member=None):
        if amount < 0:
            await ctx.send(CMD_GIVE_INVALID_AMOUNT)
            return
        if target is None:
            target = ctx.author
        target_account = EconomyAccount.get_economy_account(target, self.bot.db_session)
        target_account.add_debit(self.bot.db_session, amount, "Admin grant.")
        await ctx.send(CMD_ADMIN_TAKE.format(target, amount))

    @commands.command()
    @commands.is_owner()
    async def reconsolidateall(self, ctx, target: discord.Member=None):
        if target is None:
            all_accounts = EconomyAccount.get_all_economy_accounts(self.bot.db_session)
            inconsistent_accounts = 0
            for account in all_accounts:
                # We disable committing here to optimize SQL query execution time
                result = account.reconsolidate_balance(self.bot.db_session, commit_on_execution=False)
                if not result:
                    inconsistent_accounts += 1
            self.bot.db_session.commit()
            await ctx.send(CMD_RECONSOLIDATE_MASS.format(len(all_accounts), inconsistent_accounts))
        else:
            target_account = EconomyAccount.get_economy_account(target, self.bot.db_session)
            result = target_account.reconsolidate_balance(self.bot.db_session)
            if result:
                await ctx.send(CMD_RECONSOLIDATE_TRUE.format(target))
            else:
                await ctx.send(CMD_RECONSOLIDATE_FALSE.format(target))

    @commands.command()
    async def give(self, ctx, amount: float, target: discord.Member):
        if amount < 0:
            await ctx.send(CMD_GIVE_INVALID_AMOUNT)
            return
        credit = amount * (1 - TRANSFER_TAX)
        debit = amount

        target_account = EconomyAccount.get_economy_account(target, self.bot.db_session)
        author_account = EconomyAccount.get_economy_account(ctx.author, self.bot.db_session)

        if not author_account.has_balance(debit):
            await ctx.send(
                CMD_GIVE_INSUFFICIENT_AMOUNT.format(ctx.author, target_account.get_balance())
            )
            return

        target_account.add_credit(self.bot.db_session, credit, "T:{}".format(ctx.author.id))
        author_account.add_debit(self.bot.db_session, debit, "T:{}".format(target.id))

        await ctx.send(CMD_GIVE_SUCCESS.format(target, credit, ctx.author))


def setup(bot):
    bot.add_cog(Economy(bot))

