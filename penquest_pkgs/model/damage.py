from dataclasses import dataclass

from penquest_pkgs.constants import VALID_ATTACK_MASKS, ATTACK_MASK_MODES

@dataclass
class DamageModel():

    MAX = 3
    MIN = -3

    @staticmethod
    def create(point:int, mask:str):
        dmg_points = []
        for c in ATTACK_MASK_MODES:
            if c in mask:
                dmg_points.append(point)
            else:
                dmg_points.append(0)
        return DamageModel(*dmg_points)

    def __init__(self, C:int=0, I:int=0, A:int=0):
        self.C = max(min(C, DamageModel.MAX), DamageModel.MIN)
        self.I = max(min(I, DamageModel.MAX), DamageModel.MIN)
        self.A = max(min(A, DamageModel.MAX), DamageModel.MIN)
        self.n = 0

    def __add__(self, other):
        if not isinstance(other, DamageModel):
            raise TypeError(
                f"Summation of types DamageModel and {type(other)} is not supported"
            )
        C = self.C + other.C
        I = self.I + other.I
        A = self.A + other.A
        return DamageModel(C, I, A)

    def __sub__(self, other):
        if not isinstance(other, DamageModel):
            raise TypeError(
                f"Subtraction of types DamageModel and {type(other)} is not "
                "supported"
            )
        C = self.C - other.C
        I = self.I - other.I
        A = self.A - other.A
        return DamageModel(C, I, A)

    def __mul__(self, factor):
        C = self.C * factor
        I = self.I * factor
        A = self.A * factor
        return DamageModel(C, I, A)

    def __gt__(self, other):
        """Determines whether the self instance is greate than the other
        instance. A DamageModel instannce is greater than another one if it is
        greate on all 3 damage scales

        Args:
            other (DamageModel): second instance of DamageModel, the self instance is
                compared to

        Raises:
            TypeError: other instance is not of type DamageModel

        Returns:
            bool: returns whether self is greater than other
        """
        if not isinstance(other, DamageModel):
            raise TypeError(
                f"{other} needs to be of type DamageModel for comparison"
            )
        return self.C > other.C and self.I > other.I and self.A > other.A

    def __ge__(self, other):
        """Determines whether the self instance is greate equal than the other
        instance. A DamageModel instannce is greater equal than another one if it is
        greater equal on all 3 damage scales

        Args:
            other (DamageModel): second instance of DamageModel, the self instance is
                compared to

        Raises:
            TypeError: other instance is not of type DamageModel

        Returns:
            bool: returns whether self is greater than other
        """
        if not isinstance(other, DamageModel):
            raise TypeError(
                f"{other} needs to be of type DamageModel for comparison"
            )
        return self.C >= other.C and self.I >= other.I and self.A >= other.A

    def __lt__(self, other):
        """Determines whether the self instance is less than the other
        instance. A DamageModel instannce is less than another one if it is
        less on all 3 damage scales

        Args:
            other (DamageModel): second instance of DamageModel, the self instance is
                compared to

        Raises:
            TypeError: other instance is not of type DamageModel

        Returns:
            bool: returns whether self is less than other
        """
        if not isinstance(other, DamageModel):
            raise TypeError(
                f"{other} needs to be of type DamageModel for comparison"
            )
        return self.C < other.C and self.I < other.I and self.A < other.A

    def __le__(self, other):
        """Determines whether the self instance is less equal than the other
        instance. A DamageModel instannce is less equal than another one if it is
        less equal on all 3 damage scales

        Args:
            other (DamageModel): second instance of DamageModel, the self instance is
                compared to

        Raises:
            TypeError: other instance is not of type DamageModel

        Returns:
            bool: returns whether self is less equal than other
        """
        if not isinstance(other, DamageModel):
            raise TypeError(
                f"{other} needs to be of type DamageModel for comparison"
            )
        return self.C <= other.C and self.I <= other.I and self.A <= other.A

    def __eq__(self, other):
        if not isinstance(other, DamageModel):
            return False
        if self.C != other.C:
            return False
        if self.I != other.I:
            return False
        if self.A != other.A:
            return False
        return True

    def __repr__(self):
        return "({}, {}, {})".format(self.C, self.I, self.A)

    def __iter__(self):
        self.n = 0
        return self

    def __next__(self):
        """ Returns the damage of the next damage type, in the order CIA """
        to_return = None
        if self.n == 0:
            to_return = self.C
        elif self.n == 1:
            to_return = self.I
        elif self.n == 2:
            to_return = self.A
        if to_return is None:
            raise StopIteration
        self.n += 1
        return to_return

    def __getitem__(self, index):
        """ Returns damage of a certain damage type, in the order CIA """
        if index == 0 or index == -3:
            return self.C
        if index == 1 or index == -2:
            return self.I
        if index == 2 or index == -1:
            return self.A
        raise IndexError("Unkown Index {}".format(index))

    def __setitem__(self, index, value):
        """ Sets damage of a certain damage type, in the order CIA """
        if index == 0 or index == -3:
            self.C = max(min(value, DamageModel.MAX), DamageModel.MIN)
        elif index == 1 or index == -2:
            self.I = max(min(value, DamageModel.MAX), DamageModel.MIN)
        elif index == 2 or index == -1:
            self.A = max(min(value, DamageModel.MAX), DamageModel.MIN)
        else:
            raise IndexError("Unkown Index {}".format(index))

    def __len__(self):
        return 3

    def index(self, value):
        """ Returns the index of the first appearance of value """
        if self.C == value:
            return 0
        if self.I == value:
            return 1
        if self.A == value:
            return 2
        raise ValueError("Value {} not found".format(value))

    def apply_mask(self, attack_mask:str=ATTACK_MASK_MODES):
        """ Filteres the current damage, such that damage types that are
            not included in the attack_mask are set to 0       
        """
        if attack_mask not in VALID_ATTACK_MASKS:
            raise ValueError("Attack mask {} not supported".format(attack_mask))

        filtered_values = []
        for mode in ATTACK_MASK_MODES:
            if mode in attack_mask:
                value = getattr(self, mode)
                filtered_values.append(value)
            else:
                filtered_values.append(0)

        return DamageModel(*filtered_values)

    def does_damage(self) -> bool:
        """Indicates whether the damage model has any positive values"""
        return self.C > 0 or self.I > 0 or self.A > 0

    def heals_damage(self) -> bool:
        """Indicates whether the damage model has any negative values"""
        return self.C < 0 or self.I < 0 or self.A < 0

    def is_neutral(self) -> bool:
        """Indicates whether the damage model has only 0 values"""
        return self.C == 0 and self.I == 0 and self.A == 0
