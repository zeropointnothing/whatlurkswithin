import pickle
import os
import logging
import hashlib
import time
from wlw.utils.character import Character
from wlw.utils.errors import *
from wlw.utils.logger import WLWLogger
from wlw.utils.formatting import FormatType

logging.setLoggerClass(WLWLogger)
log = logging.getLogger("WLWLogger")
log: WLWLogger

class Manager:
    """
    Manager class.

    Manages import game data, such as characters, persistent data and history, allowing for
    save and load functionality.
    """
    def __init__(self, save_path: str):
        self.save_path = save_path

        self.__obfuscation_key = save_path

        self.HISTORY_MAX = 20 # how many history values we should keep track of

        self.__current_section = {"chapter": None, "section": None}
        self.__characters: list[Character] = [] # game characters
        self.__persistent: dict = {} # persistent data
        self.__history: list[tuple[FormatType, str]] = [] # history of text

    @property
    def characters(self):
        """
        Game characters.

        Returns:
        list: List of registered characters.
        """
        return self.__characters

    @property
    def persistent(self):
        """
        Persistent data.

        Returns:
        dict: Persistent data.
        """
        return self.__persistent
    
    @persistent.setter
    def persistent(self, key: str, value):
        """
        Set persistent data.

        Args:
        key (str): Key to set.
        value: Value to set.
        """
        self.__persistent[key] = value

    @property
    def section(self):
        return self.__current_section

    @property
    def history(self):
        return self.__history

    def set_section(self, chapter_title: str, section_name: str):
        """
        Set the game's position, which will be used to resume upon loading.

        Args:
        chapter_title (str): The chapter's title.
        section_name: The section to jump to.
        """
        self.__current_section = {"chapter": chapter_title, "section": section_name}

    def register_character(self, character: Character):
        """
        Register a character to the game.

        Only characters added via this function will be saved to the save file.

        Args:
        character (Character): Character object to register.

        Returns:
        Character: The Character object supplied to this method.
        """
        log.debug(f"Registering character '{character._name}' (hidden: {character.hidden})...")
        character_match = [_ for _ in self.__characters if _._name == character._name]

        if character_match:
            log.debug(f"Using saved values for '{character._name}', already present.")
            return character_match[0]
        else:
            self.__characters.append(character)
            return character

    def get_character(self, name: str):
        for char in self.__characters:
            if char.name == name:
                return char
        raise CharacterNotFoundError(f"No such character '{name}'.")

    def _xor_obfuscate(self, data: bytes) -> bytes:
        """
        (de)Obfuscate data using XOR with the obfuscation key.

        Mainly used to discourage editing/save-scumming by making the reverse process
        more annoying, though not impossible.

        As long as the data hasn't been modified, should reverse any obfuscated bytes and vice-versa.

        Args:
        data (bytes): Data to (de)obfuscate.

        Returns:
        bytes: (de)Obfuscated data.
        """
        key = self.__obfuscation_key.encode()
        return bytes([b ^ key[i % len(key)] for i, b in enumerate(data)])

    def _add_history(self, thought: bool, title: str, text: list[tuple[FormatType, str|float]]) -> str:
        """
        Add text to the history.

        Automatically removes values that exceed the `HISTORY_MAX` attribute.

        Will not add duplicates.

        Args:
        thought (bool): Whether the entry is a 'thought'.
        title (str): The entry's title.
        text (list[tuple[FormatType, str|float]]): The formatted text to add.

        Returns:
        str: A 'history id'.
        """
        hid = hashlib.sha256(f"{text}{id(text)}".encode()).hexdigest()
        if not self._in_history(hid):
            self.__history.append({"hid": hid, "thought": thought, "title": title, "text": text})
            if len(self.__history) > self.HISTORY_MAX:
                self.__history = self.history[len(self.__history)-self.HISTORY_MAX:]

        return hid

    def _in_history(self, hid: str) -> bool:
        """
        Check if an entry exists in the history based on its HID.

        Args:
        hid (str): The HistoryID to check for.

        Returns:
        bool: Whether it was found in the history.
        """
        return hid in [_["hid"] for _ in self.history]

    def save(self):
        """
        Save game data to the save file.

        Special characters are excluded from the save file and are not persistent.
        """
        log.info("Saving game data...")
        with open(self.save_path, "wb") as f:
            save = pickle.dumps({
                "current_section": self.__current_section,
                "history": self.__history,
                "characters": [_ for _ in self.__characters if not _.special],
                "persistent": self.__persistent})
            
            pickle.dump({"!!WLW-SAVE-FILE_DO-NOT-EDIT!!": self._xor_obfuscate(save)}, f)

        log.info(f"Successfully wrote game data to '{self.save_path}'.")

    def load(self):
        """
        Load game data from the save file.

        Raises:
        FileNotFoundError: The save file does not exist.
        """
        log.info("Loading game data...")
        if not os.path.exists(self.save_path):
            raise FileNotFoundError(f"Save file '{self.save_path}' does not exist.")

        with open(self.save_path, "rb") as f:
            try:
                raw = pickle.load(f) # load the save file container and depickle it
                data = pickle.loads(self._xor_obfuscate(raw["!!WLW-SAVE-FILE_DO-NOT-EDIT!!"])) # deobfuscate, then reconstruct the save
            except pickle.UnpicklingError as e:
                raise BadSaveError("Save file is invalid or corrupt!") from e
            except UnicodeDecodeError as e: # deobfuscation errors, should hide as much context as possible
                raise BadSaveError(f"Save file is malformed! ({e})") from None

            try:
                self.__history = data["history"]
                self.__characters = data["characters"]
                self.__persistent = data["persistent"]
                self.__current_section = data["current_section"]
            except KeyError as e: # bad keys, user likely changed something or the file is outdated.
                raise BadSaveError(f"Save data is malformed! ({e})") from None

        log.info(f"Successfully read game data from '{self.save_path}'.")
