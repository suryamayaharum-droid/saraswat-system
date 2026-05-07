#!/usr/bin/env python3
"""GitHub API client for Saraswat ecosystem."""
import urllib.request
import json
import sys
import os

TOKEN = ""
HEADERS = {
    "Authorization": f"token {TOKEN}",
    "Accept": "application/vnd.github.v3+json",
    "User-Agent": "Saraswat/1.0"
}

def api_get(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())

def api_post(url, data=None):
    body = json.dumps(data or {}).encode()
    req = urllib.request.Request(url, data=body, headers={**HEADERS, "Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())

def api_patch(url, data=None):
    body = json.dumps(data or {}).encode()
    req = urllib.request.Request(url, data=body, headers={**HEADERS, "Content-Type": "application/json"}, method="PATCH")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())

def list_repos():
    repos = api_get("https://api.github.com/users/suryamayaharum-droid/repos?per_page=100&type=all&sort=updated")
    return repos

def get_repo(owner, repo):
    return api_get(f"https://api.github.com/repos/{owner}/{repo}")

def get_readme(owner, repo):
    try:
        r = api_get(f"https://api.github.com/repos/{owner}/{repo}/readme")
        import base64
        return base64.b64decode(r["content"]).decode("utf-8")
    except:
        return None

def get_tree(owner, repo, branch="main"):
    try:
        r = api_get(f"https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive=1")
        return r.get("tree", [])
    except:
        try:
            r = api_get(f"https://api.github.com/repos/{owner}/{repo}/git/trees/master?recursive=1")
            return r.get("tree", [])
        except:
            return []

def get_file_content(owner, repo, path):
    try:
        r = api_get(f"https://api.github.com/repos/{owner}/{repo}/contents/{path}")
        import base64
        return base64.b64decode(r["content"]).decode("utf-8")
    except:
        return None

def create_file(owner, repo, path, content, message="Saraswat auto-update"):
    import base64
    encoded = base64.b64encode(content.encode()).decode()
    return api_put(f"https://api.github.com/repos/{owner}/{repo}/contents/{path}", {
        "message": message,
        "content": encoded
    })

def api_put(url, data=None):
    body = json.dumps(data or {}).encode()
    req = urllib.request.Request(url, data=body, headers={**HEADERS, "Content-Type": "application/json"}, method="PUT")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())

def fork_repo(owner, repo):
    return api_post(f"https://api.github.com/repos/{owner}/{repo}/forks")

def create_repo(name, description="", private=False):
    return api_post("https://api.github.com/user/repos", {
        "name": name,
        "description": description,
        "private": private,
        "auto_init": True
    })

def list_issues(owner, repo):
    return api_get(f"https://api.github.com/repos/{owner}/{repo}/issues?state=open&per_page=100")

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "list"

    if cmd == "list":
        repos = list_repos()
        print(f"\n{'='*80}")
        print(f"  GITHUB REPOSITORIES ({len(repos)} total)")
        print(f"{'='*80}\n")
        for r in repos:
            vis = "🔒" if r["private"] else "🌐"
            lang = r.get("language") or "N/A"
            desc = (r.get("description") or "(sem desc)")[:50]
            updated = r["updated_at"][:10]
            stars = r.get("stargazers_count", 0)
            forks = r.get("forks_count", 0)
            print(f"{vis} {r['name']:40s} | {lang:12s} | ⭐{stars} 🍴{forks} | {updated}")
            print(f"   {desc}")
            print()

    elif cmd == "readme" and len(sys.argv) > 2:
        repo_name = sys.argv[2]
        content = get_readme("suryamayaharum-droid", repo_name)
        if content:
            print(f"\n=== README: {repo_name} ===\n")
            print(content[:3000])
        else:
            print(f"No README found for {repo_name}")

    elif cmd == "tree" and len(sys.argv) > 2:
        repo_name = sys.argv[2]
        tree = get_tree("suryamayaharum-droid", repo_name)
        print(f"\n=== FILE TREE: {repo_name} ({len(tree)} files) ===\n")
        for item in tree[:100]:
            print(f"  {item['path']}")
        if len(tree) > 100:
            print(f"  ... and {len(tree)-100} more files")

    elif cmd == "issues" and len(sys.argv) > 2:
        repo_name = sys.argv[2]
        issues = list_issues("suryamayaharum-droid", repo_name)
        print(f"\n=== ISSUES: {repo_name} ({len(issues)} open) ===\n")
        for i in issues[:20]:
            print(f"  #{i['number']} {i['title']}")
