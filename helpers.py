import json
from mcrcon import MCRcon
import discord
import os

class ServerConfigManager:
    """Singleton class to manage server configuration"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ServerConfigManager, cls).__new__(cls)
            cls._instance._load_config()
        return cls._instance
    
    def _load_config(self):
        self.SERVERS_FILE = "servers.json"
        
        if not os.path.exists(self.SERVERS_FILE) or os.path.getsize(self.SERVERS_FILE) == 0:
            self.SERVERS = {}
            self._save_config()
        else:
            with open(self.SERVERS_FILE) as f:
                self.SERVERS = json.load(f)
    
    def _save_config(self):
        with open(self.SERVERS_FILE, "w") as f:
            json.dump(self.SERVERS, f, indent=4)
    
    def get_servers(self):
        return self.SERVERS
    
    def add_server(self, server_key, host, port, password, guild_id):
        if server_key in self.SERVERS:
            # If server exists, add this guild to allowed guilds
            if guild_id not in self.SERVERS[server_key].get("allowed_guilds", []):
                if "allowed_guilds" not in self.SERVERS[server_key]:
                    self.SERVERS[server_key]["allowed_guilds"] = []
                self.SERVERS[server_key]["allowed_guilds"].append(guild_id)
        else:
            # Create new server entry
            self.SERVERS[server_key] = {
                "host": host,
                "port": port,
                "password": password,
                "allowed_guilds": [guild_id]
            }
        
        self._save_config()
        return True

# Create a singleton instance
server_manager = ServerConfigManager()

def get_guild_servers(guild_id):
    """Get servers configured for a specific guild"""
    print(f"get_guild_servers called with: {guild_id}")
    guild_servers = {}
    for server_key, server_data in server_manager.get_servers().items():
        allowed_guilds = server_data.get("allowed_guilds", [])
        if not allowed_guilds or guild_id in allowed_guilds:
            guild_servers[server_key] = server_data
    print(f"guild_servers: {guild_servers}")
    return guild_servers

def get_single_guild_server(guild_id):
    """Get a single server if only one is available for a specific guild"""
    print(f"get_single_guild_server called with: {guild_id}")
    guild_servers = get_guild_servers(guild_id)
    if len(guild_servers) == 1:
        return next(iter(guild_servers))
    return None

def rcon_command(server_key, command):
    print(f"rcon_command called with: {server_key}, {command}")
    try:
        servers = server_manager.get_servers()
        if server_key not in servers:
            return "Error: Server not found"

        cfg = servers[server_key]
        with MCRcon(cfg["host"], cfg["password"], port=cfg["port"]) as mcr:
            return mcr.command(command)
    except Exception as e:
        print(f"Error in rcon_command: {e}")
        return f"Error: {e}"

def is_admin(user: discord.User | discord.Member):
    print(f"is_admin called with: {user}")
    return getattr(user, "guild_permissions", None) and user.guild_permissions.administrator

def add_server(server_key, host, port, password, guild_id):
    """Add a server to the configuration"""
    return server_manager.add_server(server_key, host, port, password, guild_id)
