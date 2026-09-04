import asyncio
import discord
from discord.ext import commands
from database import Database

DM_DELAY = 1.2


class DMCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _log(self, guild: discord.Guild, embed: discord.Embed):
        log_id = await Database.get_log_channel(str(guild.id))
        if not log_id:
            return
        channel = guild.get_channel(int(log_id))
        if channel:
            try:
                await channel.send(embed=embed)
            except discord.HTTPException:
                pass

    async def _has_dm_perms(self, ctx: commands.Context) -> bool:
        if ctx.author.guild_permissions.administrator:
            return True
        role_id = await Database.get_perms_role(str(ctx.guild.id))
        if not role_id:
            return False
        return any(str(r.id) == str(role_id) for r in ctx.author.roles)

    async def _send_dm(self, member: discord.Member, message: str):
        try:
            await member.send(message)
            return True, None
        except discord.Forbidden:
            return False, "DMs closed / bot blocked"
        except discord.HTTPException as e:
            return False, str(e)

    async def _run_mass_dm(self, ctx: commands.Context, members: list[discord.Member], message: str, label: str):
        targets = [m for m in members if not m.bot]
        total = len(targets)
        if total == 0:
            await ctx.send("Δεν βρέθηκαν μέλη για αποστολή.")
            return

        status = await ctx.send(f"📨 Ξεκινάει αποστολή σε **{total}** μέλη ({label})... `0/{total}`")
        sent, failed = 0, 0
        failed_list = []

        for i, member in enumerate(targets, start=1):
            ok, reason = await self._send_dm(member, message)
            if ok:
                sent += 1
            else:
                failed += 1
                failed_list.append(f"{member} (`{member.id}`) — {reason}")

            if i % 15 == 0 or i == total:
                try:
                    await status.edit(content=f"📨 Αποστολή σε εξέλιξη ({label})... `{i}/{total}` ✅ {sent}  ❌ {failed}")
                except discord.HTTPException:
                    pass

            await asyncio.sleep(DM_DELAY)

        result_embed = discord.Embed(
            title=f"Αποτέλεσμα Mass DM — {label}",
            color=discord.Color.green() if failed == 0 else discord.Color.orange(),
            description=(
                f"**Σύνολο στόχων:** {total}\n"
                f"**Επιτυχή:** {sent}\n"
                f"**Αποτυχημένα:** {failed}\n"
                f"**Στάλθηκε από:** {ctx.author.mention}\n"
                f"**Μήνυμα:**\n> {message[:900]}"
            )
        )
        if failed_list:
            preview = "\n".join(failed_list[:15])
            if len(failed_list) > 15:
                preview += f"\n... και {len(failed_list) - 15} ακόμα"
            result_embed.add_field(name="Αποτυχίες", value=preview[:1024], inline=False)

        await status.edit(content=None, embed=result_embed)
        await self._log(ctx.guild, result_embed)

    @commands.command(name="permsid")
    @commands.has_permissions(administrator=True)
    async def permsid(self, ctx: commands.Context, role: discord.Role):
        await Database.set_perms_role(str(ctx.guild.id), str(role.id))
        await ctx.send(f" Το role {role.mention} μπορεί πλέον να τρέχει `!dmall` και `!dmrole`.")

    @permsid.error
    async def permsid_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("Χρειάζεσαι δικαίωμα **Administrator** για να το ορίσεις.")
        elif isinstance(error, commands.RoleNotFound):
            await ctx.send("Δεν βρέθηκε role. Χρησιμοποίησε ID ή @role.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Χρήση: `!permsid <role_id ή @role>`")

    @commands.command(name="setlogchannel")
    @commands.has_permissions(administrator=True)
    async def setlogchannel(self, ctx: commands.Context, channel: discord.TextChannel):
        await Database.set_log_channel(str(ctx.guild.id), str(channel.id))
        await ctx.send(f"Τα logs θα στέλνονται στο {channel.mention}.")

    @setlogchannel.error
    async def setlogchannel_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("Χρειάζεσαι δικαίωμα **Administrator** για να το ορίσεις.")
        elif isinstance(error, commands.ChannelNotFound):
            await ctx.send("Δεν βρέθηκε το κανάλι.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Χρήση: `!setlogchannel #κανάλι`")

    @commands.command(name="dmall")
    async def dmall(self, ctx: commands.Context, *, message: str = None):
        if not await self._has_dm_perms(ctx):
            await ctx.send("Δεν έχεις δικαίωμα για αυτή την εντολή.")
            return
        if not message:
            await ctx.send("Χρήση: `!dmall <μήνυμα>`")
            return
        await self._run_mass_dm(ctx, ctx.guild.members, message, label=f"όλα τα μέλη του {ctx.guild.name}")

    @commands.command(name="dmrole")
    async def dmrole(self, ctx: commands.Context, role: discord.Role = None, *, message: str = None):
        if not await self._has_dm_perms(ctx):
            await ctx.send("Δεν έχεις δικαίωμα για αυτή την εντολή.")
            return
        if role is None or not message:
            await ctx.send("Χρήση: `!dmrole <@role ή role_id> <μήνυμα>`")
            return
        await self._run_mass_dm(ctx, role.members, message, label=f"role {role.name}")

    @dmrole.error
    async def dmrole_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.RoleNotFound):
            await ctx.send("❌ Δεν βρέθηκε role. Χρησιμοποίησε ID ή @role.")


async def setup(bot: commands.Bot):
    await bot.add_cog(DMCog(bot))
