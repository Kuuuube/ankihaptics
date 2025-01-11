import asyncio
from collections.abc import Callable


def try_parse_float(input_string: str) -> float:
    try:
        return float(input_string)
    except Exception:  # noqa: BLE001
        return None

#Allows running an async function on a thread
def start_async(function: Callable) -> None:
    asyncio.run(function())
