from wlw.utils.character import Character
from wlw.utils.errors import InvalidTargetError
import random
import copy

class Buff:
    """
    Base class for all buffs.
    """
    def __init__(self, name, description, buff_length: int = 1, hot: int = 1):
        self.__buff_length = buff_length
        self.__hot = hot
        self.__name = name
        self.__description = description

    @property
    def buff_length(self):
        """
        How long the buff should last for.
        
        Returns:
        int: The buff's remaining length (in turns)
        """
        return self.__buff_length

    @buff_length.setter
    def buff_length(self, to: int):
        try:
            to = int(str(to)) # account for bools, since they're a subclass of int
        except ValueError as e:
            raise TypeError(f"buff_length must be an 'int', not '{to.__class__.__name__}'.") from e

        self.__buff_length = to

    @property
    def hot(self):
        """
        How 'hot' a Buff is.

        Hot Buffs should not decrement per turn.
        """
        return self.__hot

    @property
    def name(self):
        """
        The buff's name.

        Returns:
        str: Buff name.
        """
        return self.__name
    
    @property
    def description(self):
        """
        The buff's description.

        Returns:
        str: Buff description.
        """
        return self.__description

    def on_attack(self):
        """
        Should be called each time a character with this buff attacks.
        """
        raise NotImplementedError()
    
    def on_attacked(self, original_damage: int):
        """
        Should be called each time a character with this buff is attacked.

        Args:
        original_damage (int): The attack's original damage.

        Returns:
        int: The new damage delt to the character.
        """
        return original_damage * 1

    def on_turn(self):
        """
        Should be called each time a character uses a turn.

        Idealy, also decrements the `__buff_length` count.
        """
        if self.__hot <= 0:
            self.__buff_length -= 1
        else:
            self.__hot -= 1

class Attack:
    def __init__(self, name: str, description: str, damage: int = 0, target: str = "foe", buff: Buff = None):
        """
        Basic attack class.
        """

        if target.lower() not in ["ally", "foe", "a_ally", "a_foe", "all"]:
            raise ValueError(f"Target {target} is not valid. Expected 'ally/a_ally', 'foe/a_foe', or 'all'.")

        self.__name = name
        self.__description = description
        self.__target = target
        self.__damage = damage
        self.__buff = buff

    @property
    def name(self):
        return self.__name

    @property
    def description(self):
        return self.__description

    @property
    def target(self):
        return self.__target

    @property
    def damage(self):
        return self.__damage
    
    @property
    def buff(self):
        return self.__buff


class BattleCharacter(Character):
    """
    Special sub-class of Character which includes several battle-related functions and attributes.
    """
    def __init__(self, name, sex = "m", affinity = 0, hitpoints = 10, special = False, hidden = False):
        super().__init__(name, sex, affinity, special, hidden)

        try:
            hitpoints = int(str(hitpoints))
        except ValueError as e:
            raise TypeError(f"Hitpoints must be 'int', not '{hitpoints.__class__.__name__}'") from e
        
        self.__hitpoints = hitpoints
        self.__attacks = []
        self.__buffs: list[Buff] = []

    @property
    def attacks(self):
        return self.__attacks

    @property
    def buffs(self):
        return self.__buffs

    @property
    def hitpoints(self):
        """
        The amount of hitpoints, or 'health' of a character.

        Returns:
        int: The character's remaining hitpoints.
        """
        return self.__hitpoints

    @hitpoints.setter
    def hitpoints(self, to: int):
        try:
            self.__hitpoints = int(str(to))
        except ValueError as e:
            raise TypeError(f"Hitpoints must be 'int', not '{to.__class__.__name__}'") from e

    def damage(self, hitpoints: int):
        """
        Damage a character for `hitpoints`.

        Automatically triggers any buffs listening for `on_attacked`.
        """
        new = hitpoints
        if self.__buffs:
            for buff in self.__buffs:
                new = buff.on_attacked(hitpoints)

        self.hitpoints -= new

    def add_buff(self, buff: Buff):
        """
        Add a Buff to a character.

        Copies `buff`, then adds it the the character's buff list.
        """
        if not isinstance(buff, Buff):
            raise TypeError(f"Buff {buff} is not a valid Buff object.")
        
        self.__buffs.append(copy.deepcopy(buff))

    def set_attacks(self, attacks: list[Attack]):
        for atk in attacks:
            if not isinstance(atk, Attack):
                raise TypeError(f"Attack '{atk}' is not a valid Attack object!")

        self.__attacks = attacks

    def get_attack(self, attack_name: str):
        for attack in self.__attacks:
            if attack_name == attack.name:
                return attack
        
        raise ValueError(f"Character '{self._name}' has no such attack '{attack_name}'")


