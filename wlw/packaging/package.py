"""
Packaging utlities.
"""
from wlw.utils.xor import obfuscate
import os
import importlib.util
import sys
import inspect
import logging
from wlw.utils.chapter import Chapter
from wlw.utils.logger import WLWLogger

logging.setLoggerClass(WLWLogger)
log = logging.getLogger("WLWLogger")
log: WLWLogger


PKG_DELIMETER = b"\x03" * 16 # 16 bytes of 0x03, used to delimit chapters
PKG_SPACER = b"\x03" * 2 # 2 bytes of 0x03, used to separate metadata from chapter content

def package_chapters(obfuscation_key: str, chapters_dir: str):
    """
    Package all chapter files (excluding special files) into a single file.

    Can then be reloaded using `load_package`.

    Args:
        obfuscation_key (str): The key used to obfuscate the package.
        chapters_dir (str): The directory containing the chapters to package.

    Format:
        `filepath<ZERO>filename<PKG_SPACER>content<PKG_DELIMETER>`
    """
    with open("chp.pkg.wlw", "wb") as f:
        for root, dirs, files in os.walk(chapters_dir):
            files = [_ for _ in files if _ not in ["__pycache__", "__init__.py"]] # filter out special files
            for file in files:
                if file.endswith(".py"):
                    mock_file_path = f"wlw.game.pkg.{os.path.basename(file)}" # mock file path to be used when the module is loaded
                    file_path = os.path.abspath(os.path.join(root, file)).replace("/", "\\")
                    print(f"'{file_path}'...")
                    with open(file_path, "rb") as f2:
                        # metadata
                        f.write(f"{mock_file_path}\0{file.split('.')[0]}".encode('utf-8'))
                        f.write(PKG_SPACER)
                        # script data
                        f.write(obfuscate(obfuscation_key.encode(), f2.read()))
                        f.write(PKG_DELIMETER) if file != files[-1] else None

def load_package(obfuscation_key: str, package_path: str) -> list:
    """
    Load a chapter package file and return a list of chapter modules that pass
    all validation checks.

    Nearly identical to `wlw.game`'s `__init__.py` file, but allows for
    drag-and-drop loading.

    Note that invalid chapters are still imported despite not being returned.
    Additionally, this function should only be used in production, as
    the chapters will be imported twice (or more times) otherwise.
    
    Args:
        obfuscation_key (str): The key used to deobfuscate the package.
        package_path (str): The path to the package file.
    
    Returns:
        list: A list of chapter modules that pass all validation
        checks.

    Raises:
        FileNotFoundError: If the package file does not exist.
    """
    chapter_modules = []

    log.debug(f"Loading packaged chapters from {package_path}...")
    
    if not os.path.exists(package_path):
        raise FileNotFoundError(f"Package file '{package_path}' does not exist. Please ensure your installation is valid.")


    with open(package_path, "rb") as f:
        for i, chunk in enumerate(f.read().split(PKG_DELIMETER)):
            meta, script = chunk.split(PKG_SPACER, maxsplit=1) # split metadata away from the actual script
            script_path, script_name = meta.split(b'\0')
            
            content = obfuscate(obfuscation_key.encode(), script).decode('utf-8')

            script_name = script_name.decode("utf-8")
            script_path = script_path.decode("utf-8")

            # mainly used for the following lines, doesn't actually import the module
            spec = importlib.util.spec_from_loader(script_name, loader=None)
            module = importlib.util.module_from_spec(spec)

            module.__file__ = script_path
            module.__name__ = script_name
            module.__path__ = [os.path.dirname(script_path)]
            module.__package__ = script_name
            module.__loader__ = None

            try:
                module_name = f"wlw.game.{script_name}"

                # compile the script and execute it. acts as a manual import.
                code = compile(content, script_path, 'exec')
                exec(code, module.__dict__)
                sys.modules[script_name] = module

                # preform checks against the module to ensure it can actually be run
                if hasattr(module, 'Main') and inspect.isclass(module.Main) and issubclass(module.Main, Chapter):
                    if hasattr(module, 'CHAPTER_NUMBER') and hasattr(module, 'CHAPTER_TITLE'):
                        chapter_modules.append(module)
                        log.debug(f"Successfully loaded chapter {module_name}")
                    else:
                        log.warning(f"{module_name} does not define CHAPTER_NUMBER and CHAPTER_TITLE, skipping.")
                        continue
                else:
                    log.warning(f"{module_name} does not define a valid Main class inheriting from Chapter, skipping.")
                    continue
            except Exception as e:
                log.warning(f"Error importing {module_name}: {e}")
                continue
    
    return chapter_modules