"""
Character class for WLW.
"""
import time

class Character:
    """
    Character class.

    Holds several important attributes for characters, such as name, sex, affinity, and pronouns.
    """
    def __init__(self, name: str, sex):
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
    def saying(self) -> tuple[str, int]:
        """
        What the character is saying, and far they are in saying it.
        
        Clears the character's speach once it has been fully read.

        Returns:
        tuple: Current text, current text index.
        """
        self.__current_text_read = True

        if self.__current_text_index > len(self.__current_text):
            self.__current_text = ""
            return ("", 0)

        return (self.__current_text, self.__current_text_index)

    def _increment_speak_index(self):
        """
        Increment the text index of the character's speach.

        Should only be called by the main thread.
        """
        self.__current_text_index += 1
        self.__current_text_read = False

    def speak(self, text: str) -> None:
        """
        Make a character 'speak'.

        Sets the character's internal speach variables to `text`, then waits
        for the text to be read, before returning.

        Args:
        text (str): The text for the character to speak.
        """

        self.__current_text = text
        self.__current_text_index = 0

        while self.__current_text or not self.__current_text_read:
            time.sleep(1)
