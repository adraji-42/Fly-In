from dataclasses import dataclass
from enum import StrEnum
from re import Pattern, compile
from typing import Callable, Optional, Tuple
from mytyping import ZoneType
from regex import ConnectionRegex, MapRegex


class Color(StrEnum):
    RED = "\033[31m"
    RED_BG = "\033[41m"
    RESET = "\033[0m"


@dataclass(frozen=True)
class TextSpan:
    start: Optional[int]
    end: Optional[int]

    @classmethod
    def unknown(cls) -> "TextSpan":
        return cls(None, None)

    @classmethod
    def whole(cls, text: str) -> "TextSpan":
        return cls(0, len(text))

    @property
    def is_known(self) -> bool:
        return self.start is not None and self.end is not None

    def shifted(self, offset: Optional[int]) -> "TextSpan":
        if offset is None or not self.is_known:
            return TextSpan.unknown()
        return TextSpan(self.start + offset, self.end + offset)

    def normalized_for(self, text: str) -> "TextSpan":
        if not self.is_known:
            return TextSpan.whole(text)
        start = max(0, min(self.start, len(text)))
        end = max(start + 1, min(self.end, len(text))) if text else 0
        return TextSpan(start, end)


class TextHighlighter:
    def __init__(self, color: Color = Color.RED_BG) -> None:
        self.color = color

    def highlight(self, text: str, span: TextSpan) -> str:
        span = span.normalized_for(text)
        return (
            f"{text[:span.start]}{self.color}"
            f"{text[span.start:span.end]}{Color.RESET}{text[span.end:]}"
        )


class BadPositionFinder:
    def __call__(self, line: str, part: str) -> Tuple[int, int]:
        cleaned_part = part.strip()
        position = line.find(cleaned_part)
        return position, position + len(cleaned_part)


GET_BAD_POSITION: Callable[[str, str], Tuple[int, int]] = BadPositionFinder()


@dataclass(frozen=True)
class SourceContext:
    line: Optional[str] = None
    metadata: Optional[str] = None
    line_number: Optional[int] = None

    def locate_metadata(self) -> TextSpan:
        if self.line is None or self.metadata is None or self.metadata == "":
            return TextSpan.unknown()

        position = self.line.find(self.metadata)
        if position == -1:
            stripped = self.metadata.strip()
            position = self.line.find(stripped)
            if position == -1:
                return TextSpan.unknown()
            return TextSpan(position, position + len(stripped))
        return TextSpan(position, position + len(self.metadata))


@dataclass(frozen=True)
class ParsingProblem:
    span: TextSpan
    reason: str
    expected: str
    fix: str
    exact: bool


