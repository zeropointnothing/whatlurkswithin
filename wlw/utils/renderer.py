import curses
import time
import logging
import textwrap
from wlw.utils.logger import WLWLogger
from wlw.utils.battle import Battle

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
        curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_WHITE)
        curses.init_pair(4, curses.COLOR_WHITE, curses.COLOR_BLACK)
        curses.init_pair(5, curses.COLOR_YELLOW, curses.COLOR_WHITE)
        curses.init_pair(6, curses.COLOR_BLACK, curses.COLOR_MAGENTA)

        self.color_red_black = curses.color_pair(1)
        self.color_green_black = curses.color_pair(2)
        self.color_black_white = curses.color_pair(3)
        self.color_white_black = curses.color_pair(4)
        self.color_yellow_white = curses.color_pair(5)
        self.color_black_magenta = curses.color_pair(6)
        
        self.__battle = None
        self.__battle_result = -1

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
    
    @property
    def battle(self):
        return self.__battle
    
    @property
    def battle_result(self):
        return self.__battle_result
    
    @battle_result.setter
    def battle_result(self, to: int):
        self.__battle_result = to
        self.__battle = None

    def place_line(self, x: int, y: int, text: str, wrap: int = 0, color = -1, italic: bool = False, bold: bool = False):
        """
        Fancy wrapper for `stdscr.addstr`.

        Add a line of text to the screen.

        If `wrap` is set, the text will automatically be wrapped and placed on the next line.

        Accepts styling parameters via `color`, `italic`, and `bold`.

        Args:
        x (int): X coord.
        y (int): Y coord.
        text (str): The text to place.
        wrap (int): How far to wrap the string, if at all.
        color (int): The color to place with.
        italic (bool): Place text with the `A_ITALIC` styling.
        bold (bool): Place the text with the `A_BOLD` styling.
        """
        text = textwrap.wrap(text, wrap) if wrap else [text]

        for i, line in enumerate(text):
            if color != -1 and italic: # color/italics
                self.stdscr.addstr(y+i, x, line, color | curses.A_ITALIC)
            elif color != -1 and bold: # color/bold
                self.stdscr.addstr(y+i, x, line, color | curses.A_BOLD)
            elif italic: # italics
                self.stdscr.addstr(y+i, x, line, curses.A_ITALIC)
            elif bold: # bold
                self.stdscr.addstr(y+i, x, line, curses.A_BOLD)
            elif color != -1: # color only
                self.stdscr.addstr(y+i, x, line, color)
            else:
                self.stdscr.addstr(y+i, x, line)

            # self.stdscr.clrtoeol()
            
    def draw_box(self, sx: int, sy: int, ex: int, ey:int):
        """
        Draw a box from (`sx`, `sy`) to (`ex`, `ey`).

        Args:
        sx (int): Starting x.
        sy (int): Starting y.
        ex (int): Ending x.
        ey (int): Ending y.
        """
        for y in range(sy, ey):
            if y == sy:
                self.place_line(sx, y, "┌"+"─"*(ex-sx)+"┐")
            elif y == ey-1:
                self.place_line(sx, y, "└"+"─"*(ex-sx)+"┘")
            else:
                self.place_line(sx, y, "│"+" "*(ex-sx)+"│")

    def clear_lines(self, fy: int, ty: int):
        """
        Clear lines starting from `fy` and up to `ty`.

        Useful for when you need to clear large portions of the screen, but not the entire screen.
        """

        old_pos = self.stdscr.getyx()

        for i in range(fy, ty):
            self.stdscr.move(i, 0)
            self.stdscr.clrtoeol()
        
        self.stdscr.move(*old_pos)

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

    def start_battle(self, battle: Battle):
        """
        Set the game's active 'battle', then wait for the battle to conclude.

        Args:
        battle (Battle): The battle instance.
        """
        self.__battle = battle
        self.__battle_result = -1

        while self.__battle_result == -1:
            time.sleep(0.1)

        log.debug("JKHJKFHSJHF")

        out = self.__battle_result
        self.__battle = None
        self.__battle_result = -1

        return out
