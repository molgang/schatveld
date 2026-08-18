"""rcon.py — minimale Source-RCON-client (pure stdlib, geen pip).
Genoeg om een Minecraft-server te authenticeren en commando's te sturen/lezen.
Protocol: length(int32 LE) + id(int32 LE) + type(int32 LE) + body(ascii\\0) + \\0.
Types: 3=AUTH, 2=AUTH_RESPONSE/EXECCOMMAND, 0=RESPONSE_VALUE."""
import socket
import struct

AUTH, EXEC, RESP = 3, 2, 0


class RconError(Exception):
    pass


class Rcon:
    def __init__(self, host="127.0.0.1", port=25575, password="", timeout=6.0):
        self.host, self.port, self.password, self.timeout = host, port, password, timeout
        self.sock = None
        self._id = 0

    def connect(self):
        self.sock = socket.create_connection((self.host, self.port), self.timeout)
        self.sock.settimeout(self.timeout)
        if not self._auth(self.password):
            raise RconError("RCON-authenticatie mislukt (verkeerd wachtwoord?)")
        return self

    def _pack(self, ptype, body):
        self._id += 1
        payload = struct.pack("<ii", self._id, ptype) + body.encode("utf-8") + b"\x00\x00"
        return struct.pack("<i", len(payload)) + payload, self._id

    def _recv(self):
        raw = self._read(4)
        (length,) = struct.unpack("<i", raw)
        data = self._read(length)
        rid, ptype = struct.unpack("<ii", data[:8])
        body = data[8:-2].decode("utf-8", "replace")
        return rid, ptype, body

    def _read(self, n):
        buf = b""
        while len(buf) < n:
            chunk = self.sock.recv(n - len(buf))
            if not chunk:
                raise RconError("verbinding gesloten")
            buf += chunk
        return buf

    def _auth(self, password):
        pkt, sent_id = self._pack(AUTH, password)
        self.sock.sendall(pkt)
        rid, ptype, _ = self._recv()
        return rid != -1

    def command(self, cmd):
        pkt, sent_id = self._pack(EXEC, cmd)
        self.sock.sendall(pkt)
        rid, ptype, body = self._recv()
        return body

    def close(self):
        if self.sock:
            try:
                self.sock.close()
            except OSError:
                pass
            self.sock = None

    def __enter__(self):
        return self.connect()

    def __exit__(self, *a):
        self.close()
