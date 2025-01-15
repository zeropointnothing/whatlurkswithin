from wlw.utils.manager import Manager
from wlw.utils.renderer import Renderer
from wlw.utils.errors import ThreadError
import threading

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
        """
        Chapter entrypoint.

        Should be overridden by any child classes.
        """
        raise NotImplementedError(f"Chapter '{self.title}' does not implement start()!")
    
class ChapterThread(threading.Thread):
    """
    Custom thread that will raise any errors that occur to the main thread once
    'join()' is called.

    Should be used to ensure thread errors propagate to the main thread.
    """
    def run(self):
        self.exc = None
        try:
            if hasattr(self, '_Thread__target'):
                self.ret = self._Thread__target(*self._Thread__args, **self._Thread__kwargs)
            else:
                self.ret = self._target(*self._args, **self._kwargs)
        except BaseException as e:
            self.exc = e

    def join(self, timeout=None):
        super(ChapterThread, self).join(timeout)
        if self.exc:
            raise ThreadError("Chapter Thread crashed unexpectedly!") from self.exc
        return self.ret