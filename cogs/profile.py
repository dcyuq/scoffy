import discord
from discord.ext import commands
from discord import app_commands
import aiohttp

import embeds  # Importing your custom embeds module

class BotProfile(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def is_owner(self, interaction: discord.Interaction) -> bool:
        return await self.bot.is_owner(interaction.user)

    @app_commands.command(name="setavatar", description="Changes the bot's profile picture using an image URL.")
    @app_commands.describe(url="The direct URL to the image (.png or .jpg)")
    async def setavatar(self, interaction: discord.Interaction, url: str):
        # Enforce owner-only execution
        if not await self.is_owner(interaction):
            return await interaction.response.send_message(
                embed=embeds.error("Only the bot owner can use this command.", title="Permission Denied"), 
                ephemeral=True
            )

        # Defer the response since downloading the image might take >3 seconds
        await interaction.response.defer(ephemeral=True)

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        return await interaction.followup.send(
                            embed=embeds.error("Failed to download the image. Check the URL.", title="Download Failed")
                        )
                    
                    image_data = await response.read()
                    
            await self.bot.user.edit(avatar=image_data)
            await interaction.followup.send(
                embed=embeds.notice("Avatar updated successfully.", title="Avatar Updated")
            )
            
        except discord.HTTPException:
            await interaction.followup.send(
                embed=embeds.error("Discord blocked the request. You might be rate-limited (2 changes per hour).", title="Rate Limited")
            )
        except Exception as e:
            await interaction.followup.send(
                embed=embeds.error(f"An error occurred: {e}", title="Error")
            )

    @app_commands.command(name="setstatus", description="Changes the bot's status.")
    @app_commands.describe(
        activity_type="The type of activity to display",
        status_message="The custom message to display next to the activity"
    )
    @app_commands.choices(activity_type=[
        app_commands.Choice(name="Playing", value="playing"),
        app_commands.Choice(name="Watching", value="watching"),
        app_commands.Choice(name="Listening", value="listening"),
    ])
    async def setstatus(self, interaction: discord.Interaction, activity_type: app_commands.Choice[str], status_message: str):
        if not await self.is_owner(interaction):
            return await interaction.response.send_message(
                embed=embeds.error("Only the bot owner can use this command.", title="Permission Denied"), 
                ephemeral=True
            )

        activity_val = activity_type.value
        
        if activity_val == "playing":
            activity = discord.Game(name=status_message)
        elif activity_val == "watching":
            activity = discord.Activity(type=discord.ActivityType.watching, name=status_message)
        elif activity_val == "listening":
            activity = discord.Activity(type=discord.ActivityType.listening, name=status_message)

        await self.bot.change_presence(activity=activity)
        
        await interaction.response.send_message(
            embed=embeds.notice(f"Status updated to: **{activity_type.name} {status_message}**", title="Status Updated"), 
            ephemeral=True
        )

    @app_commands.command(name="setusername", description="Changes the bot's global username.")
    @app_commands.describe(new_name="The new username for the bot")
    async def setusername(self, interaction: discord.Interaction, new_name: str):
        if not await self.is_owner(interaction):
            return await interaction.response.send_message(
                embed=embeds.error("Only the bot owner can use this command.", title="Permission Denied"), 
                ephemeral=True
            )

        # Defer because API calls to edit the bot user can sometimes lag
        await interaction.response.defer(ephemeral=True)

        try:
            await self.bot.user.edit(username=new_name)
            await interaction.followup.send(
                embed=embeds.notice(f"Username successfully changed to **{new_name}**.", title="Username Updated")
            )
            
        except discord.HTTPException as e:
            # Discord limits username changes to twice per hour
            await interaction.followup.send(
                embed=embeds.error(f"Discord blocked the request. You might be rate-limited (2 changes per hour).\nError: {e}", title="Update Failed")
            )
        except Exception as e:
            await interaction.followup.send(
                embed=embeds.error(f"An error occurred: {e}", title="Error")
            )


async def setup(bot):
    await bot.add_cog(BotProfile(bot))