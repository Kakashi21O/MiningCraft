"""Runner script to connect Nova to the Minecraft server and stand in the world."""

import asyncio
import contextlib
import signal
import sys
from typing import Any

from miningcraft.core.config import load_config
from miningcraft.core.events import EventBus
from miningcraft.core.logger import configure_logging, get_logger
from miningcraft.perception.cache import PerceptionManager
from miningcraft.protocol.connection import MinecraftConnection

logger = get_logger("scripts.connect_bot")


async def main() -> None:
    # 1. Load configuration
    try:
        config = load_config("config/config.yaml")
    except Exception as e:
        print(f"Error loading configuration: {e}")
        sys.exit(1)

    # 2. Configure logging
    configure_logging(level=config.logging.level, fmt=config.logging.format)
    print("\n=======================================================")
    print(f"  Starting MiningCraft Bot: {config.bot.username}")
    print(f"  Target Server: {config.server.host}:{config.server.port}")
    print("=======================================================\n")

    # 3. Initialize components
    event_bus = EventBus()
    perception = PerceptionManager()
    perception.attach(event_bus)

    # Event logging callbacks
    def on_connected(**kwargs: Any) -> None:
        print(f"\n>>> [SUCCESS] {config.bot.username} connected and spawned into server!")
        print(">>> Bot is now standing in the world. Press Ctrl+C to disconnect.\n")

    def on_disconnected(**kwargs: Any) -> None:
        print("\n>>> [DISCONNECTED] Bot disconnected from server.")

    def on_chat(**kwargs: Any) -> None:
        packet = kwargs.get("packet")
        if packet and hasattr(packet, "json_data"):
            print(f"[CHAT] {packet.json_data}")

    event_bus.subscribe("OnConnected", on_connected)
    event_bus.subscribe("OnDisconnected", on_disconnected)
    event_bus.subscribe("OnChatMessage", on_chat)

    connection = MinecraftConnection(
        event_bus=event_bus,
        max_retries=3,
        keepalive_interval=20.0,
    )

    # 4. Connect to Minecraft server
    print(f"Connecting to {config.server.host}:{config.server.port} as '{config.bot.username}'...")
    success = await connection.connect(
        host=config.server.host,
        port=config.server.port,
        username=config.bot.username,
        version=config.server.version,
    )

    if not success:
        print(f"\n[FAILED] Could not connect to {config.server.host}:{config.server.port}.")
        print("Please verify:")
        print(" 1. The Aternos server is ONLINE.")
        print(" 2. 'Cracked' is ENABLED in Aternos Options (for offline username login).")
        print(" 3. The server IP and port are exact.\n")
        return

    # 5. Keep running until stopped
    stop_event = asyncio.Event()

    def handle_signal() -> None:
        print("\nStopping bot...")
        stop_event.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        with contextlib.suppress(NotImplementedError):
            loop.add_signal_handler(sig, handle_signal)

    try:
        while not stop_event.is_set():
            await asyncio.sleep(1.0)
            if not connection.is_connected:
                print("Connection lost.")
                break
    except (asyncio.CancelledError, KeyboardInterrupt):
        print("\nDisconnecting...")
    finally:
        await connection.disconnect()
        perception.detach()
        print("Bot shutdown complete.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExited.")
