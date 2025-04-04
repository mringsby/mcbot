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

@tree.command(name="help", description="Display available commands and their descriptions")
async def help_command(interaction: discord.Interaction):
    print("help command called")
    
    # Build embed for better formatting
    embed = discord.Embed(
        title="Minecraft Bot Commands",
        description="Here are the commands you can use:",
        color=discord.Color.blue()
    )
    
    # Public commands
    embed.add_field(
        name="Public Commands",
        value=(
            "`/help` - Show this help message\n"
            "`/list_servers` - List available Minecraft servers\n"
            "`/players` - Show who's currently online\n"
            "`/say <message>` - Broadcast a message to the server\n"
            "`/weather <type>` - Set weather (clear, rain, or thunder)\n"
            "`/whitelist add <username>` - Add player to whitelist\n"
            "`/whitelist remove <username>` - Remove player from whitelist"
        ),
        inline=False
    )
    
    # Status commands
    embed.add_field(
        name="Status Commands",
        value=(
            "`/status` - Get basic server status information\n"
            "`/tps` - Check server's Ticks Per Second\n"
            "`/memory` - Check server memory usage\n"
            "`/world` - Get information about the Minecraft world"
        ),
        inline=False
    )
    
    # Admin commands - only show if user is admin
    if is_admin(interaction.user):
        embed.add_field(
            name="Admin Commands",
            value=(
                "`/add_server <key> <host> <port> <password>` - Add a new server\n"
                "`/custom <server> <command>` - Run custom RCON command"
            ),
            inline=False
        )
    
    # Tips
    embed.add_field(
        name="Tips",
        value="For commands that need a server parameter, you can omit it if only one server is available",
        inline=False
    )
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

@tree.command(name="players", description="Show who's currently online on the server")
@app_commands.describe(server="Server key from servers.json (optional if only one server)")
async def players(interaction: discord.Interaction, server: str = None):
    print(f"players called with: {server}")
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

    # Get online players using "list" command
    result = rcon_command(server, "list")
    
    # Create a nice embed
    embed = discord.Embed(
        title=f"Players on {server}",
        description=result,
        color=discord.Color.green()
    )
    
    await interaction.response.send_message(embed=embed)

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

# --- Status Commands ---

@tree.command(name="status", description="Get server status information")
@app_commands.describe(server="Server key from servers.json (optional if only one server)")
async def status(interaction: discord.Interaction, server: str = None):
    print(f"status called with: {server}")
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

    # Get version information
    version_info = rcon_command(server, "version")
    
    # Get player count
    player_count = rcon_command(server, "list")
    
    # Create embed
    embed = discord.Embed(
        title=f"{server} - Server Status",
        color=discord.Color.blue()
    )
    
    embed.add_field(name="Version", value=version_info, inline=False)
    embed.add_field(name="Players", value=player_count, inline=False)
    
    await interaction.response.send_message(embed=embed)

@tree.command(name="tps", description="Check server's Ticks Per Second")
@app_commands.describe(server="Server key from servers.json (optional if only one server)")
async def tps(interaction: discord.Interaction, server: str = None):
    print(f"tps called with: {server}")
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

    # Get TPS information (different commands depending on server type)
    # Try Spigot/Paper command first
    result = rcon_command(server, "tps")
    
    # If that didn't work, try vanilla command
    if "Unknown command" in result:
        result = rcon_command(server, "debug start")
        # Wait briefly
        await interaction.response.defer()
        import asyncio
        await asyncio.sleep(5)
        result = rcon_command(server, "debug stop")
    
    embed = discord.Embed(
        title=f"{server} - TPS Information",
        description=result,
        color=discord.Color.green()
    )
    
    await interaction.response.send_message(embed=embed)

@tree.command(name="memory", description="Check server memory usage")
@app_commands.describe(server="Server key from servers.json (optional if only one server)")
async def memory(interaction: discord.Interaction, server: str = None):
    print(f"memory called with: {server}")
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

    # Different servers might have different commands for this
    # Try Paper GC command
    result = rcon_command(server, "gc")
    
    if "Unknown command" in result:
        # If not Paper/Spigot, fallback to less detailed message
        result = "Memory information only available on Paper/Spigot servers with GC command enabled."
    
    embed = discord.Embed(
        title=f"{server} - Memory Usage",
        description=result,
        color=discord.Color.gold()
    )
    
    await interaction.response.send_message(embed=embed)

@tree.command(name="world", description="Get information about the Minecraft world")
@app_commands.describe(server="Server key from servers.json (optional if only one server)")
async def world(interaction: discord.Interaction, server: str = None):
    print(f"world called with: {server}")
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

    # Get time information
    time_info = rcon_command(server, "time query daytime")
    
    # Get weather information
    weather_info = rcon_command(server, "weather query")
    
    # Get difficulty
    difficulty_info = rcon_command(server, "difficulty")
    
    embed = discord.Embed(
        title=f"{server} - World Information",
        color=discord.Color.purple()
    )
    
    embed.add_field(name="Time", value=time_info, inline=False)
    embed.add_field(name="Weather", value=weather_info, inline=False)
    embed.add_field(name="Difficulty", value=difficulty_info, inline=False)
    
    await interaction.response.send_message(embed=embed)

