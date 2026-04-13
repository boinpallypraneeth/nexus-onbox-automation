#!/usr/bin/env python3
"""
errdisable_log.py
-----------------
On-box err-disabled port event logger.
Called by NX-OS EEM applet when an err-disabled syslog event fires.

- Captures affected interfaces at time of event
- Logs event with timestamp to bootflash
- Works in conjunction with EEM applet ERR_DISABLE_RECOVERY

EEM Applet config (paste on NX-OS CLI):
    event manager applet ERR_DISABLE_RECOVERY
      event syslog pattern ".*err-disabled.*"
      action 1.0 cli command "enable"
      action 2.0 cli command "show interface | include err-disabled"
      action 3.0 cli command "configure terminal"
      action 4.0 cli command "end"
      action 5.0 cli command "guestshell run python3 /bootflash/errdisable_log.py"

Author: Praneeth Boinpally
"""

import subprocess
import datetime

LOG_PATH = "/bootflash/errdisable_log.txt"
VSH      = "/isan/bin/vsh"


def log(message):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = "[{}] {}\n".format(timestamp, message)
    with open(LOG_PATH, "a") as f:
        f.write(entry)
    print(entry.strip())


def get_errdisabled():
    """Capture any currently err-disabled interfaces."""
    result = subprocess.run(
        [VSH, "-c", "show interface | include err-disabled"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    return result.stdout.decode("utf-8").strip()


def main():
    log("=== ERR-DISABLE EVENT DETECTED ===")
    ports = get_errdisabled()
    if ports:
        log("Affected ports: {}".format(ports))
    else:
        log("No err-disabled ports found at time of logging")
    log("Auto-recovery triggered by EEM")
    log("=== END EVENT ===\n")


if __name__ == "__main__":
    main()
