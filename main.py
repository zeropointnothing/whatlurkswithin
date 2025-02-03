import curses
import time
import logging, sys, os, platform
import random
import re

# the logger needs to be initialized before we load any other modules that require it
from wlw.utils.logger import WLWLogger
logging.setLoggerClass(WLWLogger)
log = logging.getLogger("WLWLogger")
log: WLWLogger # getLogger wont expose our custom functions

from wlw.utils.renderer import Renderer
from wlw.utils.manager import Manager
from wlw.utils.errors import *
from wlw.utils.chapter import ChapterThread
from wlw.utils.battle import Battle, BattleCharacter
from wlw.utils.discord import RichPresence
from wlw.utils.formatting import format_line, get_format_max_length, get_format_up_to, FormatType
from wlw.game import chapter_modules

class WhatLurksWithin:
    def __init__(self, stdscr: curses.window):
        self.stdscr = stdscr
        self.stdscr.nodelay(True)
        self.stdscr.keypad(True)
        curses.noecho()

        self.VERSION = "0.0.0"
        self.RPC_ID = "1333980355010629765"
        self.RPC_PING_INTERVAL = 15
        self.RPC_LAST_PING = 0

        self.renderer = Renderer(self.stdscr)
        self.manager = Manager(os.path.join(self.save_location, "save.dat"))
        self.rpc = RichPresence(self.RPC_ID)
        self.chapter_thread = None
        self.h, self.w = stdscr.getmaxyx()

        self.TEXT_SPEED = 0.05

        self.current_choice = 0

        log.debug(f"Terminal H/W: {(self.h, self.w)}")
        log.debug(f"Text speed: {self.TEXT_SPEED}")
        log.debug("Game initialized!")
    
    @property
    def save_location(self):
        """
        Determine the path to the save file depending on the detected system.

        Returns:
        str: The save file path.

        Raises:
        PlatformError: The platform is either unknown or unsupported.
        """
        if platform.system() == "Linux":
            return os.path.join(os.getenv("XDG_DATA_HOME", os.path.expanduser("~/.local/share")), "whatlurkswithin")
        elif platform.system() == "Windows":
            return os.path.join(os.getenv('LOCALAPPDATA'), "whatlurkswithin")
        else:
            raise PlatformError(f"Platform '{platform.system()}' is unsupported! Unable to determine file paths!")

    @property
    def config_location(self):
        """
        Determine the path to the config file depending on the system.

        Returns:
        str: The config file path.

        Raises:
        PlatformError: The platform is either unknown or unsupported.
        """
        if platform.system() == "Linux":
            return os.path.join(os.getenv('XDG_CONFIG_HOME', os.path.expanduser('~/.config')), "whatlurkswithin")
        elif platform.system() == 'Windows':
            return os.path.join(os.getenv('APPDATA'), "whatlurkswithin")
        else:
            raise PlatformError(f"Platform '{platform.system()}' is unsupported! Unable to determine file paths!")

    def history(self):
        """
        Render text history.

        Provides a frontend for viewing `manager.history`.
        """
        TITLE = " < HISTORY > "
        HELP = " <ESC>: Exit "
        wrap_offset = 0 # first iteration needs this

        while True:
            # height stuff
            k = self.renderer.stdscr.getch()
            newh, neww = stdscr.getmaxyx()
            if newh != self.h or neww != self.w:
                self.renderer.stdscr.clear()
            self.h, self.w = newh, neww
            h_center = self.h//2
            w_center = self.w//2

            self.renderer.draw_box(0, 0, self.w-2, self.h-1)
            self.renderer.place_line(w_center-(len(TITLE)//2), 0, TITLE) # draw the title


            start_index = max(0, len(self.manager.history) - (self.h - 3 - wrap_offset)) # we need to shift up, not down
            wrap_offset = 0 # since we're making a list, we need to shift further values down
            for i, entry in enumerate(self.manager.history[start_index:]):
                if 1+i+wrap_offset > self.h-3:
                    continue
                self.renderer.place_line(2, 1+i+wrap_offset, f"{entry["title"]}: ")

                prefix = "\"" if entry["thought"] else ""
                italic = True if entry["thought"] else False # thoughts should be italic regardless of formatting

                x_offset = 4+len(entry["title"]) if not prefix else 4+len(entry["title"])
                y_offset = 1+i+wrap_offset

                for chunk in entry["text"]: # in order to render with different styles, we need to do it chunk by chunk
                    if chunk[0] in [FormatType.SKIP, FormatType.WAIT]: # we don't need to render these
                        continue
                    words = re.split(r"(\s+)", chunk[1])
                    for word in words:
                        if x_offset + len(word) >= self.w - 4: # text wrapping
                            x_offset = 4+len(entry["title"])
                            y_offset += 1
                            wrap_offset += 1
                        if chunk[0] == FormatType.ITALIC:
                            self.renderer.place_line(x_offset, y_offset, word, italic=True)
                        elif chunk[0] == FormatType.BOLD:
                            self.renderer.place_line(x_offset, y_offset, word, bold=True)
                        else:
                            self.renderer.place_line(x_offset, y_offset, word, italic=italic)
                        x_offset += len(word)

                # self.renderer.place_line(2, i+2, f"{entry["title"]}: {entry["text"]}")

            self.renderer.place_line(self.w-len(HELP)-2, self.h-2, HELP)
            self.renderer.stdscr.refresh()

            # user input
            if k == 27:
                return

            time.sleep(0.05)


    def battsys(self, batt: Battle):
        """
        BATTleSYStem.

        Switches the Main renderer over to a basic battle system.

        Automatically returns the result of the battle.

        Args:
        batt (Battle): The battle to render.

        Returns:
        int: The battle's result.
        """
        battle_party = batt.allies+batt.foes

        acted = False
        turn = 0

        user_input = ""
        user_select = 0
        command = ""

        mode = "command" # command, select, view
        last_render = time.time()

        display = None
        display_padding_x = 5
        display_padding_y = 2

        while True:
            if acted:
                batt.next_turn()
                turn += 1
                acted = False

            # height stuff
            k = self.renderer.stdscr.getch()
            newh, neww = stdscr.getmaxyx()
            if newh != self.h or neww != self.w:
                self.renderer.stdscr.clear()
            self.h, self.w = newh, neww
            h_center = self.h//2
            w_center = self.w//2

            if all([not _.alive for _ in batt.allies]): # all allies down
                return 0
            if all([not _.alive for _ in batt.foes]): # all foes down (yay!)
                return 1


            # render foes
            box_number = len(batt.foes)
            box_width = max([len(_.name) for _ in battle_party]) + 5 + len(str(len(battle_party))) # auto resize based on maximum name length
            box_height = 10
            box_offset = (self.w-(box_number*box_width))//(box_number+1)

            draw_startx = box_offset
            for i, foe in enumerate(batt.foes):
                title = f"> {battle_party.index(foe)}:{foe.name} <" if foe == battle_party[batt.turn] else f"{battle_party.index(foe)}:{foe.name}"
                color = self.renderer.color_red_black if foe == battle_party[user_select] else -1

                draw_starty = 0

                self.renderer.draw_box(draw_startx, draw_starty, draw_startx+box_width, draw_starty+box_height)
                self.renderer.place_line((draw_startx+1)+(box_width//2)-(len(title)//2), draw_starty+1, title, color=color)
                self.renderer.place_line((draw_startx+1), draw_starty+2, "─"*box_width)
                self.renderer.place_line((draw_startx+1), draw_starty+3, f"HP:{foe.hitpoints}" if foe.hitpoints > 0 else "!DOWN!")
                self.renderer.place_line((draw_startx+1), draw_starty+5, "─"*box_width)

                for b, buff in enumerate(foe.buffs):
                    self.renderer.place_line((draw_startx+1), draw_starty+6+b, f"{buff.name}:{buff.buff_length}T")
                draw_startx += box_width+box_offset

            # render midtext
            message = f"TURN {turn+1} ({battle_party[batt.turn].name})"
            self.renderer.stdscr.move(h_center-1, 0)
            self.renderer.stdscr.clrtoeol()
            self.renderer.place_line(w_center-len(message)//2, h_center-1, message)
            # battle messages
            message = f"{batt.get_display(time.time()-last_render)[0]}"
            self.renderer.stdscr.move(h_center, 0)
            self.renderer.stdscr.clrtoeol()
            self.renderer.place_line(w_center-len(message)//2, h_center, message)

            # render allies
            box_number = len(batt.allies)
            box_offset = (self.w-(box_number*box_width))//(box_number+1)

            draw_startx = box_offset
            for i, ally in enumerate(batt.allies):
                title = f"> {battle_party.index(ally)}:{ally.name} <" if ally == battle_party[batt.turn] else f"{battle_party.index(ally)}:{ally.name}"
                color = self.renderer.color_green_black if ally == battle_party[user_select] else -1

                draw_starty = self.h-box_height-1
                self.renderer.draw_box(draw_startx, draw_starty, draw_startx+box_width, draw_starty+box_height)
                self.renderer.place_line((draw_startx+1)+(box_width//2)-(len(title)//2), draw_starty+1, title, color=color)
                self.renderer.place_line((draw_startx+1), draw_starty+2, "─"*box_width)
                self.renderer.place_line((draw_startx+1), draw_starty+3, f"HP:{ally.hitpoints}" if ally.hitpoints > 0 else "!DOWN!")
                self.renderer.place_line((draw_startx+1), draw_starty+5, "─"*box_width)

                for b, buff in enumerate(ally.buffs):
                    self.renderer.place_line((draw_startx+1), draw_starty+6+b, f"{buff.name}:{buff.buff_length}T")
                draw_startx += box_width+box_offset

            # render visuals
            if mode == "visual" and isinstance(display, BattleCharacter):
                title_color = self.renderer.color_green_black if display in batt.allies else self.renderer.color_red_black
                title = f"\"{display.name}\" ({battle_party.index(display)})"

                self.renderer.draw_box(display_padding_x, display_padding_y, self.w-display_padding_x, self.h-display_padding_y)
                self.renderer.place_line((self.w//2)-len(title)//2, display_padding_y+1, title, color=title_color) # title

                self.renderer.place_line(display_padding_x+1, display_padding_y+3, "─"*(self.w-display_padding_x*2)) # line
                stats_title = " STATS "
                self.renderer.place_line((self.w//2)-(len(stats_title)//2), display_padding_y+3, stats_title)
                self.renderer.place_line(display_padding_x+1, display_padding_y+4, f"HP:{display.hitpoints}") # HP

                self.renderer.place_line(display_padding_x+1, display_padding_y+6, "─"*(self.w-display_padding_x*2)) # line
                buff_title = " ACTIVE BUFFS "
                self.renderer.place_line((self.w//2)-(len(buff_title)//2), display_padding_y+6, buff_title)
                for i, buff in enumerate(display.buffs):
                    self.renderer.place_line(display_padding_x+1, display_padding_y+7+i, f"{i} - {buff.name}:{buff.buff_length}T")

                self.renderer.place_line(display_padding_x+1, display_padding_y+8+len(display.buffs), "─"*(self.w-display_padding_x*2)) # line
                atk_title = " ATTACKS "
                self.renderer.place_line((self.w//2)-(len(atk_title)//2), display_padding_y+8+len(display.buffs), atk_title)
                for i, atk in enumerate(display.attacks):
                    self.renderer.place_line(display_padding_x+1, display_padding_y+9+len(display.buffs)+i, f"{atk.name} ({atk.damage}/{atk.buff.name if atk.buff else "NONE"}): '{atk.description}'")

            # render ui
            if mode == "command":
                self.renderer.place_line(0, self.h-1, f"COMMAND MODE >>> {user_input}")
                self.renderer.stdscr.clrtoeol()
            elif mode == "visual":
                self.renderer.place_line(0, self.h-1, f"VISUAL MODE ~~~")
                self.renderer.stdscr.clrtoeol()


            # auto foe attacking stuff
            if (battle_party[batt.turn] in batt.foes and battle_party[batt.turn].hitpoints > 0) and not batt.get_display()[1]:
                atk_u = battle_party[batt.turn].attacks[random.randint(0, len(battle_party[batt.turn].attacks)-1)]
                atk_w = random.choice([_ for _ in batt.allies if _.hitpoints > 0])

                # print(f"CPU  ATK: {battle_party[batt.turn].name} -> {atk_w.name}, {atk_u.name}")

                batt.attack(atk_w, battle_party[batt.turn], atk_u)
                batt.set_display(f"'{battle_party[batt.turn].name} ({batt.turn})' uses '{atk_u.name}' on '{atk_w.name}'!", 2)

                acted = True
            elif battle_party[batt.turn] in batt.foes and not batt.get_display()[1]: # skip dead 
                batt.set_display(f"'{battle_party[batt.turn].name} ({batt.turn})' skipped!", 1)
                acted = True

            # skip dead allies
            if (battle_party[batt.turn] in batt.allies and battle_party[batt.turn].hitpoints <= 0):
                acted = True
                continue

            # prevent user interaction on enemy turns
            if battle_party[batt.turn] in batt.foes:
                last_render = time.time()
                time.sleep(0.05)
                continue

            elif command == "view":
                mode = "visual"
                command = ""
                display = battle_party[user_select]
            elif command.startswith("attack "):
                by = battle_party[batt.turn]
                whom = battle_party[user_select]

                if whom.hitpoints <= 0:
                    batt.set_display(f"'{whom.name}' is already down!", 2)
                    command = ""
                    continue

                try:
                    attack = by.get_attack(command.split(" ")[1])
                    batt.set_display(f"'{by.name} ({batt.turn})' uses '{attack.name}' on '{whom.name}'!", 2)
                    
                    batt.attack(whom, by, attack)
                    acted = True
                except ValueError:
                    batt.set_display(f"No such attack '{command.split(" ")[1]}'!", 2)
                except InvalidTargetError as e:
                    batt.set_display(e, 3)
                command = ""
            elif command == "skip":
                acted = True
                command = ""

            if k in [8, 127, curses.KEY_BACKSPACE]: # backspace (duh)
                user_input = user_input[:len(user_input)-1]
            elif k == curses.KEY_RIGHT:
                user_select += 1
                user_select %= len(battle_party)
            elif k == curses.KEY_LEFT:
                user_select -= 1
                user_select %= len(battle_party)
            elif k in [10, 13, curses.KEY_ENTER] and mode == "command":
                command = user_input
                user_input = ""
                
            elif 0 <= k <= 255:  # ASCII range
                char = chr(k)
                if char.isalpha() or char.isdigit() or char == " ":  # Check if it's an alphabetic character
                    user_input = user_input + char
                    k = -1
                elif k == 27:  # ESC key
                    self.renderer.stdscr.clear()
                    if mode == "visual":
                        mode = "command"
                        user_input = ""
                        command = ""
                        display = None
                    else:
                        raise KeyboardInterrupt("ESC Pressed.")
                else:
                    pass

            last_render = time.time()
            time.sleep(0.05)


    def play_chapter(self, start):
        """
        Play a chapter.

        Base Renderer.

        This is the heavy lifting function, as it handles the display of most
        features in the engine.
        """

        ###
        ## Quite an ugly function, with MANY loops due to the complexities with formatting. Pay attention to comments!
        ###

        # chapters rely on blocking functions, so it needs to run in the background
        log.info(f"Launching chapter {start.__module__} ({start.__name__})")
        self.chapter_thread = ChapterThread(target=start, daemon=True, name=f"chapter-thread_{start.__module__.replace('.', '_')}")
        self.chapter_thread.start()
        last_char = time.time()
        temp_wait = 0
        user_read = False
        waiting_on_user = False

        self.RPC_LAST_PING = time.time()

        while self.chapter_thread.is_alive():
            k = self.stdscr.getch()
            newh, neww = stdscr.getmaxyx()
            if newh != self.h or neww != self.w:
                self.stdscr.clear()
            self.h, self.w = newh, neww

            # rpc health check, we should try and re-establish the connection if it dies
            if time.time() - self.RPC_LAST_PING > self.RPC_PING_INTERVAL:
                self.RPC_LAST_PING = time.time()
                if not self.rpc.is_ready and self.rpc.rpc_supported: # connection was broken
                    log.debug("RPC connection was lost! Attempting to re-establish...")
                    self.rpc._disconnect() # cleanup
                    self.rpc._connect() # try to reconnect
                    self.rpc._authenticate()
                    self.rpc.reload_state()


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
            elif k != -1 and chr(k) in ["h", "H"]:
                self.stdscr.clear()
                log.debug("Opening History.")
                self.history()
                log.debug("Returning to main Renderer.")
                self.stdscr.clear()

            if self.renderer.battle:
                self.stdscr.clear()
                log.debug("Starting battle!")
                out = self.battsys(self.renderer.battle)
                log.debug(f"Battle ended with result: {out}")
                self.renderer.battle_result = out
                self.stdscr.clear()

            for char in self.manager.characters: # render character speech. the mess begins...
                saying = char.saying

                if saying[0]:
                    self.manager._add_history(saying[2], char.name, saying[0]) # attempt to add the current text to our history

                    if temp_wait and time.time() - last_char > temp_wait: # temp wait can adjust how long we wait
                        char._increment_speak_index()
                        last_char = time.time()
                        temp_wait = 0
                    elif not temp_wait and (time.time() - last_char > self.TEXT_SPEED and not user_read): # normal increment
                        char._increment_speak_index()
                        last_char = time.time()
                    elif user_read and not waiting_on_user: # manual skip
                        char._increment_speak_index(True)
                        user_read = False
                        temp_wait = 0
                    elif user_read and waiting_on_user and not char._is_locked: # user read text
                        char._mark_read_text()
                        waiting_on_user = False
                        user_read = False
                        # self.renderer.clear_lines(1, self.h) # text wrapping might have left some stuff behind
                        self.stdscr.move(2, 2)
                        temp_wait = 0
                        break

                    # pretty box around the text/title
                    self.renderer.draw_box(0, 0, self.w-2, self.h-1)
                    self.renderer.place_line(1, 0, f" {char.name} ({user_read}, {waiting_on_user}, {char._is_locked}) ")

                    prefix = "\"" if not saying[2] else ""
                    italic = True if saying[2] else False # thoughts should be italic regardless of formatting

                    if saying[1] != -1:
                        # pre render maths
                        splfmt = get_format_up_to(saying[0], saying[1]) # split the format list by our current text index to preserve scrolling text
                        x_offset = 2 if not prefix else 3
                        y_offset = 2
                        self.renderer.place_line(x_offset-1, y_offset, prefix)

                        for chunk in splfmt: # in order to render with different styles, we need to do it chunk by chunk                            
                            if chunk[0] == FormatType.SKIP: # forcefully skip the character by faking user interaction
                                user_read = True
                                waiting_on_user = False
                                char._mark_read_text()
                                break
                            elif chunk[0] == FormatType.WAIT:
                                # time.sleep(float(chunk[1]))
                                char._decrement_speak_index() # since this WAIT will be removed, we need to backtrack by one
                                temp_wait = float(chunk[1])
                                saying[0].remove(chunk)
                                break # break out of the loop to prevent jittery cursor
                            else:
                                words = re.split(r"(\s+)", chunk[1])
                                for word in words:
                                    if x_offset + len(word) >= self.w - 4: # text wrapping
                                        x_offset = 2
                                        y_offset += 1
                                    if chunk[0] == FormatType.ITALIC:
                                        self.renderer.place_line(x_offset, y_offset, word, italic=True)
                                    elif chunk[0] == FormatType.BOLD:
                                        self.renderer.place_line(x_offset, y_offset, word, bold=True)
                                    else:
                                        self.renderer.place_line(x_offset, y_offset, word, italic=italic)
                                    x_offset += len(word)

                        # self.renderer.place_line(2, 2, f"{prefix}{saying[0][:saying[1]]}", self.w-4, italic=italic)
                    elif saying[1] == -1: # text wrapping
                        x_offset = 2 if not prefix else 3
                        y_offset = 2
                        self.renderer.place_line(x_offset-1, y_offset, prefix)

                        for chunk in saying[0]: # still render chunk by chunk, but render the entire line instead
                            if chunk[0] == FormatType.WAIT: # special value, we should skip them
                                continue
                            elif chunk[0] == FormatType.SKIP: # forcefully skip the character by faking user interaction
                                user_read = True
                                waiting_on_user = False
                                char._mark_read_text()
                                break
                            else:
                                words = re.split(r"(\s+)", chunk[1])
                                for word in words:
                                    if x_offset + len(word) >= self.w - 4:
                                        x_offset = 2
                                        y_offset += 1
                                    if chunk[0] == FormatType.ITALIC:
                                        self.renderer.place_line(x_offset, y_offset, word, italic=True)
                                    elif chunk[0] == FormatType.BOLD:
                                        self.renderer.place_line(x_offset, y_offset, word, bold=True)
                                    else:
                                        self.renderer.place_line(x_offset, y_offset, word, italic=italic)
                                    x_offset += len(word)
                        waiting_on_user = True

                        self.renderer.place_line(x_offset, y_offset, prefix)
                    # self.renderer.place_line(0, 0, f"{char.name}: {char.saying[0][:char.saying[1]]}")

            # 'help' rendering
            help_text = " <ENTER>: Continue, h: History "
            self.renderer.place_line(self.w-len(help_text)-2, self.h-2, help_text)

            user_read = False

            # 'choice' rendering
            midy = self.h//2
            for i, choice in enumerate(self.renderer.choices):
                midx = (self.w//2)-(len(choice["title"])//2)
                if self.current_choice == i:
                    self.renderer.place_line(midx, midy-i, choice["title"], 0, self.renderer.color_black_white, bold=True)
                else:
                    self.renderer.place_line(midx, midy-i, choice["title"], 0, self.renderer.color_white_black, italic=True)


            time.sleep(0.01)
        if self.chapter_thread:
            log.info(f"Waiting on chapter {start.__module__} ({start.__name__}) to close...")
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
            log.debug(f"Initializing chapter {chap.__name__}")
            if loading and chap.CHAPTER_TITLE == self.manager.section["chapter"]:
                # print(f"SAVE: {chap.CHAPTER_TITLE}/{self.manager.section["section"]}")
                chapter_instance = chap.Main(self.manager, self.renderer)
                section_name = self.manager.section["section"]

                if hasattr(chapter_instance, section_name):
                    # set the state while we still have access to these
                    self.rpc.set_state(self.rpc.ActivityType.PLAYING, f"Chapter {chap.CHAPTER_NUMBER}: {chap.CHAPTER_TITLE}", "Continuing their story...", int(time.time()), "nihira_goober_1", "wlwlwlw")
                    self.play_chapter(getattr(chapter_instance, section_name))
                    loading = False
                    continue
                else:
                    raise SectionNotFoundError(f"Section '{section_name}' does not exist within chapter '{chap.CHAPTER_TITLE}'.")
            elif loading:
                continue

            # print(f"Starting chapter: {chap.CHAPTER_TITLE} ({chap.CHAPTER_NUMBER})")
            chapter_instance = chap.Main(self.manager, self.renderer)
            self.rpc.set_state(self.rpc.ActivityType.PLAYING, f"Chapter {chap.CHAPTER_NUMBER}: {chap.CHAPTER_TITLE}", "Writing their story...", int(time.time()), "nihira_goober_1", "wlwlwlw")
            self.play_chapter(chapter_instance.start)



    def main_menu(self):
        title = "WHAT LURKS WITHIN"
        
        self.rpc.set_state(self.rpc.ActivityType.PLAYING, "~~~", "Main Menu", int(time.time()), "nihira_goober_1", "what did you expect here? lol")

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
                    self.renderer.place_line(midx, midy-i, choice["title"], 0, self.renderer.color_black_white, bold=True)
                else:
                    self.renderer.place_line(midx, midy-i, choice["title"], 0, self.renderer.color_white_black, italic=True)

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


    try:
        stdscr = curses.initscr()
        game = WhatLurksWithin(stdscr)

        log.info(f"WHAT LURKS WITHIN v{game.VERSION}")
        log.debug(f"Saving app data to: {game.save_location}.")
        log.debug(f"Saving config data to: {game.config_location}.")
        log.log_blank()

        # spin up Rich Presence
        game.rpc._connect()
        game.rpc._authenticate()

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
        game.rpc._disconnect()
        log.critical("WLW encountered an unrecoverable error!")
        log.error(e, exc_info=True)
        sys.exit(1)
        # raise e

    curses.endwin()
    game.rpc._disconnect()
    log.info("WLW exiting gracefully.")
