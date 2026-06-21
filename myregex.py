from re import Pattern, compile


class MapRegex:
    """
    Regex patterns for general map configuration lines.
    """

    NB_DRONS: Pattern[str] = compile(
        r"^\s*(?P<key>[^\s:]+)\s*:\s*(?P<value>\S+)\s*$"
    )


class ZoneRegex:
    """
    Regex patterns for basic zone attributes.
    """

    ZONE_NAME: Pattern[str] = compile(r"^([^-\s]+)$")
    ZONE_COORDINATE: Pattern[str] = compile(r"^([-+]?\d+)$")


class HubRegex(ZoneRegex):
    """
    Regex patterns specifically for parsing hub lines and metadata.
    """

    HUB_LINE: Pattern[str] = compile(
        r"^\s*(?P<type>[^:\s]+)\s*:\s*"
        r"(?P<name>\S+)\s+(?P<x>\S+)\s+"
        r"(?P<y>\S+)(?:\s+\[(?P<metadata>[^\]]*)\])?\s*$"
    )
    HUB_TYPE: Pattern[str] = compile(r"^(start_hub|end_hub|hub)$")

    HUB_METADATA: Pattern[str] = compile(
        r"^\s*(?:(?P<key>[^\s=]+)\s*=\s*(?P<value>\S+)(?:\s+|$))+\s*$"
    )
    PAIRS_KV: Pattern[str] = compile(r"(?P<key>[^\s=]+)\s*=\s*(?P<value>\S+)")


class ConnectionRegex:
    """
    Regex patterns for parsing connection lines and metadata.
    """

    CONNECTION_LINE: Pattern[str] = compile(
        r"^\s*(?P<connection>[^:\s]+)\s*:\s*(?P<zone1>[^-\s]+)\s*-\s*"
        r"(?P<zone2>\S+)"
        r"(?:\s+\[(?P<metadata>[^\]]*)\])?\s*$"
    )

    CONNECTION_METADATA: Pattern[str] = compile(
        r"^\s*(?:(?P<key>[^\s=]+)\s*=\s*(?P<value>\S+)(?:\s+|$))+\s*$"
    )
