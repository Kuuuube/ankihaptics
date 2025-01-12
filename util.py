import asyncio
import collections.abc


def maybe_parse_float(input_string: str, maybe: float) -> float:
    try:
        return float(input_string)
    except Exception:  # noqa: BLE001
        return maybe

#Allows running an async function on a thread
def start_async(function: collections.abc.Callable) -> None:
    asyncio.run(function())
