#!/usr/bin/env python3
"""Scan GitHub repos for Saraswat ecosystem."""
import urllib.request
import json

TOKEN = ""
HEADERS = {
    "Authorization": f"token {TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

def api_get(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())

# Get all repos
print("=" * 60)
print("  GITHUB REPOSITORIES")
print("=" * 60)

repos = api_get("https://api.github.com/users/suryamayaharum-droid/repos?per_page=100&type=all")

for r in repos:
    vis = "🔒" if r["private"] else "🌐"
    lang = r.get("language") or "N/A"
    desc = r.get("description") or "(sem desc)"
    updated = r["updated_at"][:10]
    print(f"{vis} {r['name']:40s} | {lang:12s} | {updated} | {desc}")

print(f"\nTotal: {len(repos)} repositorios")
print("=" * 60)
