"""#goals deadline bot.

Runs once (e.g. daily from GitHub Actions). For every post in the #goals forum
channel that has no "Done" tag and whose target date has passed, it posts one
reminder into that post, pinging the author and the @accountability role.
It reminds only once per target date: if the author changes the date, the new
date gets its own reminder when it passes.

Stdlib only (Python 3.9+). Config via environment variables:
  DISCORD_TOKEN   bot token (required)
  GUILD_ID        server id (required)
  CHANNEL_ID      #goals forum channel id (required)
  ROLE_ID         @accountability role id (optional; no role ping if empty)
  DONE_TAG        name fragment of the "done" tag (default: "Done")
  TIMEZONE        timezone for "today" (default: Europe/Budapest)
  DRY_RUN         "1" = only print what would be posted
"""

import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import date, datetime
from zoneinfo import ZoneInfo

API = "https://discord.com/api/v10"

# "📅 Target date: 2026-11-15", also tolerates **bold**, 2026.11.15. and 2026/11/15
DATE_RE = re.compile(
    r"target\s*date\W*?(\d{4})[-./](\d{1,2})[-./](\d{1,2})", re.IGNORECASE
)


def parse_target_date(text):
    m = DATE_RE.search(text or "")
    if not m:
        return None
    try:
        return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError:
        return None


def marker(d):
    return f"[target {d.isoformat()}]"


class Discord:
    def __init__(self, token):
        self.headers = {
            "Authorization": f"Bot {token}",
            "Content-Type": "application/json",
            "User-Agent": "DiscordBot (goals-bot, 1.0)",
        }

    def call(self, method, path, body=None):
        data = json.dumps(body).encode() if body is not None else None
        for _ in range(5):
            req = urllib.request.Request(
                API + path, data=data, headers=self.headers, method=method
            )
            try:
                with urllib.request.urlopen(req) as resp:
                    raw = resp.read()
                    return json.loads(raw) if raw else None
            except urllib.error.HTTPError as e:
                if e.code == 429:
                    wait = json.loads(e.read() or b"{}").get("retry_after", 1)
                    time.sleep(float(wait) + 0.5)
                    continue
                if e.code == 404:
                    return None
                raise RuntimeError(
                    f"{method} {path} -> {e.code}: {e.read().decode(errors='replace')}"
                )
        raise RuntimeError(f"{method} {path}: rate limited too many times")


def forum_threads(dc, guild_id, channel_id):
    """Active threads + recently archived public threads of the forum."""
    threads = {}
    active = dc.call("GET", f"/guilds/{guild_id}/threads/active") or {}
    for t in active.get("threads", []):
        if t.get("parent_id") == channel_id:
            threads[t["id"]] = t
    before = None
    for _ in range(5):  # up to 500 archived posts
        q = "?limit=100" + (f"&before={before}" if before else "")
        page = dc.call("GET", f"/channels/{channel_id}/threads/archived/public{q}") or {}
        for t in page.get("threads", []):
            threads.setdefault(t["id"], t)
        if not page.get("has_more") or not page.get("threads"):
            break
        before = page["threads"][-1]["thread_metadata"]["archive_timestamp"]
    return list(threads.values())


def main():
    token = os.environ["DISCORD_TOKEN"]
    guild_id = os.environ["GUILD_ID"]
    channel_id = os.environ["CHANNEL_ID"]
    role_id = os.environ.get("ROLE_ID", "").strip()
    done_fragment = os.environ.get("DONE_TAG", "Done").lower()
    tz = ZoneInfo(os.environ.get("TIMEZONE", "Europe/Budapest"))
    dry_run = os.environ.get("DRY_RUN") == "1"
    today = datetime.now(tz).date()

    dc = Discord(token)
    me = dc.call("GET", "/users/@me")
    forum = dc.call("GET", f"/channels/{channel_id}")
    if not forum:
        sys.exit(f"Channel {channel_id} not found or bot can't see it")
    done_tags = {
        t["id"] for t in forum.get("available_tags", [])
        if done_fragment in t["name"].lower()
    }
    if not done_tags:
        print(f"WARNING: no tag containing '{done_fragment}' on the forum")

    reminded = skipped = 0
    for t in forum_threads(dc, guild_id, channel_id):
        name = t.get("name", "")
        if t.get("thread_metadata", {}).get("locked"):
            continue
        if done_tags & set(t.get("applied_tags", [])):
            continue
        # In forum channels the starter message id == thread id.
        starter = dc.call("GET", f"/channels/{t['id']}/messages/{t['id']}")
        target = parse_target_date((starter or {}).get("content")) or parse_target_date(name)
        if not target:
            skipped += 1
            continue
        if target >= today:
            continue

        recent = dc.call("GET", f"/channels/{t['id']}/messages?limit=50") or []
        if any(
            m["author"]["id"] == me["id"] and marker(target) in m.get("content", "")
            for m in recent
        ):
            continue

        owner = t.get("owner_id")
        pings = f"<@{owner}>" + (f" <@&{role_id}>" if role_id else "")
        content = (
            f"{pings} ⏰ The target date of this goal (**{target.isoformat()}**) has passed!\n"
            f"• Finished? Add the **✅ Done** tag 🎉\n"
            f"• Still going? Edit the post with a new target date and a short note on what slipped.\n"
            f"-# {marker(target)}"
        )
        body = {
            "content": content,
            "allowed_mentions": {
                "users": [owner] if owner else [],
                "roles": [role_id] if role_id else [],
            },
        }
        if dry_run:
            print(f"[DRY RUN] '{name}' ({target}): would post reminder")
        else:
            dc.call("POST", f"/channels/{t['id']}/messages", body)
            print(f"Reminded: '{name}' ({target})")
        reminded += 1

    print(f"Done. Reminders: {reminded}, posts without a target date: {skipped}")


if __name__ == "__main__":
    main()
