from wlw.utils.manager import Manager
from wlw.utils.renderer import Renderer

class Chapter:
    """
    Base class for all chapters.
    """
    def __init__(self, manager: Manager, renderer: Renderer):
        """
        Ensure context is passed properly to avoid data conflicts.

        Args:
        manager (Manager): The game's current manager.
        renderer (Renderer): The game's current renderer.
        """
        self.title = "Unnamed!"
        self.manager = manager
        self.renderer = renderer

    def start(self):
        raise NotImplementedError(f"Chapter '{self.title}' does not implement start()!")