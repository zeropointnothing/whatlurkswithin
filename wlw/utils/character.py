"""
Character class for WLW.
"""
import time

class Character:
    """
    Character class.

    Holds several important attributes for characters, such as name, sex, affinity, and pronouns.
    
    Special characters may be excluded from several functions, and should be used for characters such as the
    narrator or "system".
    """
    def __init__(self, name: str, sex, special: bool = False):
        """
        Args:
        name (str): The character's name.
        sex (str): The character's sex. Should be either 'm' or 'f'.
        special (bool): Whether the character is considered 'special'.

        Raises:
        ValueError: 'sex' was not a valid string.
        """
        self.name = name

        if sex.lower() not in ["m", "f"]:
            raise ValueError(f"Invalid character sex '{sex}' for character '{name}'. Expected 'm' or 'f'.")
        else:
            self.__sex = sex.lower()

        self.__current_text = ""
        self.__current_text_index = 0
        self.__current_text_read = False
        self.__affinity = 0
        self.__inventory = []
        self.__special = special

    @property
    def pronoun(self):
        """
        Character pronouns.

        Returns:
        dict: Dictionary containing subject, object, and possessive pronouns, based on character sex.
        """
        if self.__sex == "m":
            return {"subject": "he", "object": "him", "possessive": "his"}
        elif self.__sex == "f":
            return {"subject": "she", "object": "her", "possessive": "her"}
        else:
            raise AttributeError(f"Character sex of {self.__sex} is invalid.")    

    @property
    def sex(self):
        """
        Character sex.

        Returns:
        str: 'm' or 'f', based on the character's sex.
        """
        return self.__sex

    @property
    def affinity(self):
        """
        Character affinity.

        Returns:
        int: Character's affinity.
        """
        return self.__affinity
    
    @property
    def special(self):
        """
        Special character.

        Read-only to prevent issues with the Manager.

        Returns:
        bool: Whether the character is considered 'special'.
        """
        return self.__special

    @property
    def saying(self) -> tuple[str, int]:
        """
        What the character is saying, and far they are in saying it.
        
        When the text has been fully read, the index will be -1.

        Returns:
        tuple: Current text, current text index.
        """
        if self.__current_text_index > len(self.__current_text):
            return (self.__current_text, -1)

        return (self.__current_text, self.__current_text_index)

    def _increment_speak_index(self, max: bool = False):
        """
        Increment the text index of the character's speech.

        Should only be called by the main thread.

        Args:
        max (bool): Whether or not to completely max out the increment.
        """

        if max:
            self.__current_text_index = len(self.__current_text)+1
        else:
            self.__current_text_index += 1

    def _mark_read_text(self):
        """
        Clear the internal text variable, releasing any threads
        waiting for the user to read the text.
        """
        self.__current_text = ""

    def speak(self, text: str) -> None:
        """
        Make a character 'speak'.

        Sets the character's internal speech variables to `text`, then waits
        for the text to be read, before returning.

        Args:
        text (str): The text for the character to speak.
        """

        self.__current_text = text
        self.__current_text_index = 0

        while self.__current_text:
            time.sleep(1)
