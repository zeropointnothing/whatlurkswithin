import curses
import time
import logging
from wlw.utils.logger import WLWLogger

logging.setLoggerClass(WLWLogger)
log = logging.getLogger("WLWLogger")
log: WLWLogger

class Renderer:
    """
    Renderer class.

    Contains several useful methods for rendering in curses.

    Additionally, contains several important user-related methods.
    """
    def __init__(self, stdscr: curses.window):
        self.stdscr = stdscr

        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_WHITE)
        curses.init_pair(3, curses.COLOR_WHITE, curses.COLOR_BLACK)
        curses.init_pair(4, curses.COLOR_YELLOW, curses.COLOR_WHITE)

        self.color_red_black = curses.color_pair(1)
        self.color_black_white = curses.color_pair(2)
        self.color_white_black = curses.color_pair(3)
        self.color_yellow_white = curses.color_pair(4)
        
        self.__choices = []
        self.__choices_response = -1

    @property
    def user_chose(self):
        """
        The user's response from 'set_choices'.

        Returns:
        str: The user's response.
        """
        if self.__choices_response == -1:
            return ""
        else:
            return self.__choices[self.__choices_response]["id"]

    @user_chose.setter
    def _user_chose(self, to: int):
        """
        Internal property to set the user's choice.

        Should not be access by scripts.

        Args:
        to (int): The choice to change to.

        Raises:
        ValueError: Attempted to set the user's choice to one that doesn't exist.
        """
        if to <= len(self.__choices) and to >= 0:
            self.__choices_response = to
        else:
            raise ValueError("Cannot select answer greater or less than the amount of choices!")

    @property
    def choices(self):
        return self.__choices

    def place_line(self, x, y, text: str, color = -1, italic: bool = False, bold: bool = False):
        if color != -1 and italic: # color/italics
            self.stdscr.addstr(y, x, text, color | curses.A_ITALIC)
        elif color != -1 and bold: # color/bold
            self.stdscr.addstr(y, x, text, color | curses.A_BOLD)
        elif italic: # italics
            self.stdscr.addstr(y, x, text, curses.A_ITALIC)
        elif bold: # bold
            self.stdscr.addstr(y, x, text, curses.A_BOLD)
        elif color != -1: # color only
            self.stdscr.addstr(y, x, text, color)
        else:
            self.stdscr.addstr(y, x, text)

    def clear_choices(self):
        """
        Clears the current choices.
        """
        self.__choices_response = -1
        self.__choices = []

        log.debug("Cleared choices!")

    def set_choices(self, choices: list[dict]):
        """
        Set player choices.

        Will enable a user interface they can select choices from.
        Upon choosing, the 'user_chose' property will update.

        Example:
        ```python
        [{"title": "Say hello", "id": "accept"}, {"title": "Refuse to greet them", "id": "refuse"}]
        ```

        Args:
        choices (list[dict]): A list of choices.
        """
        for choice in choices:
            if not isinstance(choice, dict):
                raise TypeError(f"Choice '{choice}' is not a dict!")

        self.clear_choices()

        self.__choices = choices[::-1]
        log.debug(f"User choices is now: {self.__choices}")

    def wait_choice(self) -> str:
        """
        Halt the current thread until a choice has been made, then return that choice.

        Clears the choice menu and screen upon exit.

        Returns:
        str: The user's choice.
        """

        while not self.user_chose:
            time.sleep(0.1)

        out = self.user_chose

        self.clear_choices()
        self.stdscr.clear()

        return out
