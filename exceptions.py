from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ErrorInfo:
    """
    Data class representing details about a parsing error.

    Attributes:
        line_number (int): The line number where the error occurred.
        line_content (str): The raw string content of the line.
        error_start (int): The starting index of the error in the line.
        error_end (int): The ending index of the error in the line.
        reason (str): The reason why the error occurred.
        expected (str): What was expected instead.
        how_to_fix (str): Suggestion on how to fix the error.
    """

    line_number: int
    line_content: str
    error_start: int
    error_end: int
    reason: str
    expected: str
    how_to_fix: str


class BaseMapProjectError(Exception):
    """
    Base exception class for all custom exceptions in this project.
    """

    def __init__(self, info: ErrorInfo) -> None:
        """
        Initializes the base error.

        Args:
            info (ErrorInfo): Detailed information about the error.
        """
        self.info = info
        super().__init__(str(self))


class MapLogicError(BaseMapProjectError):
    """
    Exception raised for logical errors in the map definition (e.g., duplicate
    names, self-loops).
    """

    def __str__(self) -> str:
        """
        Returns a formatted string describing the logic error.

        Returns:
            str: The error message.
        """
        return (
            f"invalid line numbered {self.info.line_number}\n"
            f"the reason is {self.info.reason}\n"
            f"expected is {self.info.expected}\n"
            f"how to fix it {self.info.how_to_fix}"
        )


class MapFormatError(BaseMapProjectError):
    """
    Exception raised for formatting and syntax errors in the map file.
    """

    def __str__(self) -> str:
        """
        Returns a formatted string describing the format error, with ANSI
        styling indicating the location.

        Returns:
            str: The styled error message.
        """
        s = max(0, min(self.info.error_start, len(self.info.line_content)))
        e = max(s, min(self.info.error_end, len(self.info.line_content)))
        styled = (
            f"\x1b[31m{self.info.line_content[:s]}"
            f"\x1b[37;41m{self.info.line_content[s:e]}\x1b[0m"
            f"\x1b[31m{self.info.line_content[e:]}\x1b[0m"
        )
        return (
            f"invalid line numbered {self.info.line_number}, "
            f"line: {styled}\n"
            f"the reason is {self.info.reason}\n"
            f"expected {self.info.expected}\n"
            f"to fix it {self.info.how_to_fix}"
        )


class HubLineInspector:
    """
    Inspector to analyze malformed hub lines and provide specific error
    details.
    """

    @staticmethod
    def inspect(line: str, line_number: int) -> ErrorInfo:
        """
        Inspects a broken hub line to diagnose the formatting error.

        Args:
            line (str): The malformed line.
            line_number (int): The line number.

        Returns:
            ErrorInfo: Detailed diagnostics of the error.
        """
        stripped = line.strip()
        colon_idx = stripped.find(":")
        prefix = line.find(stripped)

        if colon_idx == -1:
            return ErrorInfo(
                line_number=line_number,
                line_content=line,
                error_start=0,
                error_end=len(line),
                reason=("hub line is missing the colon separator ':'"),
                expected="hub_type: name x y [metadata]",
                how_to_fix=("add a colon after the hub type keyword"),
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
                reason=("hub name and coordinates are missing"),
                expected="name x y after the colon",
                how_to_fix=(
                    "add a hub name followed by x and y coordinates"
                ),
            )

        if len(tokens) < 3:
            return ErrorInfo(
                line_number=line_number,
                line_content=line,
                error_start=-1,
                error_end=-1,
                reason=(
                    "the hub must have coordinates x and y after name"
                    if len(tokens) == 1
                    else "the hub is missing the y coordinate"
                ),
                expected="hub_type: name x y [metadata: key=value ...]",
                how_to_fix=(
                    "add the missing coordinate(s) after the hub name"
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
                expected=("matching ] to close the metadata block"),
                how_to_fix="add a closing ] bracket",
            )

        return ErrorInfo(
            line_number=line_number,
            line_content=line,
            error_start=0,
            error_end=len(line),
            reason="hub line format is invalid",
            expected="hub_type: name x y [metadata: key=value ...]",
            how_to_fix=("rewrite the line using the correct hub format"),
        )


class HubMetadataInspector:
    """
    Inspector to analyze malformed hub metadata blocks and provide error
    details.
    """

    @staticmethod
    def inspect(
        line: str, metadata: str, line_number: int, metadata_offset: int
    ) -> ErrorInfo:
        """
        Inspects a broken hub metadata block to diagnose the formatting error.

        Args:
            line (str): The malformed line.
            metadata (str): The malformed metadata string.
            line_number (int): The line number.
            metadata_offset (int): The character offset of the metadata in the
                line.

        Returns:
            ErrorInfo: Detailed diagnostics of the error.
        """
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
                expected=("key=value pairs or no brackets at all"),
                how_to_fix=("remove the empty brackets or add metadata"),
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
                reason=("metadata is missing the = separator"),
                expected=("key=value pairs like zone=normal"),
                how_to_fix=("add = between key and value in metadata"),
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
            expected="pairs of key=value separated by spaces",
            how_to_fix=("rewrite metadata as key=value pairs"),
        )


