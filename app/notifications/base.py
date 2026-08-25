from abc import ABC, abstractmethod


class NotificationProvider(ABC):
    @abstractmethod
    async def send(self, *, chat_id: int, text: str) -> None:
        raise NotImplementedError


class NullNotificationProvider(NotificationProvider):
    async def send(self, *, chat_id: int, text: str) -> None:
        return None
