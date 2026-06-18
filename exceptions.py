from dataclasses import dataclass


@dataclass(frozen=True)
class ErrorInfo:
    line_number: int
    line_content: str
    error_start: int
    error_end: int
    reason: str
    expected: str
    how_to_fix: str


class BaseMapProjectError(Exception):
    def __init__(self, info: ErrorInfo) -> None:
        self.info = info
        super().__init__(str(self))


class MapLogicError(BaseMapProjectError):
    def __str__(self) -> str:
        i = self.info
        return (
            f"invalid line numbered {i.line_number}\n"
            f"the reason is {i.reason}\n"
            f"expected is {i.expected}\n"
            f"how to fix it {i.how_to_fix}"
        )


class MapFormatError(BaseMapProjectError):
    def __str__(self) -> str:
        i = self.info
        s = max(0, min(i.error_start, len(i.line_content)))
        e = max(s, min(i.error_end, len(i.line_content)))
        lc = i.line_content
        styled = (
            f"\x1b[31m{lc[:s]}"
            f"\x1b[37;41m{lc[s:e]}\x1b[0m"
            f"\x1b[31m{lc[e:]}\x1b[0m"
        )
        return (
            f"invalid line numbered {i.line_number}, "
            f"line: {styled}\n"
            f"the reason is {i.reason}\n"
            f"expected {i.expected}\n"
            f"to fix it {i.how_to_fix}"
        )


class HubLineInspector:
    @staticmethod
    def inspect(
        line: str, line_number: int
    ) -> ErrorInfo:
        stripped = line.strip()
        colon_idx = stripped.find(":")
        prefix = line.find(stripped)

        if colon_idx == -1:
            return ErrorInfo(
                line_number=line_number,
                line_content=line,
                error_start=0,
                error_end=len(line),
                reason=(
                    "hub line is missing the colon separator"
                ),
                expected="hub_type: name x y [metadata]",
                how_to_fix=(
                    "add a colon after the hub type keyword"
                ),
            )

        rest = stripped[colon_idx + 1:].strip()
        bracket_idx = rest.find("[")
        if bracket_idx != -1:
            before_bracket = rest[:bracket_idx].strip()
        else:
            before_bracket = rest

        tokens = before_bracket.split() if before_bracket else []

        if len(tokens) == 0:
            err_start = prefix + colon_idx + 1
            return ErrorInfo(
                line_number=line_number,
                line_content=line,
                error_start=err_start,
                error_end=len(line),
                reason=(
                    "hub name and coordinates are missing"
                ),
                expected="name x y after the colon",
                how_to_fix=(
                    "add a hub name followed by"
                    " x and y coordinates"
                ),
            )

        if len(tokens) < 3:
            last_token = tokens[-1]
            last_pos = line.find(
                last_token, prefix + colon_idx
            )
            err_start = last_pos + len(last_token)
            return ErrorInfo(
                line_number=line_number,
                line_content=line,
                error_start=err_start,
                error_end=max(
                    err_start + 1, len(line.rstrip())
                ),
                reason=(
                    "the hub must have coordinates"
                    " x and y after name"
                    if len(tokens) == 1
                    else "the hub is missing the y coordinate"
                ),
                expected="hub_type: name x y [metadata]",
                how_to_fix=(
                    "add the missing coordinate(s)"
                    " after the hub name"
                ),
            )

        if "[" in rest and "]" not in rest:
            bracket_pos = line.find("[")
            return ErrorInfo(
                line_number=line_number,
                line_content=line,
                error_start=bracket_pos,
                error_end=len(line),
                reason="metadata bracket is not closed",
                expected=(
                    "matching ] to close the metadata block"
                ),
                how_to_fix="add a closing ] bracket",
            )

        return ErrorInfo(
            line_number=line_number,
            line_content=line,
            error_start=0,
            error_end=len(line),
            reason="hub line format is invalid",
            expected="hub_type: name x y [metadata]",
            how_to_fix=(
                "rewrite the line using"
                " the correct hub format"
            ),
        )


class HubMetadataInspector:
    @staticmethod
    def inspect(
        line: str, metadata: str,
        line_number: int, metadata_offset: int
    ) -> ErrorInfo:
        stripped = metadata.strip()

        if not stripped:
            bs = line.find("[")
            be = line.find("]", bs) + 1 if bs >= 0 else 0
            return ErrorInfo(
                line_number=line_number,
                line_content=line,
                error_start=bs if bs >= 0 else 0,
                error_end=max(be, (bs + 1) if bs >= 0 else 0),
                reason="the metadata block is empty",
                expected=(
                    "key=value pairs or no brackets at all"
                ),
                how_to_fix=(
                    "remove the empty brackets or add metadata"
                ),
            )

        if "=" not in stripped:
            pos = line.find(stripped, metadata_offset)
            if pos == -1:
                pos = metadata_offset
            return ErrorInfo(
                line_number=line_number,
                line_content=line,
                error_start=pos,
                error_end=pos + len(stripped),
                reason=(
                    "metadata is missing the = separator"
                ),
                expected=(
                    "key=value pairs like zone=normal"
                ),
                how_to_fix=(
                    "add = between key and value in metadata"
                ),
            )

        pos = line.find(stripped, metadata_offset)
        if pos == -1:
            pos = metadata_offset
        return ErrorInfo(
            line_number=line_number,
            line_content=line,
            error_start=pos,
            error_end=pos + len(stripped),
            reason="the metadata format is invalid",
            expected="space-separated key=value pairs",
            how_to_fix=(
                "rewrite metadata as key=value pairs"
            ),
        )


