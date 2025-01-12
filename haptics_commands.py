import asyncio
import threading

import buttplug

from . import util


def run_scalar_command(actuator: buttplug.client.Actuator, start_strength: float, end_strength: float, duration: float) -> None:
    threading.Thread(target = lambda: util.start_async(lambda: scalar_command(actuator, start_strength, end_strength, duration)))

async def scalar_command(actuator: buttplug.client.Actuator, start_strength: float, end_strength: float, duration: float) -> None:
    await actuator.command(start_strength)
    await asyncio.sleep(duration)
    await actuator.command(end_strength)
