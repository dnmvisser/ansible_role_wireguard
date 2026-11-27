#!/usr/bin/env python3
"""Show WireGuard peer status, resolving IDs from the '# wg-peers:' line in wg0.conf.

If the line is absent (e.g. wg_stealth_mode), peers are shown by public key only.
"""
import argparse
import json
import re
import subprocess
import sys
import time

ONLINE_SECS = 180  # handshakes happen ~every 120s while traffic flows
MARKER = re.compile(r"^\s*#\s*wg-peers:\s*(\[.*\])\s*$")
PUBKEY = re.compile(r"^\s*PublicKey\s*=\s*(\S+)\s*$")


def parse_conf(conf_path):
    """Return (ids, conf_keys).

    ids:       {public_key: id} from the embedded JSON comment, or None if absent
    conf_keys: set of public keys found in [Peer] PublicKey lines
    """
    index = None
    conf_keys = set()
    with open(conf_path) as f:
        for line in f:
            m = MARKER.match(line)
            if m:
                if index is not None:
                    raise ValueError("multiple '# wg-peers:' lines found")
                index = json.loads(m.group(1))
                continue
            m = PUBKEY.match(line)
            if m:
                conf_keys.add(m.group(1))
    ids = None if index is None else {e["public_key"]: e["id"] for e in index}
    return ids, conf_keys


def read_live(iface):
    out = subprocess.run(
        ["wg", "show", iface, "dump"],
        check=True, capture_output=True, text=True,
    ).stdout.splitlines()
    peers = {}
    for line in out[1:]:  # line 0 is the interface (has the private key); skip
        pub, _psk, endpoint, allowed, hs, rx, tx, _ka = line.split("\t")
        peers[pub] = {
            "endpoint": None if endpoint == "(none)" else endpoint,
            "allowed_ips": allowed,
            "handshake": int(hs),  # epoch seconds, 0 = never
            "rx": int(rx),         # bytes received from the peer
            "tx": int(tx),         # bytes sent to the peer
        }
    return peers


def human_bytes(n):
    n = float(n)
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if n < 1024 or unit == "TiB":
            return f"{int(n)} B" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024


def human_ago(s):
    if s < 60:
        return f"{s}s ago"
    if s < 3600:
        return f"{s // 60}m ago"
    if s < 86400:
        return f"{s // 3600}h {s % 3600 // 60}m ago"
    return f"{s // 86400}d {s % 86400 // 3600}h ago"


def make_row(pid, pub, lv, now):
    if lv is None:
        return dict(id=pid, public_key=pub, status="not-loaded",
                    last_seen=None, age=None, endpoint=None,
                    allowed_ips=None, rx=0, tx=0)
    age = now - lv["handshake"] if lv["handshake"] else None
    if age is None:
        status = "never"
    elif age <= ONLINE_SECS:
        status = "online"
    else:
        status = "idle"
    return dict(id=pid, public_key=pub, status=status,
                last_seen=lv["handshake"] or None, age=age,
                endpoint=lv["endpoint"], allowed_ips=lv["allowed_ips"],
                rx=lv["rx"], tx=lv["tx"])


def build_rows(ids, live):
    now = int(time.time())
    rows = []
    if ids is None:  # no index (stealth mode): live peers only, no names
        for pub, lv in live.items():
            rows.append(make_row("(unknown)", pub, lv, now))
        return rows
    for pub, pid in ids.items():
        rows.append(make_row(pid, pub, live.get(pub), now))
    for pub, lv in live.items():
        if pub not in ids:
            rows.append(make_row("(unknown)", pub, lv, now))
    return rows


def warn_drift(ids, conf_keys):
    if ids is None:
        return
    index_keys = set(ids)
    for pub in sorted(conf_keys - index_keys):
        print(f"warning: {pub[:8]}... is in [Peer] blocks but not in the "
              f"# wg-peers index", file=sys.stderr)
    for pub in sorted(index_keys - conf_keys):
        print(f"warning: {ids[pub]} ({pub[:8]}...) is in the # wg-peers "
              f"index but has no [Peer] block", file=sys.stderr)


def print_table(rows):
    headers = ["ID", "KEY", "STATUS", "LAST SEEN", "ENDPOINT",
               "ALLOWED IPS", "RX", "TX"]
    table = [[
        r["id"], r["public_key"][:8] + "...", r["status"],
        human_ago(r["age"]) if r["age"] is not None else "-",
        r["endpoint"] or "-", r["allowed_ips"] or "-",
        human_bytes(r["rx"]), human_bytes(r["tx"]),
    ] for r in rows]
    widths = [max(len(str(x)) for x in col) for col in zip(headers, *table)]
    for row in [headers] + table:
        print("  ".join(str(c).ljust(w) for c, w in zip(row, widths)).rstrip())


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("-i", "--interface", default="wg0")
    ap.add_argument("-c", "--conf", help="default: /etc/wireguard/<iface>.conf")
    ap.add_argument("--json", action="store_true", help="output JSON")
    args = ap.parse_args()
    conf = args.conf or f"/etc/wireguard/{args.interface}.conf"

    try:
        ids, conf_keys = parse_conf(conf)
        live = read_live(args.interface)
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as e:
        sys.exit(f"error: {e!r} (are you root?)")

    warn_drift(ids, conf_keys)
    rows = build_rows(ids, live)
    if args.json:
        json.dump(rows, sys.stdout, indent=2)
        print()
    else:
        print_table(rows)


if __name__ == "__main__":
    main()
