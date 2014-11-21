"""Pure-Python Jewish calendar implementation.

Copyright 2014, Eitan Mosenkis, all rights reserved.
Released under the MIT license which can be found at
http://opensource.org/licenses/MIT.

Based on jewish.c from the PHP stndard library, which includes the following
statement:

Copyright 1993-1995, Scott E. Lee, all rights reserved.
Permission granted to use, copy, modify, distribute and sell so long as
the above copyright and this permission statement are retained in all
copies. THERE IS NO WARRANTY - USE AT YOUR OWN RISK.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import datetime

HALAKIM_PER_HOUR = 1080
HALAKIM_PER_DAY = 25920
HALAKIM_PER_LUNAR_CYCLE = 29 * HALAKIM_PER_DAY + 13753
HALAKIM_PER_METONIC_CYCLE = HALAKIM_PER_LUNAR_CYCLE * (12 * 19 + 7)

_GREGORIAN_SDN_OFFSET  = 1721425
_JEWISH_SDN_OFFSET = 347997
_NEW_MOON_OF_CREATION = 31524

_SUNDAY = 0
_MONDAY = 1
_TUESDAY = 2
_WEDNESDAY = 3
_FRIDAY = 5

_NOON = 18 * HALAKIM_PER_HOUR
_AM3_11_20 = 9 * HALAKIM_PER_HOUR + 204
_AM9_32_43 = 15 * HALAKIM_PER_HOUR + 589

LEAP_YEARS = set((2, 5, 7, 10, 13, 16, 18))
_YEAR_OFFSET = (0, 12, 24, 37, 49, 61, 74, 86, 99, 111, 123, 136, 148, 160,
                173, 185, 197, 210, 222)

class JewishDateError(Exception):
    """Parent for all exceptions defined in jewish.date."""

class InvalidDateError(JewishDateError):
    """Error arising from attempting to calculate based on an invalid date."""

def months_in_metonic_year(year):
    return 13 if year in LEAP_YEARS else 12

def metonic_year(year):
    return (year - 1) % 19

def is_leap_year(year):
    return metonic_year(year) in LEAP_YEARS

class _Molad(object):

    def __init__(self, day=0, halakim=0):
        self.day = day
        self.halakim = halakim
        self._fix()

    def _fix(self):
        """Adjusts day and halakim so halakim < HALAKIM_PER_DAY."""
        self.day += self.halakim // HALAKIM_PER_DAY
        self.halakim %= HALAKIM_PER_DAY

    def _add_halakim(self, halakim):
        self.halakim += halakim
        self._fix()
        return self

    def add_lunar_cycles(self, lunarCycles):
        self._add_halakim(HALAKIM_PER_LUNAR_CYCLE * lunarCycles)
        return self

    def add_metonic_cycles(self, metonicCycles):
        self._add_halakim(HALAKIM_PER_METONIC_CYCLE * metonicCycles)
        return self

    def day_of_week(self):
        return self.day % 7

    def __repr__(self):
        return '_Molad(day=%s, halakim=%s)' % (self.day, self.halakim)


class JewishDate(object):
    """A date in the Jewish calendar."""

    TISHREI = 1
    CHESHVAN = 2
    KISLEV = 3
    TEVET = 4
    SHEVAT = 5
    ADAR_I = 6
    ADAR_II = 7
    NISAN = 8
    IYAR = 9
    SIVAN = 10
    TAMUZ = 11
    AV = 12
    ELUL = 13

    def __init__(self, year, month, day):
        """Create a JewishDate.

        Args:
            year: the year (must be >= 1)
            month: the month (must be in the range 1-13 inclusive, with 6
                   always representing Adar I and 7 representing Adar in
                   non-leap years and Adar II in leap years)
            day: the day (must be in the range 1-30 inclusive)

        Raises:
            InvalidDateError if year, month, or day is outside of the bounds
            described above. Note that it is still possible to create
            JewishDate objects that represent invalid dates, such as the 30th
            of a month with 29 days or a leap month in a non-leap year.
        """
        self.year = year
        self.month = month
        self.day = day
        self.isLeapYear = is_leap_year(year)
        if year <= 0 or month < 1 or month > 13 or day < 1 or day > 30:
            raise self._invalid_date_error()

    @classmethod
    def from_sdn(cls, sdn):
        """Create a JewishDate from a serial day number (SDN).

        Args:
            sdn: a serial day number

        Returns:
            A JewishDate

        Raises:
            InvalidDateError: if the input SDN is before the beginning of
                              Jewish year 1
        """
        if sdn <= _JEWISH_SDN_OFFSET:
            raise InvalidDateError(
                'Serial day number %s is before the first Jewish year' % sdn)
        inputDay = sdn - _JEWISH_SDN_OFFSET

        def get_result():
            return cls(year, month, day)

        metonicCycle, metonicYear, molad = _find_nearby_tishrei_molad(inputDay)
        tishrei1 = _get_first_day_of_year(metonicYear, molad)

        if inputDay >= tishrei1:
            # It found Tishrei 1 at the start of the year
            year = metonicCycle * 19 + metonicYear + 1
            if inputDay < tishrei1 + 59:
                if inputDay < tishrei1 + 30:
                    month = cls.TISHREI
                    day = inputDay - tishrei1 + 1
                else:
                    month = cls.CHESHVAN
                    day = inputDay - tishrei1 - 29
                return get_result()
            else:
                # Date is in Kislev
                molad.add_lunar_cycles(months_in_metonic_year(metonicYear))
                nextTishrei1 = _get_first_day_of_year((metonicYear + 1) % 19,
                                                      molad)
        else:
            # It found Tishrei 1 at the end of the year
            nextTishrei1 = tishrei1
            year = metonicCycle * 19 + metonicYear
            if inputDay >= nextTishrei1 - 177:
                # It is one of the last 6 months of the year
                for month, offset in (
                        (cls.ELUL, 30),
                        (cls.AV, 60),
                        (cls.TAMUZ, 89),
                        (cls.SIVAN, 119),
                        (cls.IYAR, 148),
                        (cls.NISAN, 178)):
                    if inputDay > nextTishrei1 - offset:
                        day = inputDay - nextTishrei1 + offset
                        break
                return get_result()
            else:
                day = inputDay - nextTishrei1 + 207
                if day > 0:
                    month = cls.ADAR_II
                    return get_result()
                if is_leap_year(year):
                    day += 30
                    if day > 0:
                        month = cls.ADAR_I
                        return get_result()
                day += 30
                if day > 0:
                    month = cls.SHEVAT
                    return get_result()
                day += 29
                if day > 0:
                    month = cls.TEVET
                    return get_result()

                # We need the length of the year to figure this out, so find
                # Tishrei 1 of this year.
                metonicCycle, metonicYear, molad = _find_nearby_tishrei_molad(
                    molad.day - 365)
                tishrei1 = _get_first_day_of_year(metonicYear, molad)

        yearLength = nextTishrei1 - tishrei1
        day = inputDay - tishrei1 - 29
        cheshvanLength = 30 if yearLength in (355, 385) else 29
        if day <= cheshvanLength:
            month = cls.CHESHVAN
            return get_result()
        else:
            day -= cheshvanLength
        # There's only one option left
        month = cls.KISLEV
        return get_result()

    @classmethod
    def from_date(cls, date):
        return cls.from_sdn(date.toordinal() + _GREGORIAN_SDN_OFFSET)

    def to_sdn(self):
        """Convert a JewishDate to serial day number (SDN).

        The return value will be > 0 for all valid dates, but there are some
        invalid dates that will return a positive value. To verify that a date
        is valid, convert it to SDN and then back and compare with the
        original.

        Returns:
            a serial day number (integer)

        Raises:
            InvalidDateError: if this JewishDate is invalid
        """
        year = self.year
        month = self.month
        day = self.day
        if year <= 0 or day <= 0 or day > 30:
            raise self._invalid_date_error()
        metonicCycle, metonicYear, molad, tishrei1 = _find_start_of_year(year)
        molad.add_lunar_cycles(months_in_metonic_year(metonicYear))
        nextTishrei1= _get_first_day_of_year((metonicYear + 1) % 19, molad)
        yearLength = nextTishrei1 - tishrei1
        adarsLength = 59 if self.isLeapYear else 29
        offset = {
            self.TISHREI: -1,
            self.CHESHVAN: 29,
            # Kislev is variable
            self.TEVET: adarsLength + 237,
            self.SHEVAT: adarsLength + 208,
            self.ADAR_I: adarsLength + 178,
            self.ADAR_II: 207,
            self.NISAN: 178,
            self.IYAR: 148,
            self.SIVAN: 119,
            self.TAMUZ: 89,
            self.AV: 60,
            self.ELUL: 30,
        }

        if month in (self.TISHREI, self.CHESHVAN):
            sdn = tishrei1 + day + offset[month]
        elif month == self.KISLEV:
            if yearLength in (355, 385):
                sdn = tishrei1 + day + 59
            else:
                sdn = tishrei1 + day + 58
        else:
            try:
                sdn = nextTishrei1 + day - offset[month]
            except KeyError:
                raise self._invalid_date_error()
        return sdn + _JEWISH_SDN_OFFSET

    def to_date(self):
        return datetime.date.fromordinal(self.to_sdn() - _GREGORIAN_SDN_OFFSET)

    def english_month_name(self):
        names = ('Tishrei', 'Cheshvan', 'Kislev', 'Tevet', 'Shevat', 'Adar I',
                 'Adar II', 'Nisan', 'Iyar', 'Sivan', 'Tamuz', 'Av', 'Elul')
        if self.month == self.ADAR_II and not self.isLeapYear:
            return 'Adar II'
        else:
            return names[self.month - 1]

    def _invalid_date_error(self):
        return InvalidDateError('%r represents an invalid date' % self)

    def __str__(self):
        return '%s %s %s' % (self.day, self.english_month_name(), self.year)

    def __repr__(self):
        return '%s(%s, %s, %s)' % (type(self).__name__,
                                   self.year, self.month, self.day)


def _get_first_day_of_year(metonicCycleYear, molad):
    """Calculate which day a year starts on.

    Args:
        cycleYear: year of 19-year cycle (0-18)
        molad: a _Molad object

    Returns:
        the serial day number of the first day of the year

    Given the year within the 19 year metonic cycle and the time of a molad
    (new moon) which starts that year, this routine will calculate what day
    will be the actual start of the year (Tishrei 1 or Rosh Ha-Shanah). This
    first day of the year will be the day of the molad unless one of 4 rules
    (called dehiyyot) delays it. These 4 rules can delay the start of the year
    by as much as 2 days.
    """
    tishrei1 = molad.day
    dow = molad.day_of_week()
    lastWasLeapYear = ((metonicCycleYear - 1) % 19) in LEAP_YEARS

    # Apply rules 2, 3, and 4
    if (molad.halakim >= _NOON
            or (metonicCycleYear not in LEAP_YEARS
                    and dow == _TUESDAY
                    and molad.halakim >= _AM3_11_20)
            or (lastWasLeapYear
                    and dow == _MONDAY
                    and molad.halakim >= _AM9_32_43)):
        tishrei1 += 1
        dow = (dow + 1) % 7

    # Apply rule 1 after the others because it can cause an additional delay of
    # one day.
    if dow in (_WEDNESDAY, _FRIDAY, _SUNDAY):
        tishrei1 += 1

    return tishrei1

def _molad_of_metonic_cycle(metonicCycle):
    """Calculate the date and time of the molad that starts a metonic cycle.

    Args:
        metonicCycle: the number of the metonic cycle

    Returns:
        a _Molad object representing the molad

    Since the length of a metonic cycle is a constant, this is a simple
    calculation, except that it requires an intermediate value which is bigger
    than 32 bits. Since Python automatically uses unlimited precision integers
    when necessary, this is does not pose a challenge, unlike in C.
    """
    return _Molad(halakim=_NEW_MOON_OF_CREATION).add_metonic_cycles(
        metonicCycle)

def _find_nearby_tishrei_molad(inputDay):
    """Find the closes molad of Tishrei to a given day number.

    Args:
        inputDay: a serial day number

    Returns:
        a tuple (metonicCycle, metonicYear, molad)

    It's not really the *closest* molad that we want here. If the input day is
    in the first two months, we want the molad at the start of the year. If the
    input day is in the fourth to last months, we want the molad at the end of
    the year. If the input day is in the third month, it doesn't matter which
    molad is returned, because both will be required. This type of "rounding"
    allows us to avoid calculating the length of the year in most cases.
    """
    # Estimate the metonic cycle number. Note that this may be an under
    # estimate because there are 6939.6896 days in a metonic cycle not 6940,
    # but it will never be an over estimate. The loop below will correct for
    # any error in this estimate.
    metonicCycle = (inputDay + 310) // 6940

    # Calculate the time of the starting molad for this metonic cycle.
    molad = _molad_of_metonic_cycle(metonicCycle)

    # If the above was an under estimate, increment the cycle number until the
    # correct one is found. For modern dates this loop is about 98.6% likely to
    # not execute, even once, because the above estimate is really quite close.
    while molad.day < inputDay - 6940 + 310:
        metonicCycle += 1
        molad.add_metonic_cycles(1)

    # Find the molad of Tishrei closest to this date.
    metonicYear = 0
    while metonicYear < 18:  # Not quite the same as a for loop over range(18)
        if molad.day > inputDay - 74:
            break
        molad.add_lunar_cycles(months_in_metonic_year(metonicYear))
        metonicYear += 1

    return metonicCycle, metonicYear, molad

def _find_start_of_year(year):
    """Find the serial day number of the the first day of a Jewish year.

    Args:
        year: the number of a Jewish calendar year

    Returns:
        the tuple (metonicCycle, metonicYear, molad, tishrei1)
    """
    metonicCycle, metonicYear = divmod(year - 1, 19)
    molad = _molad_of_metonic_cycle(metonicCycle)

    molad.add_lunar_cycles(_YEAR_OFFSET[metonicYear])
    tishrei1 = _get_first_day_of_year(metonicYear, molad)
    return (metonicCycle, metonicYear, molad, tishrei1)
