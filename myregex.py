from re import Pattern, compile


class MapRegex:
    NB_DRONS: Pattern[str] = compile(
        r"^\s*(?P<key>[^\s:]+)\s*:\s*(?P<value>\S+)\s*$"
    )


class ZoneRegex:

    ZONE_NAME: Pattern[str] = compile(r"^([^-\s]+)$")
    ZONE_COORDINATE: Pattern[str] = compile(r"^([-+]?\d+)$")


class HubRegex(ZoneRegex):

    HUB_LINE: Pattern[str] = compile(
        r"^\s*(?P<type>[^:\s]+)\s*:\s*"
        r"(?P<name>\S+)\s+(?P<x>\S+)\s+"
        r"(?P<y>\S+)(?:\s*\[(?P<metadata>[^\]]*)\])?\s*$"
    )
    HUB_TYPE: Pattern[str] = compile(r"^(start_hub|end_hub|hub)$")

    HUB_METADATA: Pattern[str] = compile(
        r"^\s*(?:(?P<key>[^\s=]+)\s*=\s*(?P<value>\S+)(?:\s+|$))+\s*$"
    )
    PAIRS_KV: Pattern[str] = compile(r"(?P<key>[^\s=]+)\s*=\s*(?P<value>\S+)")


class ConnectionRegex:

    CONNECTION_LINE: Pattern[str] = compile(
        r"^\s*connection\s*:\s*(?P<zone1>[^-\s]+)\s*-\s*"
        r"(?P<zone2>[^\s\[]+)"
        r"(?:\s*\[(?P<metadata>[^\]]*)\])?\s*$"
    )

    CONNECTION_METADATA: Pattern[str] = compile(
        r"^\s*(?P<key>[^\s=]+)\s*=\s*(?P<value>\S+)\s*$"
    )
