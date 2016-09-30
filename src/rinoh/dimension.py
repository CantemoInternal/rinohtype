# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.

"""
This module exports a single class:

* :class:`Dimension`: Late-evaluated dimension, forming the basis of the layout
  engine

It also exports a number of pre-defined units:

* :const:`PT`: PostScript point
* :const:`INCH`: Inch, equal to 72 PostScript points
* :const:`MM`: Millimeter
* :const:`CM`: Centimeter

"""

import re

from .attribute import AcceptNoneAttributeType


__all__ = ['Dimension', 'PT', 'PICA', 'INCH', 'MM', 'CM', 'PERCENT']


class DimensionType(type):
    """Maps comparison operators to their equivalents in :class:`float`"""

    def __new__(mcs, name, bases, cls_dict):
        """Return a new class with predefined comparison operators"""
        for method_name in ('__lt__', '__le__', '__gt__', '__ge__',
                            '__eq__', '__ne__'):
            cls_dict[method_name] = mcs._make_operator(method_name)
        return type.__new__(mcs, name, bases, cls_dict)

    @staticmethod
    def _make_operator(method_name):
        """Return an operator method that takes parameters of type
        :class:`Dimension`, evaluates them, and delegates to the :class:`float`
        operator with name `method_name`"""
        def operator(self, other):
            """Operator delegating to the :class:`float` method `method_name`"""
            float_operator = getattr(float, method_name)
            try:
                float_other = float(other)
            except TypeError:
                return False
            return float_operator(float(self), float_other)
        return operator


class DimensionBase(AcceptNoneAttributeType, metaclass=DimensionType):
    """Late-evaluated dimension. The result of mathematical operations on
    dimension objects is not a statically evaluated version, but rather stores
    references to the operator arguments. The result is only evaluated to a
    number on conversion to a :class:`float`.

    The internal representation is in terms of PostScript points. A PostScript
    point is equal to one 72th of an inch."""

    def __neg__(self):
        return DimensionMultiplication(self, -1)

    def __add__(self, other):
        """Return the sum of this dimension and `other`."""
        return DimensionAddition(self, other)

    __radd__ = __add__

    def __sub__(self, other):
        """Return the difference of this dimension and `other`."""
        return DimensionSubtraction(self, other)

    def __rsub__(self, other):
        """Return the difference of `other` and this dimension."""
        return DimensionSubtraction(other, self)

    def __mul__(self, factor):
        """Return the product of this dimension and `factor`."""
        return DimensionMultiplication(self, factor)

    __rmul__ = __mul__

    def __truediv__(self, divisor):
        """Return the quotient of this dimension and `divisor`."""
        return DimensionMultiplication(self, 1.0 / divisor)

    def __repr__(self):
        """Return a textual representation of the evaluated value."""
        return '{:.2f}pt'.format(float(self)).replace('.00', '')

    def __abs__(self):
        """Return the absolute value of this dimension (in points)."""
        return abs(float(self))

    def __float__(self):
        """Evaluate the value of this dimension in points."""
        raise NotImplementedError

    @classmethod
    def check_type(cls, value):
        return (super().check_type(value) or isinstance(value, Fraction)
                or value == 0)

    REGEX = re.compile(r"""(?P<value>
                             [+-]?         # optional sign
                             \d*\.?\d+     # integer or float value
                           )
                           \s*             # optional space between value & unit
                           (?P<unit>
                             [a-z%/0-9]*   # unit (can be an empty string)
                           )
                       """, re.IGNORECASE | re.VERBOSE)

    @classmethod
    def parse_string(cls, string):
        m = cls.REGEX.match(string)
        try:
            value, unit = m.groups()
            if unit == '':
                assert value == '0'
                return 0
            dimension_unit = DimensionUnitBase.all[unit.lower()]
            _, end = m.span()
            if string[end:].strip():
                raise ValueError("{}: trailing characters after dimension"
                                 .format(string))
            try:
                return int(value) * dimension_unit
            except ValueError:
                return float(value) * dimension_unit
        except (AttributeError, KeyError, AssertionError):
            raise ValueError("'{}' is not a valid dimension".format(string))

    def to_points(self, total_dimension):
        return float(self)


class Dimension(DimensionBase):
    # TODO: em, ex? (depends on context)
    def __init__(self, value=0, unit=None):
        """Initialize a dimension at `value` points."""
        self._value = value
        self._unit = unit or PT

    def __str__(self):
        number = '{:.2f}'.format(self._value).rstrip('0').rstrip('.')
        return '{}{}'.format(number, self._unit.label)

    def grow(self, value):
        self._value += float(value)
        return self

    def __float__(self):
        return float(self._value) * self._unit.points_per_unit


class DimensionAddition(DimensionBase):
    def __init__(self, *addends):
        self.addends = list(addends)

    def __float__(self):
        return sum(map(float, self.addends or (0.0, )))


class DimensionSubtraction(DimensionBase):
    def __init__(self, minuend, subtrahend):
        self.minuend = minuend
        self.subtrahend = subtrahend

    def __float__(self):
        return float(self.minuend) - float(self.subtrahend)


class DimensionMultiplication(DimensionBase):
    def __init__(self, multiplicand, multiplier):
        self.multiplicand = multiplicand
        self.multiplier = multiplier

    def __float__(self):
        return float(self.multiplicand) * self.multiplier


class DimensionMaximum(DimensionBase):
    def __init__(self, *dimensions):
        self.dimensions = dimensions

    def __float__(self):
        return max(*(float(dimension) for dimension in self.dimensions))


class DimensionUnitBase(object):
    all = {}

    def __init__(self, label):
        self.label = label
        self.all[label] = self


class DimensionUnit(DimensionUnitBase):
    def __init__(self, points_per_unit, label):
        super().__init__(label)
        self.points_per_unit = float(points_per_unit)

    def __rmul__(self, value):
        return Dimension(value, self)


# Units

PT = DimensionUnit(1, 'pt')
INCH = DimensionUnit(72*PT, 'in')
PICA = DimensionUnit(1 / 6 * INCH, 'pc')
MM = DimensionUnit(1 / 25.4 * INCH, 'mm')
CM = DimensionUnit(10*MM, 'cm')


class Fraction(DimensionUnitBase):
    def __init__(self, nominator, unit):
        self._nominator = nominator
        self._unit = unit

    def __str__(self):
       number = '{:.2f}'.format(self._nominator).rstrip('0').rstrip('.')
       return '{}{}'.format(number, self._unit.label)

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def to_points(self, total_dimension):
        fraction = self._nominator / self._unit.denominator
        return fraction * float(total_dimension)


class FractionUnit(DimensionUnitBase):
    def __init__(self, denominator, label):
        super().__init__(label)
        self.denominator = denominator

    def __rmul__(self, nominator):
        return Fraction(nominator, self)


PERCENT = FractionUnit(100, '%')
QUARTERS = FractionUnit(4, '/4')
