"""Represent one job."""

from attrs import define
from psycopg import Notify
from psycopg import Connection as PsycopgConnection


@define(frozen=True)
class ComputationJobReference:
    """Represent one job."""
    feature_specification: int
    study: str
    sample: str


class JobSerialization:
    """Job reference to and from string."""
    @classmethod
    def to_string(cls, job: ComputationJobReference) -> str:
        return f'{job.feature_specification}\t{job.study}\t{job.sample}'

    @classmethod
    def from_string(cls, payload: str) -> ComputationJobReference:
        parts = payload.split('\t')
        return ComputationJobReference(int(parts[0]), parts[1], parts[2])


@define(frozen=True)
class CompletedFeature:
    """Represents one feature with all computation jobs just completed."""
    feature_specification: int
    study: str


class CompletionSerialization:
    """Completed feature reference to and from string."""
    @classmethod
    def to_string(cls, completed: CompletedFeature) -> str:
        return f'{completed.feature_specification}\t{completed.study}'

    @classmethod
    def from_string(cls, payload: str) -> CompletedFeature:
        parts = payload.split('\t')
        return CompletedFeature(int(parts[0]), parts[1])


NotificationPayload = str | ComputationJobReference | CompletedFeature

@define
class Notification:
    pid: int
    channel: str
    payload: NotificationPayload


def parse_notification(notification: Notify) -> Notification:
    pid = notification.pid
    parts = notification.payload.split('\t')
    channel = parts[0]
    remainder = parts[1:]
    payload: NotificationPayload
    if len(remainder) == 0:
        raise ValueError(f'Notification payload "{notification.payload}" malformed.')
    elif len(remainder) == 1:
        payload = remainder[0]
    elif len(remainder) == 2:
        payload = CompletedFeature(int(remainder[0]), remainder[1])
    elif len(remainder) == 3:
        payload = ComputationJobReference(int(remainder[0]), remainder[1], remainder[2])
    else:
        raise ValueError(f'Notification payload "{notification.payload}" has 2, 4, or more components.')
    return Notification(pid, channel, payload)


def create_notify_command(channel: str, payload: NotificationPayload) -> str:
    if isinstance(payload, str):
        payload_str = payload
    if isinstance(payload, CompletedFeature):
        payload_str = CompletionSerialization.to_string(payload)
    if isinstance(payload, ComputationJobReference):
        payload_str = JobSerialization.to_string(payload)
    internal_payload = '\t'.join((channel, payload_str))
    return f"NOTIFY queue_activity, '{internal_payload}' ;"


def notify_feature_complete(study: str, feature: int, connection: PsycopgConnection) -> None:
    completed = CompletedFeature(feature, study)
    notify = create_notify_command('feature computation jobs complete', completed)
    connection.execute(notify)