class ConnectionLineInspector:
    @staticmethod
    def inspect(
        line: str, line_number: int
    ) -> ErrorInfo:
        stripped = line.strip()
        colon_idx = stripped.find(":")
        prefix = line.find(stripped)

        if colon_idx == -1:
            return ErrorInfo(
                line_number=line_number,
                line_content=line,
                error_start=0,
                error_end=len(line),
                reason=(
                    "connection line is missing"
                    " the colon separator"
                ),
                expected=(
                    "connection: zone1-zone2 [metadata]"
                ),
                how_to_fix=(
                    "add a colon after"
                    " the connection keyword"
                ),
            )

        rest = stripped[colon_idx + 1:].strip()

        if not rest:
            err_start = prefix + colon_idx + 1
            return ErrorInfo(
                line_number=line_number,
                line_content=line,
                error_start=err_start,
                error_end=len(line),
                reason="connection zones are missing",
                expected="zone1-zone2 after the colon",
                how_to_fix=(
                    "add two zone names separated by a dash"
                ),
            )

        before_bracket = rest.split("[")[0].strip()
        if "-" not in before_bracket:
            pos = line.find(
                before_bracket, prefix + colon_idx
            )
            if pos == -1:
                pos = prefix + colon_idx + 1
            return ErrorInfo(
                line_number=line_number,
                line_content=line,
                error_start=pos,
                error_end=pos + len(before_bracket),
                reason=(
                    "connection is missing"
                    " the dash separator"
                ),
                expected="zone1-zone2",
                how_to_fix=(
                    "separate the two zone names with a dash"
                ),
            )

        return ErrorInfo(
            line_number=line_number,
            line_content=line,
            error_start=0,
            error_end=len(line),
            reason="connection line format is invalid",
            expected=(
                "connection: zone1-zone2 [metadata]"
            ),
            how_to_fix=(
                "rewrite the line using"
                " the correct connection format"
            ),
        )


class ConnectionMetadataInspector:
    @staticmethod
    def inspect(
        line: str, metadata: str,
        line_number: int, metadata_offset: int
    ) -> ErrorInfo:
        stripped = metadata.strip()

        if not stripped:
            bs = line.find("[")
            be = line.find("]", bs) + 1 if bs >= 0 else 0
            return ErrorInfo(
                line_number=line_number,
                line_content=line,
                error_start=bs if bs >= 0 else 0,
                error_end=max(be, (bs + 1) if bs >= 0 else 0),
                reason="the metadata block is empty",
                expected=(
                    "max_link_capacity=<positive integer>"
                ),
                how_to_fix=(
                    "remove the empty brackets or"
                    " add metadata"
                ),
            )

        if "=" not in stripped:
            pos = line.find(stripped, metadata_offset)
            if pos == -1:
                pos = metadata_offset
            return ErrorInfo(
                line_number=line_number,
                line_content=line,
                error_start=pos,
                error_end=pos + len(stripped),
                reason=(
                    "metadata is missing the = separator"
                ),
                expected=(
                    "max_link_capacity=<positive integer>"
                ),
                how_to_fix=(
                    "add = between key and value in metadata"
                ),
            )

        pos = line.find(stripped, metadata_offset)
        if pos == -1:
            pos = metadata_offset
        return ErrorInfo(
            line_number=line_number,
            line_content=line,
            error_start=pos,
            error_end=pos + len(stripped),
            reason="the metadata format is invalid",
            expected=(
                "max_link_capacity=<positive integer>"
            ),
            how_to_fix=(
                "rewrite as max_link_capacity=<number>"
            ),
        )


class NbDronesLineInspector:
    @staticmethod
    def inspect(
        line: str, line_number: int
    ) -> ErrorInfo:
        stripped = line.strip()

        if ":" not in stripped:
            return ErrorInfo(
                line_number=line_number,
                line_content=line,
                error_start=0,
                error_end=len(line),
                reason=(
                    "the line is missing"
                    " the colon separator"
                ),
                expected="nb_drones: <positive integer>",
                how_to_fix=(
                    "rewrite as nb_drones: <number>"
                ),
            )

        return ErrorInfo(
            line_number=line_number,
            line_content=line,
            error_start=0,
            error_end=len(line),
            reason=(
                "the line does not match"
                " the drone count format"
            ),
            expected="nb_drones: <positive integer>",
            how_to_fix="rewrite as nb_drones: <number>",
        )
