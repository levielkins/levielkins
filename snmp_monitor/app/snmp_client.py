import time

from pysnmp.hlapi.v3arch.asyncio import (
    CommunityData,
    ContextData,
    ObjectIdentity,
    ObjectType,
    SnmpEngine,
    UdpTransportTarget,
    get_cmd,
)

# Standard MIB-2 "system" OIDs - supported by essentially any SNMP-enabled device.
SYSTEM_OIDS = {
    "sys_descr": "1.3.6.1.2.1.1.1.0",
    "sys_uptime": "1.3.6.1.2.1.1.3.0",
    "sys_contact": "1.3.6.1.2.1.1.4.0",
    "sys_name": "1.3.6.1.2.1.1.5.0",
    "sys_location": "1.3.6.1.2.1.1.6.0",
}


async def poll_device(
    ip_address: str,
    port: int = 161,
    community: str = "public",
    snmp_version: str = "2c",
    timeout: int = 3,
    retries: int = 1,
) -> dict:
    """Poll a device via SNMP GET for reachability + basic system info.

    Returns a dict matching the PollResult model's fields.
    """
    mp_model = 0 if snmp_version == "1" else 1  # 0=SNMPv1, 1=SNMPv2c

    result = {
        "is_up": False,
        "response_time_ms": None,
        "sys_descr": None,
        "sys_uptime": None,
        "sys_contact": None,
        "sys_name": None,
        "sys_location": None,
        "error_message": None,
    }

    engine = SnmpEngine()
    started = time.monotonic()
    try:
        transport = await UdpTransportTarget.create(
            (ip_address, port), timeout=timeout, retries=retries
        )
        var_binds = [ObjectType(ObjectIdentity(oid)) for oid in SYSTEM_OIDS.values()]

        error_indication, error_status, error_index, response_binds = await get_cmd(
            engine,
            CommunityData(community, mpModel=mp_model),
            transport,
            ContextData(),
            *var_binds,
        )

        if error_indication:
            result["error_message"] = str(error_indication)
        elif error_status:
            result["error_message"] = error_status.prettyPrint()
        else:
            result["is_up"] = True
            result["response_time_ms"] = round((time.monotonic() - started) * 1000, 2)
            for key, var_bind in zip(SYSTEM_OIDS.keys(), response_binds):
                value = var_bind[1]
                result[key] = str(value).strip() if value is not None else None
    except Exception as exc:  # noqa: BLE001 - report any transport/library error as a failed poll
        result["error_message"] = str(exc)
    finally:
        engine.close_dispatcher()

    return result
