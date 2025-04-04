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

class UserManagementSystem:
    """Singleton class to manage user additions/removals"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(UserManagementSystem, cls).__new__(cls)
            cls._instance._load_data()
        return cls._instance
    
    def _load_data(self):
        self.DATA_FILE = "user_management.json"
        
        if not os.path.exists(self.DATA_FILE) or os.path.getsize(self.DATA_FILE) == 0:
            self.data = {"entries": {}}
            self._save_data()
        else:
            with open(self.DATA_FILE) as f:
                self.data = json.load(f)
    
    def _save_data(self):
        with open(self.DATA_FILE, "w") as f:
            json.dump(self.data, f, indent=4)
    
    def record_addition(self, server_key, minecraft_username, discord_user_id):
        """Record who added which username to which server"""
        entry_key = f"{server_key}:{minecraft_username.lower()}"
        self.data["entries"][entry_key] = discord_user_id
        self._save_data()
    
    def can_remove(self, server_key, minecraft_username, discord_user_id, is_admin=False):
        """Check if user can remove a username"""
        entry_key = f"{server_key}:{minecraft_username.lower()}"
        if is_admin:
            return True
        if entry_key in self.data["entries"]:
            return str(self.data["entries"][entry_key]) == str(discord_user_id)
        return False
    
    def remove_entry(self, server_key, minecraft_username):
        """Remove the entry after successful removal"""
        entry_key = f"{server_key}:{minecraft_username.lower()}"
        if entry_key in self.data["entries"]:
            del self.data["entries"][entry_key]
            self._save_data()

# Create a singleton instance for user management
user_manager = UserManagementSystem()

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

def add_player(server_key, minecraft_username, discord_user_id):
    """Add a player to the whitelist and record who added them"""
    # Use explicit "whitelist add" command
    result = rcon_command(server_key, "whitelist add " + minecraft_username)
    user_manager.record_addition(server_key, minecraft_username, discord_user_id)
    return result

def remove_player(server_key, minecraft_username, discord_user_id, is_admin=False):
    """Remove a player from the whitelist if allowed"""
    if user_manager.can_remove(server_key, minecraft_username, discord_user_id, is_admin):
        # Use explicit "whitelist remove" command
        result = rcon_command(server_key, "whitelist remove " + minecraft_username)
        if "Removed" in result or "was not on" in result:
            user_manager.remove_entry(server_key, minecraft_username)
        return result, True
    else:
        return "You can only remove players that you added yourself.", False
