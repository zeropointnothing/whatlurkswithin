from wlw.utils.chapter import Chapter
from wlw.utils.character import Character

CHAPTER_TITLE = "False Beginnings"
CHAPTER_NUMBER = 1

class Main(Chapter):
    def __init__(self, manager, renderer):
        super().__init__(manager, renderer)
        self.title = CHAPTER_TITLE

        self.aki = self.manager.register_character(Character("Aki", "f"))
        self.chloe = self.manager.register_character(Character("Chloe", "f"))
        self.narr = self.manager.register_character(Character("Narrator", "m"))

    def start(self):
        self.s1()

    def s1(self):
        self.manager.set_section(CHAPTER_TITLE, "s1")
        self.manager.save()

        self.aki.speak("Hai! :3")
        self.chloe.speak("Hello, Aki!")
        self.aki.speak("Where are we?... I don't recognize this place.")
        self.narr.speak("Aki looks around nervously, wary of her new surroundings.")
        self.chloe.speak("I'm not sure...")

        self.s2()


    def s2(self):
        self.manager.set_section(CHAPTER_TITLE, "s2")
        self.manager.save()
        self.narr.speak("Twenty days later...")