class HubMetadataProblemLocator:
    valid_keys = {"zone", "color", "max_drones"}
    valid_zones = {z_type.value for z_type in ZoneType}

    def __init__(self, metadata: str) -> None:
        self.metadata = metadata or ""
        self.index = 0

    def locate(self) -> ParsingProblem:
        if not self.metadata.strip():
            return ParsingProblem(
                TextSpan.whole(self.metadata),
                "the metadata block is empty.",
                "at least one key=value pair or no metadata block at all.",
                "remove the empty brackets or add metadata such as zone=normal.",
                False,
            )

        while self.index < len(self.metadata):
            self._skip_spaces()
            if self.index >= len(self.metadata):
                break

            key_start = self.index
            key = self._read_key()
            key_span = TextSpan(key_start, self.index)

            if not key:
                return ParsingProblem(
                    TextSpan(self.index, min(self.index + 1, len(self.metadata))),
                    "a metadata key is missing before '='.",
                    "a key named zone, color, or max_drones.",
                    "add a valid key before the equals sign.",
                    True,
                )

            self._skip_spaces()
            if self.index >= len(self.metadata) or self.metadata[self.index] != "=":
                return ParsingProblem(
                    key_span,
                    f"'{key}' is not followed by '='.",
                    f"'{key}=<value>' with no missing equals sign.",
                    "insert '=' between the key and its value.",
                    True,
                )

            self.index += 1
            self._skip_spaces()
            if self.index >= len(self.metadata):
                return ParsingProblem(
                    TextSpan(max(0, self.index - 1), len(self.metadata)),
                    f"'{key}' has no value.",
                    "a non-empty value after '='.",
                    "add a value after the equals sign.",
                    True,
                )

            value_start = self.index
            value = self._read_value()
            value_span = TextSpan(value_start, self.index)
            invalid = self._validate_pair(key, value, key_span, value_span)
            if invalid is not None:
                return invalid

        return ParsingProblem(
            TextSpan.whole(self.metadata),
            "the metadata does not match the required format.",
            "space-separated key=value pairs.",
            "rewrite the metadata as key=value pairs, for example zone=normal color=blue max_drones=2.",
            False,
        )

    def _skip_spaces(self) -> None:
        while self.index < len(self.metadata) and self.metadata[self.index].isspace():
            self.index += 1

    def _read_key(self) -> str:
        start = self.index
        while (
            self.index < len(self.metadata)
            and not self.metadata[self.index].isspace()
            and self.metadata[self.index] != "="
        ):
            self.index += 1
        return self.metadata[start:self.index]

    def _read_value(self) -> str:
        start = self.index
        while self.index < len(self.metadata) and not self.metadata[self.index].isspace():
            self.index += 1
        return self.metadata[start:self.index]

    def _validate_pair(
        self,
        key: str,
        value: str,
        key_span: TextSpan,
        value_span: TextSpan,
    ) -> Optional[ParsingProblem]:
        if key not in self.valid_keys:
            return ParsingProblem(
                key_span,
                f"'{key}' is not a supported hub metadata key.",
                "one of: zone, color, max_drones.",
                "rename the key to a supported metadata key or remove it.",
                True,
            )
        if key == "zone" and value not in self.valid_zones:
            return ParsingProblem(
                value_span,
                f"'{value}' is not a valid zone.",
                "one of: normal, blocked, restricted, priority.",
                "replace the zone value with one of the allowed zone names.",
                True,
            )
        if key == "color" and not value.isalpha():
            return ParsingProblem(
                value_span,
                f"'{value}' is not a valid color value.",
                "letters only, such as blue or red.",
                "remove digits, punctuation, or spaces from the color value.",
                True,
            )
        if key == "max_drones":
            try:
                int(value)
            except ValueError:
                return ParsingProblem(
                    value_span,
                    f"'{value}' is not a valid max_drones value.",
                    "an integer, such as 1 or 5.",
                    "replace max_drones with a whole number.",
                    True,
                )
        return None


