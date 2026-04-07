"""Notification dispatch service — uses factory for channel selection."""

from factory import NotificationFactory


class NotificationService:
    def __init__(self, default_channel: str = "email"):
        self.default_channel = default_channel
        self.sent_count = 0

    def notify(self, recipient: str, message: str, channel: str | None = None) -> bool:
        channel = channel or self.default_channel
        notifier = NotificationFactory.create(channel)
        if not notifier.validate(recipient):
            return False
        result = notifier.send(recipient, message)
        if result:
            self.sent_count += 1
        return result

    def bulk_notify(self, recipients: list[str], message: str, channel: str | None = None) -> dict:
        results = {}
        for recipient in recipients:
            results[recipient] = self.notify(recipient, message, channel)
        return results
