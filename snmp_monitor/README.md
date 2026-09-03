# SNMP Monitor

A simple SNMP-based network monitoring tool for keeping tabs on customer IPs —
think Auvik, but small enough to read in one sitting.

It polls each device over SNMP (v1/v2c) on a schedule, records whether it's
reachable and pulls its basic system info (`sysDescr`, `sysName`,
`sysContact`, `sysLocation`, `sysUpTime`), and shows the results in a web
dashboard grouped by customer.

## How it's built

- **FastAPI** + server-rendered **Jinja2** templates (no JS framework — plain
  forms and page reloads)
- **SQLAlchemy** + **SQLite** for storage (`monitor.db`, created automatically)
- **pysnmp** (asyncio) for the actual SNMP GET requests
- **APScheduler** running in the background, polling every device on its own
  configured interval

```
app/
  main.py         FastAPI app + startup (creates tables, starts scheduler)
  database.py     SQLAlchemy engine/session
  models.py       Customer, Device, PollResult
  snmp_client.py  SNMP GET against the standard MIB-2 "system" OIDs
  poller.py       decides which devices are due, records PollResult rows
  routes/         dashboard, customer, and device HTTP routes
  templates/       Jinja2 HTML templates
  static/         style.css
```

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Running

```bash
source .venv/bin/activate
uvicorn app.main:app --reload
```

Then open http://127.0.0.1:8000 — add a customer, add a device (its IP,
SNMP community string, and poll interval), and the background scheduler will
start polling it automatically. There's also a "Poll Now" button on each
device's page for an on-demand check.

## Trying it against a real target

Any device with an SNMP agent enabled and a known community string works —
switches, routers, firewalls, printers, Linux/Windows hosts with an SNMP
daemon installed. To test locally with no hardware, install `net-snmp`'s
agent and point a device at `127.0.0.1`:

```bash
sudo apt-get install snmpd
# rocommunity public default -V systemonly must be set in /etc/snmp/snmpd.conf
sudo systemctl start snmpd   # or: sudo /usr/sbin/snmpd -f
```

## Notes / limitations

This is intentionally simple:

- SNMPv1/v2c only (community-string auth) — no SNMPv3
- Polls one OID set (reachability + system info) — no interface/traffic
  counters, no CPU/memory, no alerting/notifications yet
- Single-process scheduler — fine for a handful to a few dozen devices, not
  built for fleet-scale polling
- No authentication on the web UI — don't expose it to the open internet
  as-is

All reasonable next steps if this grows: SNMPv3 support, interface
(`ifTable`) stats and graphs, alerting (email/Slack on status change), and
a proper auth layer on the dashboard.
