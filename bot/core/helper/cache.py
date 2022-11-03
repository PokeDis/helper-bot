import time
import typing


class ExpiringCache(dict):
    def __init__(self, seconds: float) -> None:
        self.__ttl: float = seconds
        super().__init__()

    def __verify_cache_integrity(self) -> None:
        current_time = time.monotonic()
        to_remove = [k for (k, (v, t)) in self.items() if current_time > (t + self.__ttl)]
        for k in to_remove:
            del self[k]

    def __contains__(self, key: str) -> bool:
        self.__verify_cache_integrity()
        return super().__contains__(key)

    def __getitem__(self, key: str) -> typing.Any:
        self.__verify_cache_integrity()
        return super().__getitem__(key)

    def __setitem__(self, key: str, value: typing.Any) -> None:
        super().__setitem__(key, (value, time.monotonic()))
