import discord
from discord import app_commands
from bot_setup import bot, tree
from helpers import (get_guild_servers, get_single_guild_server, rcon_command, 
                    is_admin, add_server, add_player, remove_player)

# --- Helper functions for server management ---

@tree.command(name="add_server", description="Admin-only: Add a new Minecraft server")
@app_commands.describe(
    server_key="Unique key for this server",
    host="Server IP or hostname",
    port="RCON port (usually 25575)",
    password="RCON password"
)
async def add_server_command(interaction: discord.Interaction, server_key: str, host: str, port: int, password: str):
    print(f"add_server called with: {server_key}, {host}, {port}, {password}")
    if not is_admin(interaction.user):
        await interaction.response.send_message("❌ You don't have permission to use this.", ephemeral=True)
        return

    guild_id = interaction.guild_id
    
    # Use the helper function to add the server
    add_server(server_key, host, port, password, guild_id)
    
    await interaction.response.send_message(f"✅ Server '{server_key}' added successfully.", ephemeral=True)


# --- Public Commands ---

@tree.command(name="list_servers", description="List available Minecraft servers")
async def list_servers(interaction: discord.Interaction):
    print("list_servers called")
    guild_id = interaction.guild_id
    guild_servers = get_guild_servers(guild_id)

    if not guild_servers:
        await interaction.response.send_message("No servers are configured for this Discord server.", ephemeral=True)
        return

    server_list = "\n".join([f"- {key}" for key in guild_servers.keys()])
    await interaction.response.send_message(f"Available servers:\n{server_list}", ephemeral=True)


@tree.command(name="say", description="Broadcast a message")
@app_commands.describe(server="Server key from servers.json (optional if only one server)", message="Message to broadcast")
async def say(interaction: discord.Interaction, message: str, server: str = None):
    print(f"say called with: {message}, {server}")
    guild_id = interaction.guild_id
    guild_servers = get_guild_servers(guild_id)

    if not guild_servers:
        await interaction.response.send_message("No servers are configured for this Discord server.", ephemeral=True)
        return

    if server is None:
        server = get_single_guild_server(guild_id)
        if server is None:
            await interaction.response.send_message("Multiple servers are available. Please specify the server.", ephemeral=True)
            return

    if server not in guild_servers:
        await interaction.response.send_message(f"❌ Server '{server}' is not available in this Discord server.", ephemeral=True)
        return

    result = rcon_command(server, f"say {message}")
    await interaction.response.send_message(f"[{server}] {result}")


@tree.command(name="weather", description="Set weather (clear, rain, thunder)")
@app_commands.describe(server="Server key (optional if only one server)", type="Weather type: clear, rain, or thunder")
async def weather(interaction: discord.Interaction, type: str, server: str = None):
    print(f"weather called with: {type}, {server}")
    guild_id = interaction.guild_id
    guild_servers = get_guild_servers(guild_id)

    if not guild_servers:
        await interaction.response.send_message("No servers are configured for this Discord server.", ephemeral=True)
        return

    if server is None:
        server = get_single_guild_server(guild_id)
        if server is None:
            await interaction.response.send_message("Multiple servers are available. Please specify the server.", ephemeral=True)
            return

    if server not in guild_servers:
        await interaction.response.send_message(f"❌ Server '{server}' is not available in this Discord server.", ephemeral=True)
        return

    if type.lower() not in ["clear", "rain", "thunder"]:
        await interaction.response.send_message("Invalid weather type. Choose: clear, rain, or thunder.")
        return

    result = rcon_command(server, f"weather {type.lower()}")
    await interaction.response.send_message(f"[{server}] {result}")


# Whitelist command group
whitelist_group = app_commands.Group(name="whitelist", description="Manage the server whitelist")

@whitelist_group.command(name="add", description="Add a player to the server whitelist")
@app_commands.describe(
    minecraft_username="Minecraft username to whitelist",
    server="Server key (optional if only one server)"
)
async def whitelist_add(interaction: discord.Interaction, minecraft_username: str, server: str = None):
    print(f"whitelist add called with: {minecraft_username}, {server}")
    guild_id = interaction.guild_id
    guild_servers = get_guild_servers(guild_id)

    if not guild_servers:
        await interaction.response.send_message("No servers are configured for this Discord server.", ephemeral=True)
        return

    if server is None:
        server = get_single_guild_server(guild_id)
        if server is None:
            await interaction.response.send_message("Multiple servers are available. Please specify the server.", ephemeral=True)
            return

    if server not in guild_servers:
        await interaction.response.send_message(f"❌ Server '{server}' is not available in this Discord server.", ephemeral=True)
        return

    discord_user_id = interaction.user.id
    result = add_player(server, minecraft_username, discord_user_id)
    await interaction.response.send_message(f"[{server}] {result}")

@whitelist_group.command(name="remove", description="Remove a player from the server whitelist")
@app_commands.describe(
    minecraft_username="Minecraft username to remove",
    server="Server key (optional if only one server)"
)
async def whitelist_remove(interaction: discord.Interaction, minecraft_username: str, server: str = None):
    print(f"whitelist remove called with: {minecraft_username}, {server}")
    guild_id = interaction.guild_id
    guild_servers = get_guild_servers(guild_id)

    if not guild_servers:
        await interaction.response.send_message("No servers are configured for this Discord server.", ephemeral=True)
        return

    if server is None:
        server = get_single_guild_server(guild_id)
        if server is None:
            await interaction.response.send_message("Multiple servers are available. Please specify the server.", ephemeral=True)
            return

    if server not in guild_servers:
        await interaction.response.send_message(f"❌ Server '{server}' is not available in this Discord server.", ephemeral=True)
        return

    discord_user_id = interaction.user.id
    user_is_admin = is_admin(interaction.user)
    result, success = remove_player(server, minecraft_username, discord_user_id, user_is_admin)
    
    if success:
        await interaction.response.send_message(f"[{server}] {result}")
    else:
        await interaction.response.send_message(f"❌ {result}", ephemeral=True)

# Add the whitelist command group to the bot
tree.add_command(whitelist_group)


# --- Admin-only Commands ---

@tree.command(name="custom", description="Admin-only: Run custom RCON command")
@app_commands.describe(server="Server key", command="Raw RCON command to send")
async def custom(interaction: discord.Interaction, server: str, command: str):
    print(f"custom called with: {server}, {command}")
    if not is_admin(interaction.user):
        await interaction.response.send_message("❌ You don't have permission to use this.", ephemeral=True)
        return

    guild_id = interaction.guild_id
    guild_servers = get_guild_servers(guild_id)

    if server not in guild_servers:
        await interaction.response.send_message(f"❌ Server '{server}' is not available in this Discord server.",
                                                ephemeral=True)
        return

    result = rcon_command(server, command)
    await interaction.response.send_message(f"[{server}] {result}")