class ConnectionMetadataProblemLocator:
    metadata_regex: Pattern = ConnectionRegex.CONNECTION_METADATA

    def __init__(self, metadata: str) -> None:
        self.metadata = metadata or ""

    def locate(self) -> ParsingProblem:
        if not self.metadata.strip():
            return ParsingProblem(
                TextSpan.whole(self.metadata),
                "the metadata block is empty.",
                "max_link_capacity=<positive integer> or no metadata block at all.",
                "remove the empty brackets or add metadata such as max_link_capacity=1.",
                False,
            )

        match = self.metadata_regex.match(self.metadata)
        if not match:
            return self._locate_format_error()

        key = match.group("key")
        value = match.group("value")

        if key != "max_link_capacity":
            return ParsingProblem(
                TextSpan(match.start("key"), match.end("key")),
                f"'{key}' is not a supported connection metadata key.",
                "the key max_link_capacity.",
                "rename the key to max_link_capacity or remove it.",
                True,
            )

        try:
            capacity = int(value)
        except ValueError:
            return ParsingProblem(
                TextSpan(match.start("value"), match.end("value")),
                f"'{value}' is not a valid max_link_capacity value.",
                "a positive integer, such as 1 or 5.",
                "replace the value with a positive whole number.",
                True,
            )

        if capacity <= 0:
            return ParsingProblem(
                TextSpan(match.start("value"), match.end("value")),
                f"'{value}' is not a positive max_link_capacity value.",
                "a positive integer greater than 0.",
                "replace the value with a number greater than 0.",
                True,
            )

        return ParsingProblem(
            TextSpan.whole(self.metadata),
            "the metadata does not match the required format.",
            "max_link_capacity=<positive integer>.",
            "rewrite the metadata as max_link_capacity=1.",
            False,
        )

    def _locate_format_error(self) -> ParsingProblem:
        stripped = self.metadata.strip()
        start = self.metadata.find(stripped)

        if "=" not in stripped:
            key = stripped.split()[0] if stripped else stripped
            key_start = self.metadata.find(key) if key else start
            return ParsingProblem(
                TextSpan(key_start, key_start + len(key)),
                f"'{key}' is not followed by '='.",
                "max_link_capacity=<positive integer>.",
                "insert '=' between max_link_capacity and its value.",
                bool(key),
            )

        equal_index = self.metadata.find("=")
        before = self.metadata[:equal_index].strip()
        after = self.metadata[equal_index + 1:].strip()

        if not before:
            return ParsingProblem(
                TextSpan(equal_index, equal_index + 1),
                "the metadata key is missing before '='.",
                "the key max_link_capacity.",
                "add max_link_capacity before the equals sign.",
                True,
            )

        if not after:
            return ParsingProblem(
                TextSpan(equal_index, equal_index + 1),
                f"'{before}' has no value.",
                "a positive integer after '='.",
                "add a positive whole number after the equals sign.",
                True,
            )

        return ParsingProblem(
            TextSpan.whole(self.metadata),
            "the metadata contains extra or misplaced text.",
            "exactly one key=value pair: max_link_capacity=<positive integer>.",
            "remove extra text and keep one valid metadata pair.",
            False,
        )


class MapLineProblemLocator:
    drones_regex: Pattern = MapRegex.NB_DRONS

    def __init__(self, line: str) -> None:
        self.line = line or ""

    def locate(self) -> ParsingProblem:
        match = self.drones_regex.match(self.line)
        if not match:
            return ParsingProblem(
                TextSpan.whole(self.line),
                "the line does not match any expected map syntax.",
                "a drone count, hub line, or connection line.",
                "rewrite the line using one of the documented formats.",
                False,
            )

        key = match.group("key")
        value = match.group("value")

        if key.lower() != "nb_drones":
            return ParsingProblem(
                TextSpan(match.start("key"), match.end("key")),
                f"'{key}' is not the expected map header key.",
                "the key nb_drones.",
                "rename the key to nb_drones.",
                True,
            )

        try:
            drones = int(value)
        except ValueError:
            return ParsingProblem(
                TextSpan(match.start("value"), match.end("value")),
                f"'{value}' is not a valid drone count.",
                "a positive integer.",
                "replace it with a whole number greater than 0.",
                True,
            )

        if drones <= 0:
            return ParsingProblem(
                TextSpan(match.start("value"), match.end("value")),
                f"'{value}' is not a positive drone count.",
                "a positive integer greater than 0.",
                "replace it with a number greater than 0.",
                True,
            )

        return ParsingProblem(
            TextSpan.whole(self.line),
            "the map line is invalid in this context.",
            "a valid map line at the current parser stage.",
            "check the order and uniqueness of map entries.",
            False,
        )


