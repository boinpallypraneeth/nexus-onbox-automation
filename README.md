# Nexus On-Box Automation

On-device network automation projects built and tested on a Cisco Nexus 93180YC-EX switch.

All automation runs **entirely inside the switch** — using NX-OS Guest Shell and Embedded Event Manager (EEM). No external servers, no Ansible, no management laptops required.

**Author:** Praneeth Boinpally

---

## Projects

### 1. Config Drift Auditor

**File:** `scripts/config_auditor.py`

A Python script that runs inside NX-OS Guest Shell on a cron schedule, comparing the live running-config against a known-good baseline and logging any deviations with timestamps to bootflash.

**How it works:**
- Pulls live running-config via `/isan/bin/vsh`
- Filters dynamic NX-OS lines (`!Time:`, `!Command:`) to prevent false positives
- Uses Python `difflib` to compare against baseline
- Logs all changes with timestamps to `/bootflash/config_audit_log.txt`
- Runs every 5 minutes via cron — fully autonomous

**Tested drift scenarios:**
- Interface description changes
- VLAN additions
- ACL creation

**Sample output:**
```
[2026-04-03 00:19:04] --- Audit started ---
[2026-04-03 00:19:04] DRIFT DETECTED: 32 changed lines
[2026-04-03 00:19:04] +vlan 999
[2026-04-03 00:19:04] +  name DRIFT_VLAN_TEST
[2026-04-03 00:19:04] --- Audit complete ---

[2026-04-03 00:57:22] --- Audit started ---
[2026-04-03 00:57:27] PASS: No config drift detected.
[2026-04-03 00:57:27] --- Audit complete ---
```

**Deployment:**
```bash
# 1. Save baseline from NX-OS CLI
show running-config > bootflash:baseline_config.txt

# 2. Enter Guest Shell
guestshell

# 3. Deploy script
cat > /bootflash/config_auditor.py << 'ENDOFFILE'
<paste script here>
ENDOFFILE

# 4. Test manually
python3 /bootflash/config_auditor.py

# 5. Schedule via cron
crontab -e
# Add: */5 * * * * python3 /bootflash/config_auditor.py
```

---

### 2. EEM Err-Disable Recovery + Logger

**File:** `scripts/errdisable_log.py`

An NX-OS EEM applet that triggers automatically when any interface enters an err-disabled state. Captures affected ports and invokes an on-box Python logger via Guest Shell for a persistent audit trail.

**How it works:**
- EEM monitors syslog for pattern `.*err-disabled.*`
- On match: captures affected interfaces, enters config mode for remediation
- Calls Guest Shell Python logger as action 5.0
- Logger writes timestamped event to `/bootflash/errdisable_log.txt`

**Sample output:**
```
[2026-04-03 01:21:39] === ERR-DISABLE EVENT DETECTED ===
[2026-04-03 01:21:40] Affected ports: Ethernet1/5    err-disabled
[2026-04-03 01:21:40] Auto-recovery triggered by EEM
[2026-04-03 01:21:40] === END EVENT ===
```

**Deployment:**

Step 1 — Configure EEM applet on NX-OS CLI:
```
configure terminal

event manager applet ERR_DISABLE_RECOVERY
  event syslog pattern ".*err-disabled.*"
  action 1.0 cli command "enable"
  action 2.0 cli command "show interface | include err-disabled"
  action 3.0 cli command "configure terminal"
  action 4.0 cli command "end"
  action 5.0 cli command "guestshell run python3 /bootflash/errdisable_log.py"
end
```

Step 2 — Deploy Python logger inside Guest Shell:
```bash
guestshell
cat > /bootflash/errdisable_log.py << 'ENDOFFILE'
<paste script here>
ENDOFFILE

# Test manually
python3 /bootflash/errdisable_log.py
```

Step 3 — Verify EEM applet is active:
```
show event manager policy internal
```

---

## Platform Notes

| Detail | Value |
|---|---|
| Hardware | Cisco Nexus 93180YC-EX |
| Python version | 3.6 (Guest Shell) |
| vsh location | `/isan/bin/vsh` |
| Storage | `/bootflash` (persistent) |

**Important for Python 3.6 compatibility:**
- Use `stdout=subprocess.PIPE` instead of `capture_output=True`
- Use `.format()` instead of f-strings
- `vsh` is not in default PATH — use full path `/isan/bin/vsh`

---

## Troubleshooting

| Issue | Fix |
|---|---|
| `FileNotFoundError: vsh` | Use full path `/isan/bin/vsh` |
| `capture_output` TypeError | Replace with `stdout=subprocess.PIPE, stderr=subprocess.PIPE` |
| False-positive drift on every run | Add `!Time:` to filter_lines() skip list |
| SyntaxError: `:wq` in script | Use `cat heredoc` method instead of vi for pasting code |

---

## Screenshots

See `screenshots/` folder for terminal output from actual device runs.

---

## License

MIT
