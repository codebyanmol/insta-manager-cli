# Instagram Manager CLI

A powerful, feature-rich command-line tool for managing your Instagram followers
and following list — built with Python, [instagrapi](https://github.com/subzeroid/instagrapi), and [Rich](https://github.com/Textualize/rich).

---

## ⚠ Important Disclaimer

> This tool uses **instagrapi**, an **unofficial** third-party Instagram client.
> Instagram may restrict or ban accounts that use automated tools.
> Use this tool **responsibly**, with generous delays between actions, and at
> your own risk. The authors are not responsible for any account suspensions
> or data loss.

---

## Features

| Category            | Details |
|---------------------|---------|
| **Login**           | Username + password, 2FA support, saved sessions |
| **Followers**       | View followers, following, non-followers, mutuals |
| **Unfollowing**     | Non-followers only, everyone, or selective pick |
| **Safety System**   | Configurable random delays, per-session action cap |
| **Export**          | CSV, JSON, TXT export of any list |
| **Settings**        | Delay range, session limit, logging toggle |
| **Activity Logs**   | Every action timestamped in `logs/instagram_manager.log` |
| **UI**              | Full colour terminal UI via Rich — no GUI required |

---

## Directory Structure

```
instagram-manager/
├── instagram_manager.py   # Main entry point
├── requirements.txt
├── README.md
├── settings.json          # Created on first settings change
├── session.json           # Created on first login (auto-managed)
├── logs/
│   └── instagram_manager.log
├── exports/               # All exported files land here
└── modules/
    ├── __init__.py
    ├── auth.py            # Login / session management
    ├── client.py          # instagrapi wrapper + cache
    ├── display.py         # Rich terminal UI components
    ├── followers.py       # Follower list & unfollow operations
    ├── export.py          # CSV / JSON / TXT export
    ├── settings.py        # Settings persistence
    └── logger.py          # Activity logging
```

---

## Requirements

- Python **3.10+**
- pip packages listed in `requirements.txt`

---

## Installation

```bash
# 1. Clone or download the project
git clone https://github.com/codebyanmol/insta-manager-cli.git
cd instagram-manager

# 2. (Optional but recommended) Create a virtual environment
python -m venv venv
source venv/bin/activate        # macOS / Linux
venv\Scripts\activate           # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the tool
python instagram_manager.py
```

---

## Usage

```
python instagram_manager.py
```

You will be greeted by the **Authentication Menu**:

```
[1] Login with Username & Password
[2] Use Saved Session              (if a session exists)
[3] Exit
```

After login, the **Main Menu** appears:

```
Instagram Manager

 [1]  View Account Information      Stats & overview
 [2]  List Followers                See who follows you
 [3]  List Following                See who you follow
 [4]  Show Non-Followers            They don't follow back
 [5]  Show Mutual Followers         Both follow each other
 [6]  Unfollow Non-Followers        Auto-clean non-followers
 [7]  Unfollow All                  Remove all following
 [8]  Selective Unfollow            Choose who to unfollow
 [9]  Export User Lists             CSV / JSON / TXT
[10]  Automation Settings           Delays, limits, options
[11]  View Activity Logs            Review past actions
[12]  Help                          Commands & safety tips
[13]  Logout                        Switch account
[14]  Exit
```

---

## Automation Settings

| Setting                  | Default | Description |
|--------------------------|---------|-------------|
| `min_delay`              | 20s     | Minimum pause between unfollow actions |
| `max_delay`              | 90s     | Maximum pause (random within range) |
| `max_unfollows_per_session` | 50   | Hard cap per run |
| `random_delay_enabled`   | true    | Randomise delay within range |
| `logging_enabled`        | true    | Write actions to log file |
| `confirm_bulk_actions`   | true    | Ask for confirmation before batch unfollows |

Settings are stored in `settings.json` and persist between sessions.

---

## Selective Unfollow Syntax

When prompted for a selection, you can use:

| Input      | Meaning |
|------------|---------|
| `1,3,7`    | Users #1, #3, and #7 |
| `2-10`     | Users #2 through #10 |
| `1,4-6,9`  | Mixed: #1, #4, #5, #6, #9 |
| `all`      | Every user in the list |

---

## Exports

Exports are saved to the `exports/` directory with timestamps:

```
exports/followers_20260314_103045.csv
exports/non_followers_20260314_103200.json
```

---

## Activity Log Format

```
[2026-03-14 10:23] Logged in successfully as @yourusername
[2026-03-14 10:30] Unfollowed user: @example_user
[2026-03-14 10:31] Unfollow batch complete — succeeded: 5, failed: 0
[2026-03-14 10:45] Exported non_followers (42 users) as csv → exports/...
```

---

## Tips for Safe Usage

1. **Keep delays high** — 30–120 seconds is safer than the defaults.
2. **Don't unfollow too many per day** — stay well under 200 actions/day.
3. **Space out sessions** — avoid running the tool multiple times in a row.
4. **Use a VPN** (optional) — reduces the chance of location-based challenges.
5. **Enable 2FA on your account** — protects you independent of this tool.

---

## License

MIT — see `LICENSE` for details.
