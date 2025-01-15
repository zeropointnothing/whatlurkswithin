import curses
import time
import logging, sys, platform

# the logger needs to be initialized before we load any other modules that require it
from wlw.utils.logger import WLWLogger
logging.setLoggerClass(WLWLogger)
log = logging.getLogger("WLWLogger")
log: WLWLogger # getLogger wont expose our custom functions

from wlw.utils.renderer import Renderer
from wlw.utils.manager import Manager
from wlw.utils.errors import *
from wlw.utils.chapter import ChapterThread
from wlw.game import chapter_modules

class WhatLurksWithin:
    def __init__(self, stdscr: curses.window):
        self.stdscr = stdscr
        self.stdscr.nodelay(True)
        self.stdscr.keypad(True)
        curses.noecho()

        self.VERSION = "0.0.0"

        self.renderer = Renderer(self.stdscr)
        self.manager = Manager("save.dat")
        self.chapter_thread = None
        self.h, self.w = stdscr.getmaxyx()

        self.TEXT_SPEED = 0.05

        self.current_choice = 0

        log.debug(f"Terminal H/W: {(self.h, self.w)}")
        log.debug(f"Text speed: {self.TEXT_SPEED}")
        log.debug("Game initialized!")

    def play_chapter(self, start):
        """
        Play a chapter.

        This is the heavy lifting function, as it handles the display of most
        features in the engine.
        """

        # chapters rely on blocking functions, so it needs to run in the background
        log.debug(f"Launching chapter {start.__module__}/{start.__name__}")
        self.chapter_thread = ChapterThread(target=start, daemon=True, name=f"chapter-thread_{start.__module__.replace(".", "_")}")
        self.chapter_thread.start()
        last_char = time.time()
        user_read = False
        waiting_on_user = False

        while self.chapter_thread.is_alive():
            newh, neww = stdscr.getmaxyx()
            if newh != self.h or neww != self.w:
                self.stdscr.clear()
            self.h, self.w = newh, neww

            k = self.stdscr.getch()

            # 'choice' rendering
            midy = self.h//2
            for i, choice in enumerate(self.renderer.choices):
                midx = (self.w//2)-(len(choice["title"])//2)
                if self.current_choice == i:
                    self.renderer.place_line(midx, midy-i, choice["title"], self.renderer.color_black_white, bold=True)
                else:
                    self.renderer.place_line(midx, midy-i, choice["title"], self.renderer.color_white_black, italic=True)

            # user input
            # 'choice' input
            if k == curses.KEY_DOWN and self.renderer.choices:
                self.current_choice -= 1
                self.current_choice %= len(self.renderer.choices)
            elif k == curses.KEY_UP and self.renderer.choices:
                self.current_choice += 1
                self.current_choice %= len(self.renderer.choices)
            elif k in [curses.KEY_ENTER, 10] and self.renderer.choices:
                self.renderer._user_chose = self.current_choice
                self.current_choice = 0
            # normal input
            elif k in [curses.KEY_ENTER, 10]:
                user_read = True

            for char in self.manager.characters:
                saying = char.saying

                if saying[0]:
                    if time.time() - last_char > self.TEXT_SPEED and not user_read: # normal increment
                        char._increment_speak_index()
                        last_char = time.time()
                    elif user_read and not waiting_on_user: # manual skip
                        char._increment_speak_index(True)
                        user_read = False
                    elif user_read and waiting_on_user and not char._is_locked: # user read text
                        char._mark_read_text()
                        waiting_on_user = False
                        user_read = False
                        break

                    self.renderer.place_line(0, 0, f"{char.name} ({user_read}, {waiting_on_user}, {char._is_locked}):")
                    self.stdscr.clrtoeol()
                    if saying[1] != -1:
                        self.renderer.place_line(0, 1, saying[0][:saying[1]])
                    else:
                        self.renderer.place_line(0, 1, saying[0])
                        waiting_on_user = True
                    self.stdscr.clrtoeol()
                    # self.renderer.place_line(0, 0, f"{char.name}: {char.saying[0][:char.saying[1]]}")

            user_read = False

            time.sleep(0.01)
        if self.chapter_thread:
            self.chapter_thread.join()

    def game_loop(self, loading: bool = False):
        """
        Main game loop for WLW.

        Automatically launches chapters, starting from the last saved location if
        'loading' is `True`.

        Args:
        loading (bool): Whether to load from save.

        """
        chapter_modules.sort(key=lambda x: x.CHAPTER_NUMBER)

        if loading:
            self.manager.load()

        for chap in chapter_modules:
            if loading and chap.CHAPTER_TITLE == self.manager.section["chapter"]:
                # print(f"SAVE: {chap.CHAPTER_TITLE}/{self.manager.section["section"]}")
                chapter_instance = chap.Main(self.manager, self.renderer)
                section_name = self.manager.section["section"]

                if hasattr(chapter_instance, section_name):
                    self.play_chapter(getattr(chapter_instance, section_name))
                    loading = False
                    continue
                else:
                    raise SectionNotFoundError(f"Section '{section_name}' does not exist within chapter '{chap.CHAPTER_TITLE}'.")
            elif loading:
                continue

            # print(f"Starting chapter: {chap.CHAPTER_TITLE} ({chap.CHAPTER_NUMBER})")
            chapter_instance = chap.Main(self.manager, self.renderer)
            self.play_chapter(chapter_instance.start)



    def main_menu(self):
        title = "WHAT LURKS WITHIN"
        
        self.renderer.set_choices([{"title": "Start New Game", "id": "start"},
                        {"title": "Load Game", "id": "load"},
                        {"title": "Quit", "id": "quit"}])

        while True:
            time.sleep(0.05)
            k = stdscr.getch()
            newh, neww = stdscr.getmaxyx()
            if newh != self.h or neww != self.w:
                self.stdscr.clear()
            self.h, self.w = newh, neww

            midy = self.h//2
            for i, choice in enumerate(self.renderer.choices):
                midx = (self.w//2)-(len(choice["title"])//2)
                if self.current_choice == i:
                    self.renderer.place_line(midx, midy-i, choice["title"], self.renderer.color_black_white, bold=True)
                else:
                    self.renderer.place_line(midx, midy-i, choice["title"], self.renderer.color_white_black, italic=True)

            self.renderer.place_line((self.w//2)-(len(title)//2), 0, str(title))
            self.stdscr.clrtoeol()
            self.stdscr.move(0,0)


            # user input
            if k == curses.KEY_DOWN:
                self.current_choice -= 1
                self.current_choice %= len(self.renderer.choices)
            if k == curses.KEY_UP:
                self.current_choice += 1
                self.current_choice %= len(self.renderer.choices)
            if k in [curses.KEY_ENTER, 10]:
                self.renderer._user_chose = self.current_choice

            # input checking
            if self.renderer.user_chose == "quit":
                return 0
            elif self.renderer.user_chose == "start":
                return 1
            elif self.renderer.user_chose:
                return 2

            stdscr.refresh()

if __name__ == "__main__":
    log.info("Hello from WLW!")
    
    log.info(f"Running on platform: {platform.platform()}")
    log.info(f"Using Python version: {platform.python_version()}")
    log.info(f"At: {time.asctime()}")
    # log.info(sys.)
    stdscr = curses.initscr()
    game = WhatLurksWithin(stdscr)

    log.info(f"WHAT LURKS WITHIN v{game.VERSION}")
    log.log_blank()

    try:
        log.debug("Entering main menu.")
        user_choice = game.main_menu()

        game.stdscr.clear()
        game.renderer.clear_choices()
        game.current_choice = 0

        if user_choice == 1:
            log.debug("Starting a new game...")
            game.game_loop()
        elif user_choice == 2:
            log.debug("Loading game from save...")
            game.game_loop(True)
        else:
            pass

    except KeyboardInterrupt: # user wants out, so we shouldn't wait on the chapter thread
        log.info("WLW exit via KeyboardInterrupt!")
        pass
    except Exception as e:
        curses.endwin()
        log.critical("WLW encountered an unrecoverable error!")
        log.error(e, exc_info=True)
        sys.exit(1)
        # raise e

    curses.endwin()
    log.info("WLW exiting gracefully.")