class Battle:
    def __init__(self, allies: list[BattleCharacter], foes: list[BattleCharacter]):
        for ally in allies:
            if not isinstance(ally, BattleCharacter):
                raise TypeError(f"Ally '{ally}' is not a BattleCharacter object!")
        for foe in foes:
            if not isinstance(foe, BattleCharacter):
                raise TypeError(f"Foe '{foe}' is not a BattleCharacter object!")

        self.__display = {"text": "", "length": 0}
        self.__allies = allies
        self.__foes = foes
        self.__turn = 0

    @property
    def allies(self):
        return self.__allies
    
    @property
    def foes(self):
        return self.__foes
    
    @property
    def turn(self):
        return self.__turn

    def set_display(self, text: str, length: int) -> None:
        """
        Set the current "display" message.
        
        Args:
        text (str): The display message.
        length (int): How long the message should be up for.
        """
        self.__display["text"] = text
        self.__display["length"] = length


    def get_display(self, decrement: float = 0.0) -> tuple[str, int]:
        """
        Get the current set "display" message for the battle.

        If `decrement` is set, will automatically decrement the timer.

        Automatically clears any expired messages.

        Args:
        decrement (float): Decrement internal timer.

        Returns:
        tuple[str, int]: The current display message.
        """

        if decrement and self.__display["length"] > 0:
            self.__display["length"] = self.__display["length"] - decrement
        else:
            self.set_display("", 0)

        return (self.__display["text"], self.__display["length"])

    def find_foe(self, foe_name: str):
        """
        Find the first foe with the name `foe_name`.

        Returns:
        BattleCharacter: The foe, if found.
        """
        for foe in self.__foes:
            if foe_name == foe.name:
                return foe
        
        raise ValueError(f"No such foe with name '{foe_name}'")

    def _on_same_team(self, a: BattleCharacter, b: BattleCharacter) -> bool:
        """
        Check if `a` is on the same team as `b`.

        Returns:
        bool: Whether both characters exist on the same team.
        """
        if (a in self.__allies and b in self.__allies) or (a in self.__foes and b in self.__foes):
            return True
        return False

    def next_turn(self):
        """
        Increment the internal turn counter.
        """
        battle_party = self.__allies+self.__foes

        self.__turn += 1
        self.__turn %= len(battle_party)

        self._trigger_turn(battle_party[self.__turn])

    def _trigger_turn(self, character: BattleCharacter):
        """
        Trigger `character`'s turn, calling all buff's `on_turn` method.
        """
        # print(f"TURN: {character.name}")

        for buff in character.buffs:
            buff.on_turn()
            if buff.buff_length <= 0:
                character.buffs.remove(buff)


    def attack(self, whom: BattleCharacter, by: BattleCharacter, using: Attack):
        """
        Attack `whom` with `by`, with `using`.

        Buff attacks must have a target, even if they are type a_ally/a_foe, however damage will only be dealt if that Attack
        has any.
        """
        # print(f"{by.name} -> {whom.name} ({using.name})")

        if using not in by.attacks:
            raise ValueError(f"Attack '{using.name}' does not belong to character '{by.name}'!")
        elif (using.target in ["a_foe", "foe"] and self._on_same_team(whom, by)) or (using.target in ["a_ally", "ally"] and not self._on_same_team(whom, by)):
            raise InvalidTargetError(f"Attack '{using.name}' ('{by.name}') cannot target '{whom.name}', only characters of type '{using.target}'")

        # targets all allies
        if using.target == "a_ally":
            for ally in self.__allies:
                ally.damage(using.damage)
                
                if using.buff:
                    ally.add_buff(using.buff)
        elif using.target == "a_foe":
            for foe in self.__foes:
                foe.damage(using.damage)

                if using.buff:
                    foe.add_buff(using.buff)
        elif using.target in ["ally", "foe"]:
            whom.damage(using.damage)

            if using.buff:
                whom.add_buff(using.buff)



def create_units(name: str, sex: str, hitpoints: int, attacks: list[Attack], i: int = 1) -> list[BattleCharacter]:
    """
    Create `i` BattleCharacter objects.

    Useful for creating many non-persistent enemies.
    """
    char = []
    for _ in range(i):
        b = BattleCharacter(name, sex, 0, hitpoints)
        b.set_attacks(attacks)

        char.append(b)

    return char

        



# BUFFS

class EvadeBuff(Buff):
    def __init__(self, buff_length = 1):
        super().__init__("Evade", "Enhanced knowledge of the battlefield allows this character to dodge attacks.", buff_length)

    def on_attacked(self, original_damage):
        # print(f"attacked! ({self.name}:{original_damage})")

        if random.randint(1, 3) == 1:
            # print("evade!")
            return 0
        else:
            return original_damage


class WeakenedBuff(Buff):
    def __init__(self, buff_length = 1):
        super().__init__("Weakened", "This character takes +2 extra damage... Ouch!", buff_length)

    def on_attacked(self, original_damage):
        # print(f"attacked! ({self.name}:{original_damage})")

        return original_damage + 2