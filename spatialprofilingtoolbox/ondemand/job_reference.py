"""Represent one job."""

from attrs import define
from psycopg import Notify


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


@define
class Notification:
    pid: int
    channel: str
    payload: str | ComputationJobReference


def parse_notification(notification: Notify) -> Notification:
    pid = notification.pid
    parts = notification.payload.split('\t')
    channel = parts[0]
    remainder = parts[1:]
    payload: str | ComputationJobReference
    if len(remainder) == 0:
        raise ValueError(f'Notification payload "{notification.payload}" malformed.')
    elif len(remainder) == 1:
        payload = remainder[0]
    elif len(remainder) == 3:
        payload = JobSerialization.from_string('\t'.join(remainder))
    else:
        raise ValueError(f'Notification payload "{notification.payload}" has 2, 4, or more components.')
    return Notification(pid, channel, payload)


def create_notify_command(channel: str, payload: str | ComputationJobReference) -> str:
    if isinstance(payload, str):
        payload_str = payload
    if isinstance(payload, ComputationJobReference):
        payload_str = JobSerialization.to_string(payload)
    internal_payload = '\t'.join((channel, payload_str))
    return f"NOTIFY queue_activity, '{internal_payload}' ;"
