from wlw.utils.character import Character

class Player(Character):
    """
    Player class.
    
    Inherits from Character class.
    """
    def __init__(self, name, sex):
        super().__init__(name, sex)
