#!/usr/bin/env python3
"""
config_auditor.py
-----------------
On-box NX-OS configuration drift detector.
Runs inside Guest Shell on Cisco Nexus switches.

- Compares live running-config against a known-good baseline
- Filters dynamic NX-OS lines (timestamps) to prevent false positives
- Logs all deviations with timestamps to bootflash

Schedule via cron inside Guest Shell:
    */5 * * * * python3 /bootflash/config_auditor.py

Author: Praneeth Boinpally
"""

import subprocess
import difflib
import datetime
import os

BASELINE_PATH = "/bootflash/baseline_config.txt"
LOG_PATH      = "/bootflash/config_audit_log.txt"
LIVE_SNAP     = "/bootflash/live_config_snap.txt"
VSH           = "/isan/bin/vsh"


def get_live_config():
    """Pull running config via vsh (NX-OS shell inside Guest Shell)."""
    result = subprocess.run(
        [VSH, "-c", "show running-config"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    return result.stdout.decode("utf-8")


def filter_lines(lines):
    """Filter out dynamic NX-OS lines that change every run."""
    skip = ["!Time:", "!Command:"]
    return [l for l in lines if not any(l.strip().startswith(s) for s in skip)]


def read_file(path):
    with open(path, "r") as f:
        return f.readlines()


def write_file(path, content):
    with open(path, "w") as f:
        f.write(content)


def log(message):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = "[{}] {}\n".format(timestamp, message)
    with open(LOG_PATH, "a") as f:
        f.write(entry)
    print(entry.strip())


def run_audit():
    if not os.path.exists(BASELINE_PATH):
        log("ERROR: Baseline config not found at " + BASELINE_PATH)
        return

    log("--- Audit started ---")

    live = get_live_config()
    write_file(LIVE_SNAP, live)

    baseline_lines = filter_lines(read_file(BASELINE_PATH))
    live_lines     = filter_lines(read_file(LIVE_SNAP))

    diff = list(difflib.unified_diff(
        baseline_lines,
        live_lines,
        fromfile="baseline",
        tofile="live",
        lineterm=""
    ))

    if not diff:
        log("PASS: No config drift detected.")
    else:
        log("DRIFT DETECTED: {} changed lines".format(len(diff)))
        for line in diff:
            line = line.strip()
            if line.startswith("+") or line.startswith("-"):
                log(line)

    log("--- Audit complete ---\n")


if __name__ == "__main__":
    run_audit()
