from abc import ABC, abstractmethod


class NotificationProvider(ABC):
    @abstractmethod
    async def send(self, *, recipient: str, text: str) -> None:
        raise NotImplementedError


class NullNotificationProvider(NotificationProvider):
    async def send(self, *, recipient: str, text: str) -> None:
        return None
