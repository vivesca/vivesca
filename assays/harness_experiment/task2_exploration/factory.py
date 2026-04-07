"""Abstract factory pattern for notification delivery."""

from abc import ABC, abstractmethod
from typing import ClassVar


class Notification(ABC):
    @abstractmethod
    def send(self, recipient: str, message: str) -> bool: ...

    @abstractmethod
    def validate(self, recipient: str) -> bool: ...


class EmailNotification(Notification):
    def send(self, recipient: str, message: str) -> bool:
        return "@" in recipient

    def validate(self, recipient: str) -> bool:
        return "@" in recipient and "." in recipient


class SMSNotification(Notification):
    def send(self, recipient: str, message: str) -> bool:
        return recipient.startswith("+")

    def validate(self, recipient: str) -> bool:
        return recipient.startswith("+") and len(recipient) >= 10


class NotificationFactory:
    _registry: ClassVar[dict[str, type[Notification]]] = {
        "email": EmailNotification,
        "sms": SMSNotification,
    }

    @classmethod
    def create(cls, channel: str) -> Notification:
        if channel not in cls._registry:
            raise ValueError(f"Unknown channel: {channel}")
        return cls._registry[channel]()

    @classmethod
    def register(cls, channel: str, notification_cls: type[Notification]) -> None:
        cls._registry[channel] = notification_cls

    @classmethod
    def available_channels(cls) -> list[str]:
        return list(cls._registry.keys())
