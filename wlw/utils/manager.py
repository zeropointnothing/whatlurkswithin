import pickle
import os
from wlw.utils.character import Character

class Manager:
    """
    Manager class.

    Manages import game data, such as characters and persistent data, allowing for
    save and load functionality.
    """
    def __init__(self, save_path: str):
        self.save_path = save_path

        self.__SPECIAL_CHARACTERS = ["narrator"]

        self.__current_section = {"chapter": None, "section": None}
        self.__characters: list[Character] = [] # game characters
        self.__persistent: dict = {} # persistent data

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

        Special characters (Narrator) are not included when saving.

        Args:
        character (Character): Character object to register.

        Returns:
        Character: The Character object supplied to this method.
        """
        self.__characters.append(character)

        return character

    def get_character(self, name: str):
        for char in self.__characters:
            if char.name == name:
                return char
        raise ValueError(f"No such character '{name}'.")

    def save(self):
        """
        Save game data to the save file.
        """
        with open(self.save_path, "wb") as f:
            pickle.dump({"current_section": self.__current_section, 
                         "characters": [_ for _ in self.__characters if _.name.lower() not in self.__SPECIAL_CHARACTERS],
                         "persistent": self.__persistent}, f)

    def load(self):
        """
        Load game data from the save file.

        Raises:
        FileNotFoundError: The save file does not exist.
        """

        if not os.path.exists(self.save_path):
            raise FileNotFoundError(f"Save file '{self.save_path}' does not exist.")

        with open(self.save_path, "rb") as f:
            data = pickle.load(f)
            self.__characters = data["characters"]
            self.__persistent = data["persistent"]
            self.__current_section = data["current_section"]
