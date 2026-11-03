# goals-bot

Daily check of the `#goals` forum: if a post's `📅 Target date:` has passed and it
has no **✅ Done** tag, the bot replies in that post once, pinging the author and
`@accountability`.

## Setup

1. **Bot**: https://discord.com/developers/applications → New Application →
   *Bot* tab → enable **Message Content Intent** → *Reset Token* and copy it.
2. **Invite** (replace `APP_ID` with the Application ID from *General Information*):
   `https://discord.com/oauth2/authorize?client_id=APP_ID&scope=bot&permissions=274877973504`
   (View Channels, Read Message History, Send Messages in Threads)
3. **Role**: make `@accountability` *mentionable* (Server Settings → Roles), or the
   role ping won't notify anyone.
4. **IDs**: User Settings → Advanced → Developer Mode on, then right-click →
   *Copy ID* on the server, the `#goals` channel and the role.
5. **GitHub** (run in the polymaths-crew repo; workflow: `.github/workflows/goals-deadline-check.yml`):
   ```sh
   gh secret set GOALS_BOT_DISCORD_TOKEN   # paste token when asked
   gh variable set GUILD_ID   --body <server id>
   gh variable set CHANNEL_ID --body <#goals id>
   gh variable set ROLE_ID    --body <role id>
   ```
6. Test: Actions → *goals deadline check* → Run workflow with **dry run** ticked.

## Local run

```sh
DISCORD_TOKEN=... GUILD_ID=... CHANNEL_ID=... ROLE_ID=... DRY_RUN=1 python3 goals_bot.py
python3 -m unittest
```