class LineHighlighter:
    def __init__(self, context: SourceContext, highlighter: TextHighlighter) -> None:
        self.context = context
        self.highlighter = highlighter

    def highlighted_metadata(self, problem: ParsingProblem) -> str:
        metadata = self.context.metadata or ""
        if not metadata:
            return ""
        span = problem.span if problem.exact else TextSpan.whole(metadata)
        return self.highlighter.highlight(metadata, span)

    def highlighted_line(self, problem: ParsingProblem) -> Optional[str]:
        if self.context.line is None:
            return None

        metadata_span = self.context.locate_metadata()
        if metadata_span.is_known:
            metadata = self.context.metadata or ""
            highlighted_metadata = self.highlighted_metadata(problem)
            return (
                f"{self.context.line[:metadata_span.start]}{highlighted_metadata}"
                f"{self.context.line[metadata_span.start + len(metadata):]}"
            )

        if self.context.metadata == "" and "[]" in self.context.line:
            bracket_start = self.context.line.find("[]")
            return self.highlighter.highlight(
                self.context.line,
                TextSpan(bracket_start, bracket_start + 2),
            )

        return self.context.line

    def line_problem_span(self, problem: ParsingProblem) -> TextSpan:
        if not problem.exact:
            return TextSpan.unknown()
        return problem.span.shifted(self.context.locate_metadata().start)


class MetadataMessage:
    subject = "metadata"
    correct_format = "[key=value]"
    invalid_reason = "metadata must be valid key=value pairs."

    def __init__(
        self,
        problem: ParsingProblem,
        highlighted_metadata: str,
        highlighted_line: Optional[str],
        line_span: TextSpan,
    ) -> None:
        self.problem = problem
        self.highlighted_metadata = highlighted_metadata
        self.highlighted_line = highlighted_line
        self.line_span = line_span

    def build(self) -> str:
        location = (
            f"column {self.line_span.start + 1}"
            if self.line_span.is_known
            else "the metadata section; the exact column could not be determined"
        )
        message = (
            f"Invalid {self.subject} at {location}.\n"
            f"What is wrong: {self.problem.reason}\n"
            f"Why it is invalid: {self.invalid_reason}\n"
            f"Correct format: {self.correct_format}.\n"
            f"What is expected here: {self.problem.expected}\n"
            f"How to fix it: {self.problem.fix}\n"
            f"Metadata: {self.highlighted_metadata or '<empty>'}"
        )
        if self.highlighted_line:
            message += f"\nLine: {self.highlighted_line}"
        return message


class HubMetadataMessage(MetadataMessage):
    subject = "hub metadata"
    invalid_reason = (
        "hub metadata must be space-separated key=value pairs using only "
        "zone, color, and max_drones."
    )
    correct_format = (
        "[zone=normal color=blue max_drones=2]. Allowed zones are normal, "
        "blocked, restricted, and priority; color must contain letters only; "
        "max_drones must be an integer"
    )


class ConnectionMetadataMessage(MetadataMessage):
    subject = "connection metadata"
    invalid_reason = (
        "connection metadata must be exactly one key=value pair using "
        "max_link_capacity with a positive integer value."
    )
    correct_format = "[max_link_capacity=1]"


class MapParsingMessage:
    def __init__(
        self,
        original: "MapError",
        context: SourceContext,
        fallback_line: Optional[str],
    ) -> None:
        self.original = original
        self.context = context
        self.fallback_line = fallback_line

    def build(self) -> str:
        original_text = str(self.original)
        message = f"Invalid map file at {self._location()}.\n{original_text}\n"
        if "Line:" not in original_text:
            message += f"Line: {self._line()}\n"
        message += (
            "How to fix it: correct the highlighted part if one is shown; otherwise "
            "rewrite the whole line using the documented format."
        )
        return message

    def _location(self) -> str:
        location = (
            f"line {self.context.line_number}"
            if self.context.line_number is not None
            else "the current line"
        )
        if self.original.position is not None:
            return f"{location}, column {self.original.position + 1}"
        return f"{location}; the exact column could not be determined"

    def _line(self) -> str:
        return self.original.highlighted_line or self.original.line or self.fallback_line or "<unknown>"


