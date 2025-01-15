"""
Scripts for WLW, intended to be run from main.py.

Dynamically loads all chapter modules in the game package.

All chapters should inherit from wlw.utils.chapter.Chapter, be named Main, and implement the start method.
Additionally, they should define the constants CHAPTER_TITLE and CHAPTER_NUMBER.
"""
import os
import importlib
import inspect
import logging
from wlw.utils.chapter import Chapter
from wlw.utils.logger import WLWLogger

logging.setLoggerClass(WLWLogger)
log = logging.getLogger("WLWLogger")
log: WLWLogger

# Dynamically import all chapter modules
chapter_modules = []
for filename in os.listdir(os.path.dirname(__file__)):
    if filename.endswith(".py") and filename != "__init__.py":
        module_name = f"wlw.game.{filename[:-3]}"
        try:
            module = importlib.import_module(module_name)
            if hasattr(module, 'Main') and inspect.isclass(module.Main) and issubclass(module.Main, Chapter):
                if hasattr(module, 'CHAPTER_NUMBER') and hasattr(module, 'CHAPTER_TITLE'):
                    chapter_modules.append(module)
                    log.debug(f"Sucessfully loaded chapter {module_name}")
                else:
                    log.warning(f"{module_name} does not define CHAPTER_NUMBER and CHAPTER_TITLE, skipping.")
            else:
                log.warning(f"{module_name} does not define a valid Main class inheriting from Chapter, skipping.")
        except Exception as e:
            log.warning(f"Error importing {module_name}: {e}")

# Expose chapter classes
__all__ = [module.__name__.split('.')[-1] for module in chapter_modules]
__all__.append("chapter_modules")