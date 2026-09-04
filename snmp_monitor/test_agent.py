"""
Standalone SNMP test agent.

Runs a tiny SNMP v1/v2c agent on 127.0.0.1 so you have a guaranteed-working
target to point the monitor app at, without needing SNMP support on your OS
or network gear. Community string is "public" (read-only).

Usage:
    python test_agent.py [port]

Default port is 1161 (no admin/root needed). If you pass a port below 1024
(e.g. the standard 161), you'll need to run this as Administrator/root.

Then in the app, add a device with:
    IP address: 127.0.0.1
    Port:       1161 (or whatever you passed)
    Version:    2c
    Community:  public

Stop with Ctrl+C.
"""

import sys

from pysnmp.entity import config, engine
from pysnmp.entity.rfc3413 import cmdrsp, context


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 1161

    snmp_engine = engine.SnmpEngine()

    transport = config.udp.UdpAsyncioTransport().open_server_mode(("127.0.0.1", port))
    config.add_transport(snmp_engine, config.udp.DOMAIN_NAME, transport)

    config.add_v1_system(snmp_engine, "test-agent", "public")

    # SNMPv2c, read-only access to the whole standard MIB-2 tree (covers
    # sysDescr/sysName/sysUpTime/etc. plus interface counters and more).
    config.add_vacm_user(
        snmp_engine,
        2,
        "test-agent",
        "noAuthNoPriv",
        readSubTree=(1, 3, 6, 1, 2, 1),
    )

    config.add_context(snmp_engine, "")

    snmp_context = context.SnmpContext(snmp_engine)

    cmdrsp.GetCommandResponder(snmp_engine, snmp_context)
    cmdrsp.NextCommandResponder(snmp_engine, snmp_context)
    cmdrsp.BulkCommandResponder(snmp_engine, snmp_context)

    print(f"Test SNMP agent listening on 127.0.0.1:{port}, community 'public' (v1/v2c)")
    print("Point the monitor app's device at this IP/port/community. Ctrl+C to stop.")

    snmp_engine.open_dispatcher()
    try:
        snmp_engine.transport_dispatcher.run_dispatcher()
    except KeyboardInterrupt:
        print("\nStopping test agent.")
    finally:
        snmp_engine.close_dispatcher()


if __name__ == "__main__":
    main()
