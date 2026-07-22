import asyncio
import json
import logging
from typing import Callable, List, Optional, Set, Tuple

logger = logging.getLogger("ResQMesh.SocketServer")


class ResQMeshSocketServer:
    """Async TCP Socket Server for peer-to-peer event broadcasting over LAN."""

    def __init__(self, host: str = "0.0.0.0", port: int = 8001):
        self.host = host
        self.port = port
        self.server: Optional[asyncio.Server] = None
        self.connected_clients: Set[Tuple[asyncio.StreamReader, asyncio.StreamWriter]] = set()
        self.message_handlers: List[Callable[[dict, str], None]] = []
        self.is_running = False

    def register_handler(self, handler: Callable[[dict, str], None]) -> None:
        """Register a callback for incoming messages: handler(payload_dict, sender_ip)."""
        self.message_handlers.append(handler)

    async def start(self) -> None:
        """Start listening for incoming TCP peer connections."""
        if self.is_running:
            return

        self.server = await asyncio.start_server(
            self._handle_client, self.host, self.port
        )
        self.is_running = True
        logger.info(f"Socket server listening on {self.host}:{self.port}")

    async def stop(self) -> None:
        """Stop server and close all client sockets."""
        if not self.is_running or not self.server:
            return

        self.is_running = False
        for reader, writer in list(self.connected_clients):
            try:
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass
        self.connected_clients.clear()

        self.server.close()
        await self.server.wait_closed()
        logger.info("Socket server stopped.")

    async def _handle_client(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        peer_addr = writer.get_extra_info("peername")
        sender_ip = peer_addr[0] if peer_addr else "unknown"
        client_tuple = (reader, writer)
        self.connected_clients.add(client_tuple)
        logger.info(f"New socket peer connected from {sender_ip}")

        try:
            while self.is_running:
                data = await reader.readline()
                if not data:
                    break
                line = data.decode("utf-8").strip()
                if not line:
                    continue

                try:
                    payload = json.loads(line)
                    for handler in self.message_handlers:
                        try:
                            if asyncio.iscoroutinefunction(handler):
                                await handler(payload, sender_ip)
                            else:
                                handler(payload, sender_ip)
                        except Exception as e:
                            logger.error(f"Error executing message handler: {e}")
                except json.JSONDecodeError:
                    logger.warning(f"Received non-JSON packet from {sender_ip}: {line[:50]}")

        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.debug(f"Connection error with peer {sender_ip}: {e}")
        finally:
            self.connected_clients.discard(client_tuple)
            try:
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass
            logger.info(f"Peer {sender_ip} disconnected.")

    async def send_to_peer(self, ip: str, port: int, payload: dict) -> bool:
        """Connect to a target peer IP/port and send a newline-delimited JSON payload."""
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(ip, port), timeout=3.0
            )
            raw_data = json.dumps(payload) + "\n"
            writer.write(raw_data.encode("utf-8"))
            await writer.drain()
            writer.close()
            await writer.wait_closed()
            return True
        except Exception as e:
            logger.warning(f"Failed to send TCP packet to peer {ip}:{port} - {e}")
            return False

    async def broadcast(self, payload: dict, target_peers: List[dict]) -> int:
        """Broadcast payload to all discovered LAN peers."""
        success_count = 0
        tasks = [
            self.send_to_peer(peer["ip"], peer["port"], payload)
            for peer in target_peers
            if "ip" in peer and "port" in peer
        ]
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            success_count = sum(1 for r in results if r is True)
        return success_count
