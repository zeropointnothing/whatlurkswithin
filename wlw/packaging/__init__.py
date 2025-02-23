"""
Packaging utility.

Allows for the 'compilation' of chapters into a single file, which can then be run
indepedently of the main game executable.

Does not actually compile code, though does obfuscate it.
"""

from .package import load_package, package_chapters

__all__ = ["load_package", "package_chapters"]