class MapError(Exception):
    default_message = "The map contains invalid syntax."

    def __init__(
        self,
        message: Optional[str] = None,
        *,
        original: Optional[BaseException] = None,
        line: Optional[str] = None,
        line_number: Optional[int] = None,
        position: Optional[int] = None,
        end_position: Optional[int] = None,
        highlighted_line: Optional[str] = None,
    ) -> None:
        self.original = original
        self.line = line
        self.line_number = line_number
        self.position = position
        self.end_position = end_position
        self.highlighted_line = highlighted_line
        self.message = message or self.default_message
        super().__init__(self.message)

    def __str__(self) -> str:
        return self.message


class MapParsingError(MapError):
    default_message = (
        "Invalid map file.\n"
        "What is wrong: the parser found a line that does not match the map format.\n"
        "Why it is invalid: every map must start with 'nb_drones: <positive integer>' "
        "and then contain valid hub or connection lines.\n"
        "Correct format: nb_drones: 3, hub: H1 0 0 [zone=normal color=blue max_drones=2], "
        "or connection: H1-H2 [max_link_capacity=1].\n"
        "How to fix it: rewrite the line using the expected format and valid values."
    )

    def __init__(
        self,
        message: Optional[str] = None,
        *,
        original: Optional[BaseException] = None,
        line: Optional[str] = None,
        line_number: Optional[int] = None,
        **kwargs,
    ) -> None:
        if message is None and isinstance(original, MapError):
            context = SourceContext(line=line, line_number=line_number)
            message = MapParsingMessage(original, context, line).build()
            kwargs.setdefault("highlighted_line", original.highlighted_line)
            kwargs.setdefault("position", original.position)
            kwargs.setdefault("end_position", original.end_position)
        elif message is None and line is not None:
            problem = MapLineProblemLocator(line).locate()
            highlighted_line = TextHighlighter().highlight(
                line,
                problem.span if problem.exact else TextSpan.whole(line),
            )
            location = (
                f"line {line_number}, column {problem.span.start + 1}"
                if line_number is not None and problem.exact
                else f"line {line_number}; the exact column could not be determined"
                if line_number is not None
                else "the current line; the exact column could not be determined"
            )
            message = (
                f"Invalid map file at {location}.\n"
                f"What is wrong: {problem.reason}\n"
                "Why it is invalid: every map must start with 'nb_drones: <positive integer>' "
                "and then contain valid hub or connection lines.\n"
                "Correct format: nb_drones: 3, hub: H1 0 0 [zone=normal color=blue max_drones=2], "
                "or connection: H1-H2 [max_link_capacity=1].\n"
                f"What is expected here: {problem.expected}\n"
                f"How to fix it: {problem.fix}\n"
                f"Line: {highlighted_line}"
            )
            kwargs.setdefault("highlighted_line", highlighted_line)
            if problem.exact:
                kwargs.setdefault("position", problem.span.start)
                kwargs.setdefault("end_position", problem.span.end)

        super().__init__(
            message,
            original=original,
            line=line,
            line_number=line_number,
            **kwargs,
        )


class HubError(MapError):
    default_message = (
        "Invalid hub definition.\n"
        "What is wrong: the hub line does not match the expected hub syntax.\n"
        "Why it is invalid: a hub must have a valid type, name, x coordinate, y coordinate, "
        "and optional metadata in square brackets.\n"
        "Correct format: hub: H1 0 0 [zone=normal color=blue max_drones=2].\n"
        "How to fix it: use start_hub, hub, or end_hub, followed by a name and integer coordinates."
    )


class HubParsingError(HubError, MapParsingError):
    def __init__(
        self,
        message: Optional[str] = None,
        *,
        line: Optional[str] = None,
        **kwargs,
    ) -> None:
        if message is None and line is not None:
            highlighted_line = TextHighlighter().highlight(line, TextSpan.whole(line))
            message = (
                "Invalid hub definition.\n"
                "What is wrong: this line is not a valid hub.\n"
                "Why it is invalid: the parser expected a hub type, a name, two integer coordinates, "
                "and optional metadata in square brackets.\n"
                "Correct format: hub: H1 0 0 [zone=normal color=blue max_drones=2].\n"
                "How to fix it: check the hub type, spacing, name, coordinates, and metadata brackets.\n"
                f"Line: {highlighted_line}"
            )
            kwargs.setdefault("highlighted_line", highlighted_line)
        MapError.__init__(self, message, line=line, **kwargs)


