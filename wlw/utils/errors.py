"""
Various errors for WLW.
"""

class SectionNotFoundError(Exception):
    """
    The required section could not be found.
    """
    pass

class CharacterNotFoundError(Exception):
    """
    The requested character was not found.
    """
    pass
