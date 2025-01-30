"""
Character class for WLW.
"""
import time
from wlw.utils.errors import *
from wlw.utils.formatting import format_line, get_format_max_length, FormatType

class Character:
    """
    Character class.

    Holds several important attributes for characters, such as name, sex, affinity, and pronouns.
    
    Special characters may be excluded from several functions, and should be used for characters such as the
    narrator or "system".
    """
    def __init__(self, name: str, sex: str = "m", affinity: int = 0, special: bool = False, hidden: bool = False):
        """
        Args:
        name (str): The character's name.
        sex (str): The character's sex. Should be either 'm' or 'f'.
        affinity (int): The character's starting affinity.
        special (bool): Whether the character is considered 'special'.
        hidden (bool): Whether the character is 'hidden', and should fake their name as '...'.

        Raises:
        ValueError: 'sex' was not a valid string.
        """

        self.hidden = hidden

        if sex.lower() not in ["m", "f"]:
            raise ValueError(f"Invalid character sex '{sex}' for character '{name}'. Expected 'm' or 'f'.")
        else:
            self.__sex = sex.lower()
        try:
            affinity = int(str(affinity)) # account for bools, since they're a subclass of int
        except ValueError as e:
            raise TypeError(f"Starting affinity must be an 'int', not '{affinity.__class__.__name__}'.") from e

        self._name = name
        self.__current_text = []
        self.__current_text_index = 0
        self.__current_text_thought = False
        self.__current_text_lock = False
        self.__affinity = affinity
        self.__AFFINITY_LEVELS = {
            "ADORED": 95,
            "CHERISHED": 80,
            "CLOSE": 50,
            "TRUSTED": 20,
            "NEUTRAL": 0,
            "TENSE": -10,
            "DISLIKED": -20,
            "HATED": -50,
            "DESPISED": -80
        }
        self.__inventory = []
        self.__special = special

    @property
    def name(self):
        """
        Character name.

        Automatically switches between the 'hidden' view and normal view.

        For raw name access, use the `_name` variable.
        """
        if self.hidden:
            return "???"
        else:
            return self._name

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
    def affinity_level(self):
        """
        Character affinity level.

        For positive levels, the greatest value is returned.
        For negatives, the lowest is returned.

        Returns:
        str: Character's affinity level.
        """
        affin = None

        for level in self.__AFFINITY_LEVELS:
            if self.__affinity >= 0 and self.__affinity >= self.__AFFINITY_LEVELS[level]:
                return level
            # negatives are reversed, so we want the last result.
            elif self.__affinity < 0 and self.__affinity <= self.__AFFINITY_LEVELS[level]:
                affin = level

        return affin

    @property
    def affinity(self):
        """
        Character affinity.

        Returns:
        int: Character's affinity.
        """
        return self.__affinity
    
    @affinity.setter
    def affinity(self, to: int):
        if not isinstance(to, int):
            raise TypeError(f"Affinity value must be 'int', not '{to.__class__.__name__}'")
    
        self.__affinity = to

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
    def saying(self) -> tuple[list[tuple[FormatType, str|float]], int, bool]:
        """
        What the character is saying, how far they are in saying it, and whether it's a thought.
        
        When the text has been fully read, the index will be -1.

        Returns:
        tuple: Current text, current text index, is_thought.
        """
        if self.__current_text_index > get_format_max_length(self.__current_text):
            return (self.__current_text, -1, self.__current_text_thought)

        return (self.__current_text, self.__current_text_index, self.__current_text_thought)

    @property
    def _is_locked(self) -> bool:
        """
        Whether or not the current character's text is 'locked'.

        Returns:
        bool: The character's lock status.
        """
        return self.__current_text_lock

    def lock_speech(self):
        """
        Locks a character's speech, preventing it from being cleared.

        Raises:
        LockError: The character was already locked.
        """
        if self.__current_text_lock:
            raise LockError(f"Character '{self.name}' is already locked!")

        self.__current_text_lock = True

    def unlock_speech(self):
        """
        Unlocks a character's speech.

        To properly unlock the character, calls the `_mark_read_text` function.

        Raises:
        LockError: The character was already unlocked.
        """
        if not self.__current_text_lock:
            raise LockError(f"Character '{self.name}' is already unlocked!")

        self.__current_text_lock = False
        self._mark_read_text()

    def _increment_speak_index(self, max: bool = False):
        """
        Increment the text index of the character's speech.

        Should only be called by the main thread.

        Args:
        max (bool): Whether or not to completely max out the increment.
        """

        if max:
            self.__current_text_index = get_format_max_length(self.__current_text)+1
        else:
            self.__current_text_index += 1
    def _decrement_speak_index(self):
        """
        Decrement the text index of the character's speech.

        Should only called by the main thread.
        """

        self.__current_text_index -= 1

    def _mark_read_text(self):
        """
        Clear the internal text variable, releasing any threads
        waiting for the user to read the text.
        """
        self.__current_text = []

    def speak(self, text: str, thought: bool = False, lock: bool = False) -> None:
        """
        Make a character 'speak'.

        Sets the character's internal speech variables to `text`, then waits
        for the text to be read, before returning.

        If `lock` is set, this function will immediately return after locking the character's
        speech.

        If `thought` is set, the renderer will likely display it with italics instead of quotation marks.

        Args:
        text (str): The text for the character to speak.
        thought (bool): Whether the text is a thought.
        lock (bool): Whether to lock the character's speech.
        """

        if not isinstance(text, str):
            raise TypeError(f"Invalid type '{text.__class__.__name__}'. Expected 'str'")

        fmt = format_line(text) # we need to format here since it's computationally expensive to run RegEx.

        self.__current_text = fmt
        self.__current_text_thought = thought
        self.__current_text_index = 0

        if lock:
            self.lock_speech()

        while self.__current_text and not self.__current_text_lock:
            time.sleep(0.05)
