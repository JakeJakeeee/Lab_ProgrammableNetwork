#!/usr/bin/env python3
"""Make the lab API match intent.yaml.
    python3 sync.py intent.yaml --dry-run
    python3 sync.py intent.yaml
"""
import argparse
import os
import random
import sys
import time
import uuid

import requests
import yaml

API = os.environ.get("LAB_API_URL", "http://api:8000")
IDEMPOTENT = {"GET", "PUT", "DELETE"}


class Client:
    def __init__(self):
        self.token = None
        self.requests = 0

    def login(self):
        try:
            user, password = os.environ["LAB_USERNAME"], os.environ["LAB_PASSWORD"]
        except KeyError:
            sys.exit("Set LAB_USERNAME and LAB_PASSWORD in the environment first.")
        r = requests.post(f"{API}/api/v1/auth/token", json={"username": user, "password": password}, timeout=5)
        r.raise_for_status()
        self.token = r.json()["token"]

    def call(self, method, path, body=None, key=None):
        """Send one request and return the response. Retries only what is safe to retry."""
        if self.token is None:
            self.login()
        safe = method in IDEMPOTENT or key is not None
        for attempt in range(1, 7):
            headers = {"Authorization": f"Bearer {self.token}"}
            if key:
                headers["Idempotency-Key"] = key
            self.requests += 1
            try:
                r = requests.request(method, f"{API}{path}", json=body, headers=headers, timeout=5)
            except (requests.ConnectionError, requests.Timeout):
                r = None
            if r is not None and r.status_code == 401:      # not processed: log in, send again
                print("  token expired: logging in again", flush=True)
                self.login()
                continue
            if r is not None and r.status_code == 429:      # not processed: wait, send again
                print(f"  rate limited: waiting {r.headers.get('Retry-After', '1')}s", flush=True)
                time.sleep(int(r.headers.get("Retry-After", "1")))
                continue
            if r is None or r.status_code == 503:           # may or may not have been applied
                if not safe:
                    sys.exit(f"{method} {path}: no clear answer, and it is not safe to retry")
                wait = 2 ** (attempt - 1) + random.random()
                print(f"  retry {attempt}: {method} {path} {'lost reply' if r is None else '503'}, waiting {wait:.1f}s", flush=True)
                time.sleep(wait)
                continue
            return r
        sys.exit(f"{method} {path}: gave up after 6 tries")


def get_items(c, path):
    """Read a list, following 'next' links to the end."""
    items = []
    while path:
        r = c.call("GET", path)
        r.raise_for_status()
        body = r.json()
        items += body["items"]
        path = body.get("next")
        if path and path.startswith(API):
            path = path[len(API):]
    return items


def acl_key(e):
    """What makes two ACL entries 'the same': everything they say, with defaults filled in."""
    return (e["action"], e["src"], e["dst"], e.get("protocol", "any"), e.get("port"), e.get("description", ""))


def make_plan(intent, vlans, acl):
    plan = []
    want = {v["id"]: v["name"] for v in intent["vlans"]}
    for vid, name in sorted(want.items()):
        if vid not in vlans:
            plan.append(("create-vlan", vid, name))
        elif vlans[vid] != name:
            plan.append(("rename-vlan", vid, name))
    for vid in sorted(vlans):
        if vid not in want and vid != 1:
            plan.append(("delete-vlan", vid, None))
    want_acl = {acl_key(e): e for e in intent["acl"]}
    seen = set()
    for e in acl:
        k = acl_key(e)
        if k in want_acl and k not in seen:
            seen.add(k)
        else:                                   # not wanted, or a duplicate
            plan.append(("delete-acl", e["id"], k))
    for k, e in want_acl.items():
        if k not in seen:
            plan.append(("create-acl", e, k))
    return plan

def describe(step):
    kind, a, b = step
    if kind in ("create-vlan", "rename-vlan"):
        return f"{kind} {a} {b}"
    if kind == "delete-vlan":
        return f"{kind} {a}"
    k = b
    text = f"{k[0]} {k[1]} -> {k[2]} {k[3]}" + (f"/{k[4]}" if k[4] else "") + f" ({k[5]})"
    return f"{kind} {text}" + (f" [id {a}]" if kind == "delete-acl" else "")


def apply_step(c, step):
    kind, a, b = step
    if kind in ("create-vlan", "rename-vlan"):
        r = c.call("PUT", f"/api/v1/vlans/{a}", {"name": b})
        ok = (200, 201)
    elif kind == "delete-vlan":
        r = c.call("DELETE", f"/api/v1/vlans/{a}")
        ok = (204, 404)                       # 404: already gone, which is what we wanted
    elif kind == "delete-acl":
        r = c.call("DELETE", f"/api/v1/acl/entries/{a}")
        ok = (204, 404)
    else:                                     # create-acl: POST, so it needs a key
        key = str(uuid.uuid4())               # made ONCE here, reused by every retry inside call()
        r = c.call("POST", "/api/v1/acl/entries", a, key=key)
        ok = (201,)
    if r.status_code not in ok:
        sys.exit(f"{describe(step)}: unexpected {r.status_code} {r.text}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("intent")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    with open(args.intent) as f:
        intent = yaml.safe_load(f)

    c = Client()
    vlans = {v["id"]: v["name"] for v in get_items(c, "/api/v1/vlans")}
    acl = get_items(c, "/api/v1/acl/entries")
    plan = make_plan(intent, vlans, acl)

    if not plan:but 
        print("plan is empty: the API already matches the intent")
    for step in plan:
        print("plan:", describe(step))
    if args.dry_run:
        print("dry run: nothing changed")
        return
    for step in plan:
        apply_step(c, step)
        print("done:", describe(step))

    vlans = {v["id"]: v["name"] for v in get_items(c, "/api/v1/vlans")}
    acl = get_items(c, "/api/v1/acl/entries")
    left = make_plan(intent, vlans, acl)
    if left:
        for step in left:
            print("MISMATCH:", describe(step))
        sys.exit(1)
    print(f"check: the API matches the intent ({c.requests} requests)")


if __name__ == "__main__":
    main()