class ConnectionLineInspector:
    """
    Inspector to analyze malformed connection lines and provide specific error
    details.
    """

    @staticmethod
    def inspect(line: str, line_number: int) -> ErrorInfo:
        """
        Inspects a broken connection line to diagnose the formatting error.

        Args:
            line (str): The malformed line.
            line_number (int): The line number.

        Returns:
            ErrorInfo: Detailed diagnostics of the error.
        """
        stripped = line.strip()
        colon_idx = stripped.find(":")
        prefix = line.find(stripped)

        if colon_idx == -1:
            return ErrorInfo(
                line_number=line_number,
                line_content=line,
                error_start=0,
                error_end=len(line),
                reason=("connection line is missing the colon separator"),
                expected=("connection: zone1-zone2 [metadata: key=value ...]"),
                how_to_fix=("add a colon after the connection keyword"),
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
                how_to_fix=("add two zone names separated by a dash"),
            )

        before_bracket = rest.split("[")[0].strip()
        if "-" not in before_bracket:
            pos = line.find(before_bracket, prefix + colon_idx)
            if pos == -1:
                pos = prefix + colon_idx + 1
            return ErrorInfo(
                line_number=line_number,
                line_content=line,
                error_start=pos,
                error_end=pos + len(before_bracket),
                reason=("connection is missing the dash separator"),
                expected="zone1-zone2",
                how_to_fix=("separate the two zone names with a dash"),
            )

        return ErrorInfo(
            line_number=line_number,
            line_content=line,
            error_start=0,
            error_end=len(line),
            reason="connection line format is invalid",
            expected=("connection: zone1-zone2 [metadata: key=value ...]"),
            how_to_fix=(
                "rewrite the line using the correct connection format"
            ),
        )


class ConnectionMetadataInspector:
    """
    Inspector to analyze malformed connection metadata blocks and provide error
    details.
    """

    @staticmethod
    def inspect(
        line: str, metadata: str, line_number: int, metadata_offset: int
    ) -> ErrorInfo:
        """
        Inspects a broken connection metadata block to diagnose the formatting
        error.

        Args:
            line (str): The malformed line.
            metadata (str): The malformed metadata string.
            line_number (int): The line number.
            metadata_offset (int): The character offset of the metadata in the
                line.

        Returns:
            ErrorInfo: Detailed diagnostics of the error.
        """
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
                expected=("max_link_capacity=<positive integer>"),
                how_to_fix=("remove the empty brackets or add metadata"),
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
                reason=("metadata is missing the = separator"),
                expected=("max_link_capacity=<positive integer>"),
                how_to_fix=("add = between key and value in metadata"),
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
            expected=("max_link_capacity=<positive integer>"),
            how_to_fix=("rewrite as max_link_capacity=<number>"),
        )


class NbDronesLineInspector:
    """
    Inspector to analyze malformed nb_drones lines and provide specific error
    details.
    """

    @staticmethod
    def inspect(line: str, line_number: int) -> ErrorInfo:
        """
        Inspects a broken nb_drones line to diagnose the formatting error.

        Args:
            line (str): The malformed line.
            line_number (int): The line number.

        Returns:
            ErrorInfo: Detailed diagnostics of the error.
        """
        stripped = line.strip()

        if ":" not in stripped:
            return ErrorInfo(
                line_number=line_number,
                line_content=line,
                error_start=0,
                error_end=len(line),
                reason=("the line is missing the colon separator"),
                expected="nb_drones: <positive integer>",
                how_to_fix=("rewrite as nb_drones: <number>"),
            )

        return ErrorInfo(
            line_number=line_number,
            line_content=line,
            error_start=0,
            error_end=len(line),
            reason=("the line does not match the drone count format"),
            expected="nb_drones: <positive integer>",
            how_to_fix="rewrite as nb_drones: <number>",
        )
