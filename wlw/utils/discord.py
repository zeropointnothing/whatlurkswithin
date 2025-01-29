import sys
import os
import logging
import json
import struct
import socket
import time
from enum import Enum
from wlw.utils.logger import WLWLogger
from wlw.utils.errors import *

logging.setLoggerClass(WLWLogger)
log = logging.getLogger("WLWLogger")
log: WLWLogger

class RichPresence:
    """
    Simple wrapper for Discord Rich Presence.
    """
    __socket: socket.socket
    def __init__(self, client_id: str):
        """
        Automatically locates the Discord IPC socket and preps the client for RPC.
        """
        if sys.platform == "linux":
            self.__ipc_path = os.path.join(os.getenv("XDG_RUNTIME_DIR", "/tmp"),  "discord-ipc-0")
        else:
            raise NotImplementedError("Unable to determine a valid IPC socket path for this platform!")

        if not os.path.exists(self.__ipc_path):
            raise FileNotFoundError("Failed to determine a valid IPC socket path!")
        else:
            log.debug(f"Using IPC socket path: '{self.__ipc_path}' to communicate with Discord.")


        self.__client_id = client_id
        self.__authenticated = -1
        self.__socket = None

        log.debug("Ready for RichPresence!")

    # utility classes/functions
    class ActivityType(Enum):
        """
        Supported activity types for this library and Discord.

        Must be '0', '2', or '3'.
        """
        PLAYING = 0
        LISTENING = 2
        WATCHING = 3

    # 'frontend' RPC functions
    def set_state(self, type: ActivityType, state: str, details: str, start: int = None, large_image: str = None, large_text: str = None) -> tuple[int, dict] | None:
        """
        Set the current Presence state.
        
        Automatically creates the payload, then returns Discord's response, if any.
        
        Args:
        type (ActivityType): The type of activity.
        state (str): The 'state' of the activity. Will be the second line in the presence.
        details (str): The 'details' of the activity. Will be the first line in the presence.
        start (int | None): When the activity started. Will default the the current time if not supplied.
        large_image (str | None): The large image key.
        large_text (str | None): The large image's hover text.

        Returns:
        tuple[int, dict] | None: Discord's response, if any.
        """
        # assemble the payload
        payload = {
            "cmd": "SET_ACTIVITY",
            "args": {
                "pid": os.getpid(),
                "activity": {
                    "type": type.value,
                    "state": state,
                    "details": details,
                    "timestamps": {
                        "start": start if start else int(time.time())
                    },
                    "assets": {
                        "large_image": large_image,
                        "large_text": large_text
                    }
                }
            },
            "nonce": str(time.time())
        }


        log.debug(f"Updating presence with payload: {payload}.")
        self.__send_packet(1, payload)

        op, payload = self.__read_packet()
        log.debug(f"Discord responded with OpCode '{op}'.")

        return op, payload

    def clear_state(self):
        """
        Sends an empty activity update to Discord, effectively clearing the presence.
        
        Returns Discord's response, if any.
        
        Returns:
        tuple[int, dict] | None: Discord's response, if any.
        """
        payload = {
            "cmd": "SET_ACTIVITY",
            "args": {
                "pid": os.getpid(),
                "activity": None
            },
            "nonce": str(time.time())
        }
        log.debug("Clearing presence...")
        self.__send_packet(1, payload)

        # we don't really need this, but the RPC server will error out if we close without reading
        op, payload = self.__read_packet()
        log.debug(f"Discord responded with '{op}'.")

        return op, payload

    # manual RPC functions

    def _connect(self) -> socket.socket:
        """
        Connect to the Discord IPC socket.
        
        Should only be called once, unless the connection needs to be restablished.

        Returns:
        socket: The connected socket.
        """
        if self.__socket:
            raise ConnectionError("IPC socket is already connected!")

        log.debug("Attempting to open a connection to the IPC socket...")

        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect(self.__ipc_path)

        if sock.fileno() != -1:
            self.__socket = sock
            log.debug("Connection to IPC socket established!")
            return self.__socket
        else:
            ConnectionError("Connection to IPC socket was abnormally closed?")

    def _disconnect(self):
        """
        Disconnect from the Discord IPC socket.

        If authenticated, will attempt to clear any ongoing presence.
        """
        if not self.__socket:
            raise ConnectionError("IPC socket is not connected!")

        log.debug("Attempting to cleanup and close the IPC socket...")

        if self.__authenticated == 1:
            self.clear_state()
            self.__authenticated = -1
        self.__socket.close()
        self.__socket = None


    def _authenticate(self):
        """
        Authenticate with Discord.
        
        Required before any other RPC calls.
        """
        payload = {
            "v": 1,
            "client_id": self.__client_id
        }
        log.debug("Attempting to authenticate with Discord...")
        self.__authenticated = 0
        self.__send_packet(0, payload)

        op, payload = self.__read_packet()
        if op == 1:
            self.__authenticated = 1
            log.debug("Authentication with Discord successful!")
        else:
            self.__authenticated = -1
            raise ConnectionError(f"Failed to authenticate with Discord. Returned OpCode: '{op}'.")

    # private backend stuff

    def __check_auth(func):
        """
        Decorator to check if the client is authenticated.

        Raises:
        AuthenticationError: Client has no been authenticated yet.
        """
        def wrapper(self, *args, **kwargs):
            if self.__authenticated in [0, 1]: # we aren't authenticating or already authenticated
                return func(self, *args, **kwargs)
            else:
                raise AuthenticationError("Client is not authenticated with Discord!")
        return wrapper

    @__check_auth
    def __send_packet(self, op: int, payload: dict):
        """
        Send a packet, including its OpCode and Payload to the IPC socket.
        """
        if not self.__socket:
            raise ConnectionError("IPC socket is not connected!")

        data = json.dumps(payload).encode('utf-8') # we can't send dict objects over socket
        # we need to convert these into binary first
        length = struct.pack('<I', len(data))
        packet = struct.pack('<I', op) + length + data
        
        self.__socket.sendall(packet)

    @__check_auth
    def __read_packet(self) -> tuple[int, dict]:
        """
        Attempt to read a packet from the IPC socket.
        
        Returns:
        tuple[int, dict]: OpCode and Payload.
        """
        if not self.__socket:
            raise ConnectionError("IPC socket is not connected!")

        op = struct.unpack('<I', self.__socket.recv(4))[0] # first four bytes are the OpCode
        length = struct.unpack('<I', self.__socket.recv(4))[0] # next four bytes are the length of the payload
        data = self.__socket.recv(length) # read the actual payload
        payload = json.loads(data.decode('utf-8')) # decode into a dict we can use

        return op, payload
