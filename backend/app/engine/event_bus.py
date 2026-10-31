"""In-memory pub/sub feeding Server-Sent Events. History is bounded per experiment."""
import asyncio
from collections import OrderedDict, deque
from dataclasses import dataclass
from typing import Any, AsyncIterator, Optional


@dataclass
class BusEvent:
    id: int
    type: str
    data: Any


class _Channel:
    def __init__(self, history_size: int):
        self.history: deque[BusEvent] = deque(maxlen=history_size)
        self.subscribers: set[asyncio.Queue] = set()
        self.seq = 0
        self.closed = False


class EventBus:
    def __init__(self, history_size: int = 500, max_channels: int = 20):
        self._channels: OrderedDict[str, _Channel] = OrderedDict()
        self._history_size, self._max_channels = history_size, max_channels

    def _channel(self, experiment_id: str) -> _Channel:
        if experiment_id not in self._channels:
            self._channels[experiment_id] = _Channel(self._history_size)
            while len(self._channels) > self._max_channels:
                self._channels.popitem(last=False)
        return self._channels[experiment_id]

    def publish(self, experiment_id: str, event_type: str, data: Any) -> None:
        channel = self._channel(experiment_id)
        channel.seq += 1
        event = BusEvent(channel.seq, event_type, data)
        channel.history.append(event)
        for queue in channel.subscribers:
            if queue.full():
                queue.get_nowait()  # drop the oldest rather than grow without bound
            queue.put_nowait(event)

    def close(self, experiment_id: str) -> None:
        channel = self._channel(experiment_id)
        channel.closed = True
        for queue in channel.subscribers:
            queue.put_nowait(None)

    def has_channel(self, experiment_id: str) -> bool:
        return experiment_id in self._channels

    async def subscribe(self, experiment_id: str, last_event_id: int = 0,
                        keepalive_s: float = 15.0) -> AsyncIterator[Optional[BusEvent]]:
        """Yield history after last_event_id, then live events. Yields None as a keep-alive tick."""
        channel = self._channels.get(experiment_id)
        if channel is None:
            return
        queue: asyncio.Queue = asyncio.Queue(maxsize=1000)
        channel.subscribers.add(queue)  # subscribe first so nothing is missed during replay
        try:
            last = last_event_id
            for event in list(channel.history):
                if event.id > last:
                    last = event.id
                    yield event
            if channel.closed:
                return
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), keepalive_s)
                except asyncio.TimeoutError:
                    yield None
                    continue
                if event is None:
                    return
                if event.id > last:
                    last = event.id
                    yield event
        finally:
            channel.subscribers.discard(queue)