class HubMetaDataParsingError(HubParsingError):
    def __init__(
        self,
        message: Optional[str] = None,
        *,
        line: Optional[str] = None,
        metadata: str = "",
        **kwargs,
    ) -> None:
        context = SourceContext(line=line, metadata=metadata)
        problem = HubMetadataProblemLocator(metadata).locate()
        highlighter = LineHighlighter(context, TextHighlighter())
        highlighted_metadata = highlighter.highlighted_metadata(problem)
        highlighted_line = highlighter.highlighted_line(problem)
        line_span = highlighter.line_problem_span(problem)

        if message is None:
            message = HubMetadataMessage(
                problem,
                highlighted_metadata,
                highlighted_line,
                line_span,
            ).build()

        MapError.__init__(
            self,
            message,
            line=line,
            position=line_span.start if line_span.is_known else None,
            end_position=line_span.end if line_span.is_known else None,
            highlighted_line=highlighted_line,
            **kwargs,
        )
        self.metadata = metadata
        self.highlighted_metadata = highlighted_metadata
        self.exact = problem.exact


class ConnectionError(MapError):
    default_message = (
        "Invalid connection definition.\n"
        "What is wrong: the connection line does not match the expected connection syntax.\n"
        "Why it is invalid: a connection must name two existing hubs and may include valid metadata.\n"
        "Correct format: connection: H1-H2 [max_link_capacity=1].\n"
        "How to fix it: use two different known hub names and a positive integer capacity."
    )


class ConnectionParsingError(ConnectionError, MapParsingError):
    def __init__(
        self,
        message: Optional[str] = None,
        *,
        line: Optional[str] = None,
        **kwargs,
    ) -> None:
        if message is None and line is not None:
            highlighted_line = TextHighlighter().highlight(line, TextSpan.whole(line))
            message = (
                "Invalid connection definition.\n"
                "What is wrong: this line is not a valid connection.\n"
                "Why it is invalid: a connection must name two different valid hubs and may include "
                "metadata in square brackets.\n"
                "Correct format: connection: H1-H2 [max_link_capacity=1].\n"
                "How to fix it: check the connection keyword, hub names, separator, and metadata.\n"
                f"Line: {highlighted_line}"
            )
            kwargs.setdefault("highlighted_line", highlighted_line)
        MapError.__init__(self, message, line=line, **kwargs)


class ConnectionMetaDataParsingError(ConnectionParsingError):
    def __init__(
        self,
        message: Optional[str] = None,
        *,
        line: Optional[str] = None,
        metadata: str = "",
        **kwargs,
    ) -> None:
        context = SourceContext(line=line, metadata=metadata)
        problem = ConnectionMetadataProblemLocator(metadata).locate()
        highlighter = LineHighlighter(context, TextHighlighter())
        highlighted_metadata = highlighter.highlighted_metadata(problem)
        highlighted_line = highlighter.highlighted_line(problem)
        line_span = highlighter.line_problem_span(problem)

        if message is None:
            message = ConnectionMetadataMessage(
                problem,
                highlighted_metadata,
                highlighted_line,
                line_span,
            ).build()

        MapError.__init__(
            self,
            message,
            line=line,
            position=line_span.start if line_span.is_known else None,
            end_position=line_span.end if line_span.is_known else None,
            highlighted_line=highlighted_line,
            **kwargs,
        )
        self.metadata = metadata
        self.highlighted_metadata = highlighted_metadata
        self.exact = problem.exact
