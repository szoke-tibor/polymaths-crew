# polymaths-crew

Tools and automation for the Polymaths Crew community.

## Structure

```
discord/
  bots/
    goals-bot/   # daily reminder for overdue #goals posts
    roles-bot/   # reaction roles in #roles (🎯 → @accountability)
.github/workflows/
  goals-deadline-check.yml   # runs goals-bot every day
  roles-sync.yml             # runs roles-bot every 5 minutes
```

## goals-bot

Checks the `#goals` forum once a day. If a post's `📅 Target date:` has passed and
it has no **✅ Done** tag, the bot replies in the post, pinging the author and
`@accountability` (once per target date).

Setup and local run: [discord/bots/goals-bot/README.md](discord/bots/goals-bot/README.md)

## roles-bot

Keeps an opt-in role message in `#roles` and syncs roles from its reactions every
~5 minutes. Roles are configured in `roles.json`.

Setup: [discord/bots/roles-bot/README.md](discord/bots/roles-bot/README.md)
