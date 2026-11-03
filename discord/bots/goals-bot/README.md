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
3. **Role**: `@accountability` must be *mentionable* (Server Settings → Roles).
   The bot finds it by name (`ROLE_NAME`), no ID needed.
4. **GitHub**: add repo secret `GOALS_BOT_DISCORD_TOKEN` (Settings → Secrets and
   variables → Actions). Server and `#goals` channel ids are set in
   `.github/workflows/goals-deadline-check.yml`.
5. Test: Actions → *goals deadline check* → Run workflow with **dry run** ticked.

## Local run

```sh
DISCORD_TOKEN=... GUILD_ID=... CHANNEL_ID=... DRY_RUN=1 python3 goals_bot.py
python3 -m unittest
```
