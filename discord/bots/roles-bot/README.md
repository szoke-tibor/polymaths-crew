# roles-bot

Reaction roles without an always-on bot. Every ~5 minutes (GitHub Actions) it
keeps one message in `#roles` up to date and syncs roles from its reactions:
react 🎯 → get `@accountability`, remove the reaction → lose it.

The reactions are the source of truth: a role given by hand to someone who
hasn't reacted is removed on the next run.

## Add or change a role

Edit [`roles.json`](roles.json) (emoji, role name as on the server, description)
and push. The bot edits its message and adds the new reaction by itself.
The role must already exist on the server and sit **below** the bot's role.

## Setup

1. **Bot**: https://discord.com/developers/applications → New Application →
   *Bot* tab → enable **Server Members Intent** → *Reset Token* and copy it.
2. **Invite** (replace `APP_ID`):
   `https://discord.com/oauth2/authorize?client_id=APP_ID&scope=bot&permissions=268504128`
   (View Channels, Send Messages, Read Message History, Add Reactions, Manage Roles)
3. **Role order**: Server Settings → Roles → drag the bot's role **above**
   `accountability` (and any other role in `roles.json`).
4. **GitHub**: repo secret `ROLES_BOT_DISCORD_TOKEN`. Server and `#roles` ids are
   in `.github/workflows/roles-sync.yml`.
5. Test: Actions → *roles sync* → Run workflow with **dry run**, then without.

## Local run

```sh
DISCORD_TOKEN=... GUILD_ID=... CHANNEL_ID=... DRY_RUN=1 python3 roles_bot.py
python3 -m unittest
```
