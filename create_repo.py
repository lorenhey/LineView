import os
import json
import ssl
import urllib.request

token = os.environ.get("GITHUB_TOKEN")
if not token:
    raise ValueError("GITHUB_TOKEN not found")

# Bypass SSL
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# 1. Create Repository
repo_data = {
    "name": "LineView",
    "description": "A lightweight scientific viewer for astronomical spectra.",
    "private": False,
    "has_issues": True
}
req = urllib.request.Request(
    "https://api.github.com/user/repos",
    data=json.dumps(repo_data).encode("utf-8"),
    headers={
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json"
    }
)

try:
    with urllib.request.urlopen(req, context=ctx) as response:
        print("Repo created successfully.")
except urllib.error.HTTPError as e:
    if e.code == 422: # Already exists
        print("Repo might already exist.")
    else:
        raise

# 2. Add Deploy Key
with open(".git/deploy_key.pub", "r") as f:
    pub_key = f.read().strip()

key_data = {
    "title": "LineView Deploy Key",
    "key": pub_key,
    "read_only": False
}

req_key = urllib.request.Request(
    "https://api.github.com/repos/lorenhey/LineView/keys",
    data=json.dumps(key_data).encode("utf-8"),
    headers={
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json"
    }
)

try:
    with urllib.request.urlopen(req_key, context=ctx) as response:
        print("Deploy key added successfully.")
except urllib.error.HTTPError as e:
    if e.code == 422:
        print("Deploy key already exists.")
    else:
        print(f"Error adding key: {e.read().decode()}")
        raise
