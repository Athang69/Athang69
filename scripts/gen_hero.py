#!/usr/bin/env python3
"""Generate the profile hero SVG (dark + light) for github.com/Athang69.

Design mirrors athangkali.me: editor chrome, line-number gutter, rendered
content. Stats are pulled live from the GitHub and LeetCode APIs so the
banner never goes stale -- see .github/workflows/refresh.yml.

    python3 scripts/gen_hero.py            # live stats
    python3 scripts/gen_hero.py --offline  # cached stats from stats.json
"""

import base64
import json
import os
import pathlib
import sys
import urllib.error
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
CACHE = ROOT / "assets" / "stats.json"

USER = "Athang69"
LEETCODE_USER = "AthangOP"
REPOS = [
    "kubernetes-sigs/headlamp",
    "kubearmor/KubeArmor",
    "headlamp-k8s/plugins",
    "vfarcic/dot-ai-headlamp",
]

W, H = 900, 432
TITLEBAR, TABBAR, STATUSBAR = 38, 38, 38
BODY_TOP = TITLEBAR + TABBAR
BODY_BOT = H - STATUSBAR
GUTTER_W = 64
PAD_X = 96
LINE_H = 22

THEMES = {
    "dark": dict(
        bg="#16161f", title="#101017", tabbar="#12121a", tab_active="#16161f",
        border="#2a2a38", text="#c9c9d4", dim="#8c8ca0", bright="#f2f2ff",
        accent="#8669fc", comment="#6b9a56", gutter="#3d3d50",
        minimap=["#8669fc", "#82aaff", "#4ec9b0", "#c586c0", "#8c8ca0"],
        minimap_op=0.30, shadow_op=0.55,
    ),
    "light": dict(
        bg="#ffffff", title="#f1f1f6", tabbar="#f7f7fa", tab_active="#ffffff",
        border="#e3e3ec", text="#3a3a52", dim="#6b6b87", bright="#101017",
        accent="#5b34e0", comment="#4a7a36", gutter="#b4b4c6",
        minimap=["#5b34e0", "#2f6fd0", "#128271", "#a2489c", "#6b6b87"],
        minimap_op=0.38, shadow_op=0.10,
    ),
}


# ---------------------------------------------------------------- stats

def _get(url, headers=None):
    req = urllib.request.Request(url, headers=headers or {})
    req.add_header("User-Agent", "athang-profile-hero")
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode())


def _gh_count(query):
    headers = {"Accept": "application/vnd.github+json"}
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    url = "https://api.github.com/search/issues?per_page=1&q=" + urllib.parse.quote(query)
    return _get(url, headers).get("total_count", 0)


def fetch_stats():
    merged = _gh_count(f"author:{USER} is:pr is:merged {' '.join('repo:'+r for r in REPOS)}")
    review = _gh_count(f"author:{USER} is:pr is:open -is:draft {' '.join('repo:'+r for r in REPOS)}")

    q = {"query": """
        query($u: String!) {
          matchedUser(username: $u) {
            submitStatsGlobal { acSubmissionNum { difficulty count } }
          }
          userContestRanking(username: $u) { rating }
        }""", "variables": {"u": LEETCODE_USER}}
    req = urllib.request.Request(
        "https://leetcode.com/graphql",
        data=json.dumps(q).encode(),
        headers={"Content-Type": "application/json", "Referer": "https://leetcode.com",
                 "User-Agent": "Mozilla/5.0"},
    )
    with urllib.request.urlopen(req, timeout=20) as r:
        lc = json.loads(r.read().decode())["data"]
    solved = next(d["count"] for d in
                  lc["matchedUser"]["submitStatsGlobal"]["acSubmissionNum"]
                  if d["difficulty"] == "All")
    rating = round((lc.get("userContestRanking") or {}).get("rating") or 0)
    return {"merged": merged, "review": review, "solved": solved, "rating": rating}


