import curses
import time
import threading
from wlw.utils.renderer import Renderer
from wlw.utils.manager import Manager
from wlw.game import chapter_modules

class WhatLurksWithin:
    def __init__(self, stdscr: curses.window):
        self.stdscr = stdscr
        self.stdscr.nodelay(True)
        self.stdscr.keypad(True)
        curses.noecho()

        self.renderer = Renderer(self.stdscr)
        self.manager = Manager("save.dat")
        self.h, self.w = stdscr.getmaxyx()

        self.current_choice = 0

    def play_chapter(self, start):
        """
        Play a chapter.
        """

        chapter_thread = threading.Thread(target=start, daemon=True, name="chapter-thread")
        chapter_thread.start()

        while chapter_thread.is_alive():
            for char in self.manager.characters:
                if char.saying[0]:
                    char._increment_speak_index()
                    self.renderer.place_line(0, 0, f"{char.name}: {char.saying[0][:char.saying[1]]}")
                    self.stdscr.refresh()
                    # if not char.saying[0]:
                    #     print("\n")

            time.sleep(0.05)

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
                    raise ImportError(f"Section '{section_name}' does not exist within chapter '{chap.CHAPTER_TITLE}'.")
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
            self.h, self.w = stdscr.getmaxyx()
            
            midy = self.h//2
            for i, choice in enumerate(self.renderer.choices):
                midx = (self.w//2)-(len(choice["title"])//2)
                if self.current_choice == i:
                    self.renderer.place_line(midx, midy-i, choice["title"], self.renderer.color_black_white)
                else:
                    self.renderer.place_line(midx, midy-i, choice["title"], self.renderer.color_white_black)

            self.renderer.place_line((self.w//2)-(len(title)//2), 0, str(self.current_choice))
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
    stdscr = curses.initscr()
    game = WhatLurksWithin(stdscr)

    try:
        user_choice = game.main_menu()

        game.stdscr.clear()

        if user_choice == 1:
            game.game_loop()
        elif user_choice == 2:
            game.game_loop(True)
        else:
            pass

    except KeyboardInterrupt:
        pass
    except Exception as e:
        curses.endwin()
        raise e

    curses.endwin()
