from wlw.utils.chapter import Chapter
from wlw.utils.character import Character
import time

CHAPTER_TITLE = "False Beginnings"
CHAPTER_NUMBER = 1

class Main(Chapter):
    def __init__(self, manager, renderer):
        super().__init__(manager, renderer)
        self.title = CHAPTER_TITLE

        self.nih = self.manager.register_character(Character("Nihira Khimaris", "f", hidden=True))
        self.emi = self.manager.register_character(Character("EdEn:TU9A-EMIL (Emil Khmaris)", "f", hidden=True))
        self.narr = self.manager.register_character(Character("Narrator", "m", True))

    def start(self):
        self.narr.speak("Two people, two stories. One choice.")
        self.narr.speak("That choice is yours, Player.")

        while True:
            self.narr.speak("Who will you choose to follow?")

            self.renderer.set_choices([
                {"title": "Nihira", "id": "female"},
                {"title": "... [COMING SOON!]", "id": "male"}
                ])

            user = self.renderer.wait_choice()

            if user == "female":
                self.manager.persistent["route"] = "f"
                break
            else:
                continue

        if self.manager.persistent["route"] == "f":
            self.f_s1()

    # female 'Commander' route start
    def f_s1(self):
        self.manager.set_section(CHAPTER_TITLE, "f_s1")
        self.manager.save()

        self.nih.speak("placeholder.")

