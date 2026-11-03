# polymaths-crew

Tools and automation for the Polymaths Crew community.

## Structure

```
discord/
  bots/
    goals-bot/   # daily reminder for overdue #goals posts
.github/workflows/
  goals-deadline-check.yml   # runs goals-bot every day
```

## goals-bot

Checks the `#goals` forum once a day. If a post's `📅 Target date:` has passed and
it has no **✅ Done** tag, the bot replies in the post, pinging the author and
`@accountability` (once per target date).

Setup and local run: [discord/bots/goals-bot/README.md](discord/bots/goals-bot/README.md)
