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

    Supplies various functions to interact ONLY with the Rich Presence API.

    Most functions will raise errors upon unexpected results, so ensure proper error handling is done when using this.
    """
    __socket: socket.socket
    def __init__(self, client_id: str):
        """
        Automatically locates the Discord IPC socket and preps the client for RPC.

        Args:
        client_id (str): The client ID to use when communicating with Discord.
        """
        if sys.platform == "linux":
            self.__ipc_path = os.path.join(os.getenv("XDG_RUNTIME_DIR", "/tmp"),  "discord-ipc-0")
            self.__rpc_supported = True
        else:
            log.warning("Unable to determine a valid IPC socket path for this platform! RPC should be completely disabled!")
            self.__ipc_path = ""
            self.__rpc_supported = False

        if not os.path.exists(self.__ipc_path):
            log.warning("Failed to determine a valid IPC socket path! RPC will be disabled!")
            self.__can_rpc = False
        else:
            self.__can_rpc = True
            log.debug(f"Using IPC socket path: '{self.__ipc_path}' to communicate with Discord.")

        self.__client_id = client_id
        self.__authenticated = -1
        self.__socket = None
        self.__last_payload = {}

        log.debug("Ready for RichPresence!")

    # properties
    @property
    def is_ready(self) -> bool:
        """
        Whether the connection to the IPC socket is active and authenticated.

        If the socket is available and supposedly authenticated, will attempt to reload the current activity.
        
        If any known errors occur, will assume the connection was broken.

        Returns:
        bool: Whether the connection is active and authenticated.
        """

        if not self.__can_rpc:
            return False
        elif self.__socket and self.__authenticated == 1:
            try:
                op, payload = self.reload_state()
                return op == 1
            except (socket.error, json.JSONDecodeError, struct.error, ConnectionError, BrokenPipeError, AuthenticationError) as e:
                return False
        else:
            return False

    @property
    def rpc_supported(self) -> bool:
        """
        Whether the current platform supports Rich Presence.
        """
        return self.__rpc_supported

    @property
    def enabled(self):
        """
        Whether or not RPC is enabled.

        To prevent errors, most functions will simply return if this is False.
        """
        return self.__can_rpc

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

        if not self.__can_rpc:
            # we can't update, but we should still save the intended payload
            self.__last_payload = payload
            return None

        try:
            log.debug(f"Updating presence with payload: {payload}.")
            self.__send_packet(1, payload)
            self.__last_payload = payload

            op, payload = self.__read_packet()
            log.debug(f"Discord responded with OpCode '{op}'.")
            return op, payload
        except (ConnectionError, BrokenPipeError) as e:
            log.warning(f"RPC failed to update with error: {e}. Disabling until further notice.")
            self.__authenticated = -1
            self.__socket = None
            self.__can_rpc = False


    def reload_state(self):
        """
        Reload the state using the last saved payload set by `set_state`.

        Useful for reconnecting to Discord's IPC.

        Returns:
        tuple[int, dict]: Discord's response, if any.
        """
        if not self.__can_rpc:
            return None
        elif not self.__last_payload:
            raise ValueError("No last payload!")

        log.debug(f"Reloading last presence state: {self.__last_payload}")
        self.__send_packet(1, self.__last_payload)

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
        if not self.__can_rpc:
            return None

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

        self.__last_payload = {}

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
        elif not self.__rpc_supported:
            return

        log.debug("Attempting to open a connection to the IPC socket...")

        try:
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect(self.__ipc_path)
        except FileNotFoundError: # we shouldn't raise an error here, since this is the best way to 'ping' the socket
            self.__can_rpc = False
            log.debug("Unable to locate IPC socket!")
            return None

        if sock.fileno() != -1:
            self.__socket = sock
            self.__can_rpc = True
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
            self.__authenticated = -1
            return # socket was already closed, we don't need to (cant) do anything
        elif not self.__can_rpc:
            return None

        log.debug("Attempting to cleanup and close the IPC socket...")

        if self.__authenticated == 1:
            try:
                self.clear_state()
            except BrokenPipeError: # connection was closed already, we can't do anything more
                pass
            self.__authenticated = -1
        self.__socket.close()
        self.__socket = None


    def _authenticate(self):
        """
        Authenticate with Discord.
        
        Required before any other RPC calls.
        """
        if not self.__can_rpc:
            return None

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
