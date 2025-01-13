from wlw.utils.chapter import Chapter

CHAPTER_TITLE = "Chapter Two"
CHAPTER_NUMBER = 2

class Main(Chapter):
    def __init__(self, manager, renderer):
        super().__init__(manager, renderer)
        self.title = CHAPTER_TITLE

        self.aki = self.manager.get_character("Aki")
        self.chloe = self.manager.get_character("Chloe")

    def start(self):
        self.aki.speak("mow :3")
        self.chloe.speak("Yes.")
