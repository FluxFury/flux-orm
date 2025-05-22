import enum
import typing


class CustomStrEnum(enum.StrEnum):
    @classmethod
    def _missing_(cls, value: object) -> typing.LiteralString | None:
        """Return the member that matches the lowercase value."""
        value = str(value).lower()
        for member in cls:
            if all((
                hasattr(member, "value"),
                isinstance(member.value, str),
                member.value.lower() == value,
            )):
                return member
        return None


@enum.unique
class PipelineStatus(CustomStrEnum):
    NEW = "new"
    SENT = "sent"
    PROCESSED = "processed"
    ERROR = "error"


@enum.unique
class MatchStatusEnum(CustomStrEnum):
    SCHEDULED = "scheduled"
    LIVE = "live"
    FINISHED = "finished"
    CANCELLED = "cancelled"
    POSTPONED = "postponed"
