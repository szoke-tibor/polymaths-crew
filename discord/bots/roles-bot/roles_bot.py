"""Reaction roles without an always-on bot.

Runs periodically (e.g. every 5 min from GitHub Actions):
  1. Makes sure the bot's role message exists in the roles channel (posts it,
     edits it if roles.json changed, adds the emoji reactions).
  2. For every emoji in roles.json: whoever reacted gets the role, whoever has
     the role but no reaction loses it. The reactions are the source of truth.

Stdlib only (Python 3.9+). Config via environment variables:
  DISCORD_TOKEN   bot token (required)
  GUILD_ID        server id (required)
  CHANNEL_ID      roles channel id (required)
  CONFIG          path to roles.json (default: roles.json next to this file)
  DRY_RUN         "1" = only print what would change

Discord setup: Server Members Intent ON; bot permissions View Channels, Send
Messages, Read Message History, Add Reactions, Manage Roles; the bot's role must
be ABOVE the roles it manages.
"""

import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

API = "https://discord.com/api/v10"
MESSAGE_MARKER = "Opt-in roles"


class Discord:
    def __init__(self, token):
        self.headers = {
            "Authorization": f"Bot {token}",
            "Content-Type": "application/json",
            "User-Agent": "DiscordBot (roles-bot, 1.0)",
            "X-Audit-Log-Reason": "roles-bot reaction sync",
        }

    def call(self, method, path, body=None):
        data = json.dumps(body).encode() if body is not None else None
        for _ in range(6):
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
                raise RuntimeError(
                    f"{method} {path} -> {e.code}: {e.read().decode(errors='replace')}"
                )
        raise RuntimeError(f"{method} {path}: rate limited too many times")


def render(config, role_ids):
    lines = [config["title"], config["intro"], ""]
    for r in config["roles"]:
        lines.append(f"{r['emoji']} → <@&{role_ids[r['role']]}>: {r['description']}")
    return "\n".join(lines)


def diff(reactors, holders):
    """Return (to_add, to_remove) user id sets."""
    return reactors - holders, holders - reactors


def reactors_of(dc, channel_id, message_id, emoji):
    users, after = set(), None
    enc = urllib.parse.quote(emoji)
    while True:
        q = "?limit=100" + (f"&after={after}" if after else "")
        page = dc.call("GET", f"/channels/{channel_id}/messages/{message_id}/reactions/{enc}{q}") or []
        users |= {u["id"] for u in page if not u.get("bot")}
        if len(page) < 100:
            return users
        after = page[-1]["id"]


def members_by_role(dc, guild_id):
    """{role_id: {user ids}} for all non-bot members (needs Server Members Intent)."""
    result, after = {}, "0"
    while True:
        page = dc.call("GET", f"/guilds/{guild_id}/members?limit=1000&after={after}") or []
        for m in page:
            if m["user"].get("bot"):
                continue
            for rid in m.get("roles", []):
                result.setdefault(rid, set()).add(m["user"]["id"])
        if len(page) < 1000:
            return result
        after = page[-1]["user"]["id"]


def ensure_message(dc, channel_id, me_id, content, emojis, dry_run):
    recent = dc.call("GET", f"/channels/{channel_id}/messages?limit=50") or []
    msg = next(
        (m for m in recent if m["author"]["id"] == me_id and MESSAGE_MARKER in m.get("content", "")),
        None,
    )
    body = {"content": content, "allowed_mentions": {"parse": []}}
    if msg is None:
        if dry_run:
            print("[DRY RUN] would post the role message")
            return None
        msg = dc.call("POST", f"/channels/{channel_id}/messages", body)
        print(f"Posted role message {msg['id']}")
    elif msg["content"] != content and not dry_run:
        msg = dc.call("PATCH", f"/channels/{channel_id}/messages/{msg['id']}", body)
        print("Updated role message text")
    present = {
        r["emoji"]["name"] for r in msg.get("reactions", []) if r.get("me")
    }
    for e in emojis:
        if e not in present and not dry_run:
            dc.call("PUT", f"/channels/{channel_id}/messages/{msg['id']}/reactions/{urllib.parse.quote(e)}/@me")
    return msg


def main():
    token = os.environ["DISCORD_TOKEN"]
    guild_id = os.environ["GUILD_ID"]
    channel_id = os.environ["CHANNEL_ID"]
    dry_run = os.environ.get("DRY_RUN") == "1"
    config_path = Path(os.environ.get("CONFIG", Path(__file__).with_name("roles.json")))
    config = json.loads(config_path.read_text(encoding="utf-8"))

    dc = Discord(token)
    me = dc.call("GET", "/users/@me")
    guild_roles = {r["name"].lower(): r["id"] for r in dc.call("GET", f"/guilds/{guild_id}/roles")}
    role_ids = {}
    for r in config["roles"]:
        rid = guild_roles.get(r["role"].lower())
        if not rid:
            sys.exit(f"Role '{r['role']}' not found on the server")
        role_ids[r["role"]] = rid

    content = render(config, role_ids)
    msg = ensure_message(dc, channel_id, me["id"], content, [r["emoji"] for r in config["roles"]], dry_run)
    if msg is None:
        return

    holders = members_by_role(dc, guild_id)
    for r in config["roles"]:
        rid = role_ids[r["role"]]
        reactors = reactors_of(dc, channel_id, msg["id"], r["emoji"])
        to_add, to_remove = diff(reactors, holders.get(rid, set()))
        for uid in sorted(to_add):
            print(f"{'[DRY RUN] ' if dry_run else ''}+ {r['role']} -> {uid}")
            if not dry_run:
                dc.call("PUT", f"/guilds/{guild_id}/members/{uid}/roles/{rid}")
        for uid in sorted(to_remove):
            print(f"{'[DRY RUN] ' if dry_run else ''}- {r['role']} -> {uid}")
            if not dry_run:
                dc.call("DELETE", f"/guilds/{guild_id}/members/{uid}/roles/{rid}")
        print(f"{r['role']}: {len(reactors)} reacted, +{len(to_add)} / -{len(to_remove)}")


if __name__ == "__main__":
    main()
