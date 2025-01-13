from wlw.utils.manager import Manager
from wlw.utils.renderer import Renderer

class Chapter:
    def __init__(self, manager: Manager, renderer: Renderer):
        self.title = "Unnamed!"
        self.manager = manager
        self.renderer = renderer

    def start(self):
        raise NotImplementedError(f"Chapter '{self.title}' does not implement start()!")