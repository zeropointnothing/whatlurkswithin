"""
Scripts for WLW, intended to be run from main.py.

Dynamically loads all chapter modules in the game package.

All chapters should inherit from wlw.utils.chapter.Chapter, be named Main, and implement the start method.
Additionally, they should define the constants CHAPTER_TITLE and CHAPTER_NUMBER.
"""
import importlib
import pkgutil
import inspect
import logging
from wlw.utils.chapter import Chapter
from wlw.utils.logger import WLWLogger

logging.setLoggerClass(WLWLogger)
log = logging.getLogger("WLWLogger")
log: WLWLogger

# Dynamically import all chapter modules
# When built, requires the Nuitka --include-package='wlw.game' flag to be set so that pkgutil can find chapters.
chapter_modules = []
for package in pkgutil.iter_modules([__path__][0]): # pkgutil will function when built with nuitka
    if package.name != "__init__.py":
        module_name = f"wlw.game.{package.name}"
        try:
            module = importlib.import_module(module_name)
            if hasattr(module, 'Main') and inspect.isclass(module.Main) and issubclass(module.Main, Chapter):
                if hasattr(module, 'CHAPTER_NUMBER') and hasattr(module, 'CHAPTER_TITLE'):
                    chapter_modules.append(module)
                    log.debug(f"Successfully loaded chapter {module_name}")
                else:
                    log.warning(f"{module_name} does not define CHAPTER_NUMBER and CHAPTER_TITLE, skipping.")
            else:
                log.warning(f"{module_name} does not define a valid Main class inheriting from Chapter, skipping.")
        except Exception as e:
            log.warning(f"Error importing {module_name}: {e}")

# Expose chapter classes
__all__ = [module.__name__.split('.')[-1] for module in chapter_modules]
__all__.append("chapter_modules")