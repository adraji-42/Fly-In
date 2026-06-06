from re import Pattern, compile


class MapRegex:
    NB_DRONS: Pattern = compile(
        r"^\s*(?P<key>[^\s:]+)\s*:\s*(?P<value>\S+)\s*$"
    )


class ZoneRegex:

    ZONE_NAME: Pattern = compile(r"^([^-]+)$")
    ZONE_COORDINATE: Pattern = compile(r"^([-+]?\d+)$")


class HubRegex(ZoneRegex):

    HUB_LINE: Pattern = compile(
        r"^\s*(?P<type>[^:\s]+)\s*:\s*"
        r"(?P<name>\S+)\s+(?P<x>\S+)\s+"
        r"(?P<y>\S+)(?:\s*\[(?P<metadata>[^\]]*)\])?\s*$"
    )
    HUB_TYPE: Pattern = compile(r"^(start_hub|end_hub|hub)$")

    HUB_METADATA: Pattern = compile(
        r"^\s*(?:(?P<key>[^\s=]+)\s*=\s*(?P<value>\S+)(?:\s+|$))+\s*$"
    )
    PAIRS_KV: Pattern = compile(r"(?P<key>[^\s=]+)\s*=\s*(?P<value>\S+)")


class ConnectionRegex:

    CONNECTION_LINE: Pattern = compile(
        r"\s*(?P<start>[^:\s]+)\s*:\s*(?P<zone1>[^-\s]+)\s*-\s*(?P<zone2>\S+)"
        r"(?:\s*\[(?P<metadata>[^\]]*)\])?\s*$"
    )

    CONNECTION_METADATA: Pattern = compile(
        r"^\s*\[\s*(?P<key>[^\s=])\s*=\s*(?P<value>\S+)\s*\]\s*$"
    )