def load_stats(offline):
    cached = json.loads(CACHE.read_text()) if CACHE.exists() else {}
    if offline:
        return cached
    try:
        s = fetch_stats()
        CACHE.write_text(json.dumps(s, indent=2) + "\n")
        return s
    except (urllib.error.URLError, KeyError, StopIteration, TimeoutError) as e:
        print(f"  ! live fetch failed ({e}); using cached stats", file=sys.stderr)
        return cached


# ---------------------------------------------------------------- svg

def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def font_face(name, filename, weight="100 900"):
    data = base64.b64encode((ASSETS / "fonts" / filename).read_bytes()).decode()
    return (f"@font-face{{font-family:'{name}';font-style:normal;"
            f"font-weight:{weight};font-display:block;"
            f"src:url(data:font/woff2;base64,{data}) format('woff2')}}")


def text(x, y, s, cls, **kw):
    attrs = "".join(f' {k.replace("_","-")}="{v}"' for k, v in kw.items())
    return f'<text x="{x}" y="{y}" class="{cls}"{attrs}>{esc(s)}</text>'


def build(theme_name, st):
    c = THEMES[theme_name]
    o = []
    a = o.append

    a(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
      f'viewBox="0 0 {W} {H}" role="img" '
      f'aria-label="Athang Kali - Systems Engineer, Cloud Native and Backend, Open Source Contributor">')
    a("<title>Athang Kali — Systems Engineer · Cloud Native · Open Source</title>")

    a("<style>")
    a(font_face("JBM", "jetbrains-mono.woff2"))
    a(font_face("Syne", "syne.woff2", "400 800"))
    a(f".m{{font-family:'JBM',ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}}")
    a(f".d{{font-family:'Syne','JBM',ui-sans-serif,system-ui,sans-serif;font-weight:800}}")
    a("</style>")

    # ---- window
    a(f'<rect width="{W}" height="{H}" rx="12" fill="{c["bg"]}"/>')
    a(f'<path d="M0 12a12 12 0 0 1 12-12h{W-24}a12 12 0 0 1 12 12v{TITLEBAR-12}H0z" fill="{c["title"]}"/>')
    a(f'<rect y="{TITLEBAR}" width="{W}" height="{TABBAR}" fill="{c["tabbar"]}"/>')

    # traffic lights
    for i, col in enumerate(("#ff5f57", "#febc2e", "#28c840")):
        a(f'<circle cx="{22+i*19}" cy="{TITLEBAR/2}" r="5.5" fill="{col}" opacity="0.92"/>')
    a(text(W / 2, TITLEBAR / 2 + 4, "athang-kali : profile", "m",
           fill=c["dim"], font_size="11.5", text_anchor="middle", letter_spacing="0.4"))

    # ---- tabs
    tabs = [("home.tsx", c["accent"], True), ("opensource.go", "#4ec9b0", False),
            ("contact.sh", "#dcdcaa", False)]
    tx = 0
    for label, dot, active in tabs:
        tw = 26 + len(label) * 7.1 + 24
        if active:
            a(f'<rect x="{tx}" y="{TITLEBAR}" width="{tw:.1f}" height="{TABBAR}" fill="{c["tab_active"]}"/>')
            a(f'<rect x="{tx}" y="{TITLEBAR}" width="{tw:.1f}" height="2" fill="{c["accent"]}"/>')
        a(f'<rect x="{tx+16}" y="{TITLEBAR+16}" width="7" height="7" rx="1.5" fill="{dot}" opacity="0.9"/>')
        a(text(tx + 31, TITLEBAR + TABBAR / 2 + 4, label, "m",
               fill=c["bright"] if active else c["dim"], font_size="11.5"))
        tx += tw
    a(f'<rect y="{BODY_TOP-1}" width="{W}" height="1" fill="{c["border"]}"/>')

    # ---- gutter
    n = int((BODY_BOT - BODY_TOP) / LINE_H)
    for i in range(n):
        a(text(GUTTER_W - 18, BODY_TOP + LINE_H * (i + 1), str(i + 1), "m",
               fill=c["gutter"], font_size="11.5", text_anchor="end"))

    # ---- content
    a(text(PAD_X, 103, "// home.tsx", "m", fill=c["comment"], font_size="13"))
    a(text(PAD_X, 141, "LFX MENTEE 2026  ·  CNCF HEADLAMP", "m",
           fill=c["accent"], font_size="11", letter_spacing="2.1", font_weight="500"))
    a(text(PAD_X - 3, 206, "Athang Kali", "d", fill=c["bright"], font_size="56",
           letter_spacing="-1.2"))
    a(text(PAD_X, 240, "Systems Engineer  ·  Cloud Native / Backend  ·  Open Source", "m",
           fill=c["dim"], font_size="14"))
    a(f'<rect x="{PAD_X}" y="272" width="716" height="1" fill="{c["border"]}"/>')

    stats = [(str(st.get("merged", "—")), "PRS MERGED"),
             (str(st.get("review", "—")), "IN REVIEW"),
             (str(st.get("solved", "—")), "PROBLEMS SOLVED"),
             (str(st.get("rating", "—")), "LEETCODE RATING")]
    for i, (num, label) in enumerate(stats):
        x = PAD_X + i * 184
        a(text(x, 318, num, "d", fill=c["bright"], font_size="30", letter_spacing="-0.5"))
        a(text(x, 340, label, "m", fill=c["dim"], font_size="9.5", letter_spacing="1.7"))

    # ---- minimap
    seed = 1337
    y = BODY_TOP + 10
    while y < BODY_BOT - 8:
        seed = (seed * 1103515245 + 12345) & 0x7FFFFFFF
        wbar = 8 + (seed >> 5) % 40
        col = c["minimap"][(seed >> 11) % len(c["minimap"])]
        a(f'<rect x="838" y="{y}" width="{wbar}" height="2" rx="1" fill="{col}" '
          f'opacity="{c["minimap_op"]:.2f}"/>')
        y += 5

    # ---- status bar
    sy = BODY_BOT
    a(f'<path d="M0 {sy}h{W}v{STATUSBAR-12}a12 12 0 0 1-12 12H12a12 12 0 0 1-12-12z" fill="{c["title"]}"/>')
    a(f'<rect y="{sy}" width="{W}" height="1" fill="{c["border"]}"/>')
    by = sy + STATUSBAR / 2
    a(f'<g stroke="{c["dim"]}" stroke-width="1.3" fill="none">'
      f'<circle cx="22" cy="{by-4.5}" r="2.6"/><circle cx="22" cy="{by+4.5}" r="2.6"/>'
      f'<circle cx="33" cy="{by-4.5}" r="2.6"/>'
      f'<path d="M22 {by-1.9}v2.4M24.6 {by-4.5}h5.8"/></g>')
    a(text(42, by + 4, "main", "m", fill=c["dim"], font_size="10.5"))
    a(f'<circle cx="92" cy="{by}" r="3" fill="{c["accent"]}"/>')
    a(text(103, by + 4, "LFX MENTEE · CNCF 2026 TERM 3", "m",
           fill=c["accent"], font_size="10.5", letter_spacing="0.5"))
    a(text(W - 22, by + 4, "athangkali.me", "m", fill=c["dim"], font_size="10.5",
           text_anchor="end"))

    a(f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="11.5" fill="none" stroke="{c["border"]}"/>')
    a("</svg>")
    return "\n".join(o)


def main():
    offline = "--offline" in sys.argv
    st = load_stats(offline)
    if not st:
        sys.exit("no stats available (no network and no assets/stats.json)")
    ASSETS.mkdir(exist_ok=True)
    for name in THEMES:
        p = ASSETS / f"hero-{name}.svg"
        p.write_text(build(name, st))
        print(f"  {p.relative_to(ROOT)}  {p.stat().st_size//1024} KB")
    print(f"  stats: {st}")


if __name__ == "__main__":
    main()
