# CEGBot - Discord Reaction Role Bot & Web Admin Panel

CEGBot is a modern, lightweight Python Discord Bot paired with a glassmorphic **Web Admin Dashboard**.
It allows server administrators to design customizable Discord Embed messages with reaction role mappings directly from a browser interface.

## Features

- 🎨 **Live Discord Embed Preview**: Visual previewer in the web admin panel that mirrors Discord's embed styling in real-time.
- 📌 **Custom Reaction Roles**: Map any Unicode emoji or custom Discord emoji to server roles.
- 🤖 **Auto Reaction Adding**: When a panel is deployed, the bot automatically adds the reaction emojis to the message in Discord.
- 🔄 **Reaction Listener**: Automatically assigns roles when members react and removes roles when reactions are removed.
- 📁 **JSON Data Storage**: Clean, lightweight storage in `panels.json`. No complex database setup required.

## Getting Started

### 1. Configuration
Copy `.env.example` to `.env` or use the **⚙️ Settings** modal inside the Web Admin Panel to set your Discord Bot Token:
```env
DISCORD_TOKEN=your_discord_bot_token_here
PORT=8000
```

### 2. Run the Application
Launch both the Web Admin Panel and Discord Bot simultaneously:
```bash
python3 main.py
```

Open your browser and navigate to:
```
http://localhost:8000
```

### 3. Required Discord Bot Intents
Make sure to enable the following Privileged Gateway Intents in your [Discord Developer Portal](https://discord.com/developers/applications):
- **Server Members Intent** (Required for role assignment)
- **Message Content Intent** (Required for embed deployment)

Ensure the Bot role is placed **above** the roles it needs to assign in your Discord Server Settings $\rightarrow$ Roles hierarchy.
