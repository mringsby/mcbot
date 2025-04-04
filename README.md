# Minecraft Discord Bot

A Discord bot for managing Minecraft servers through RCON commands.

## Setup Instructions

1. Clone this repository
2. Create a virtual environment: `python -m venv .venv`
3. Activate the virtual environment:
   - Windows: `.venv\Scripts\activate`
   - Linux/Mac: `source .venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Create a `.env` file with your Discord bot token:
   ```
   TOKEN=your_discord_token_here
   ```
6. Run the bot: `python main.py`

## Commands

- `/add_server` - Add a new Minecraft server (admin only)
- `/list_servers` - List available Minecraft servers
- `/say` - Broadcast a message on the server
- `/weather` - Set weather (clear, rain, thunder)
- `/whitelist` - Add yourself to the server whitelist
- `/custom` - Run custom RCON command (admin only)

## Configuration

Servers are stored in `servers.json` with the following structure:

```json
{
    "server_key": {
        "host": "server_ip",
        "port": 25575,
        "password": "rcon_password",
        "allowed_guilds": [guild_id1, guild_id2]
    }
}
```

## Security Notes

- Always keep your `.env` file out of version control
- Reset your bot token if it has been exposed
- Be careful about who has admin privileges in your Discord server, as they can run custom commands
