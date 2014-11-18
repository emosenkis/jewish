from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

HALAKIM_PER_HOUR = 1080
HALAKIM_PER_DAY = 25920
HALAKIM_PER_LUNAR_CYCLE = 29 * HALAKIM_PER_DAY + 13753
HALAKIM_PER_METONIC_CYCLE = HALAKIM_PER_LUNAR_CYCLE * (12 * 19 + 7)

JEWISH_SDN_OFFSET = 347997
JEWISH_SDN_MAX = 324542846
NEW_MOON_OF_CREATION = 31524

SUNDAY = 0
MONDAY = 1
TUESDAY = 2
WEDNESDAY = 3
THURSDAY = 4
FRIDAY = 5
SATURDAY = 6

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

NOON = 18 * HALAKIM_PER_HOUR
AM3_11_20 = 9 * HALAKIM_PER_HOUR + 204
AM9_32_43 = 15 * HALAKIM_PER_HOUR + 589

LEAP_YEARS = set((2, 5, 7, 10, 13, 16, 18))
YEAR_OFFSET = (0, 12, 24, 37, 49, 61, 74, 86, 99, 111, 123, 136, 148, 160, 173,
               185, 197, 210, 222)

def monthsInMetonicYear(year):
  return 13 if year in LEAP_YEARS else 12

def MetonicYear(year):
  return (year - 1) % 19

def IsLeapYear(year):
  return MetonicYear(year) in LEAP_YEARS

class Molad(object):

  def __init__(self, day=0, halakim=0):
    self.day = day
    self.halakim = halakim
    self._fix()

  def _fix(self):
    """Adjusts day and halakim so halakim < HALAKIM_PER_DAY."""
    self.day += self.halakim // HALAKIM_PER_DAY
    self.halakim %= HALAKIM_PER_DAY

  def _addHalakim(self, halakim):
    self.halakim += halakim
    self._fix()
    return self

  def addLunarCycles(self, lunarCycles):
    self._addHalakim(HALAKIM_PER_LUNAR_CYCLE * lunarCycles)
    return self

  def addMetonicCycles(self, metonicCycles):
    self._addHalakim(HALAKIM_PER_METONIC_CYCLE * metonicCycles)
    return self

  def dayOfWeek(self):
    return self.day % 7

  def __repr__(self):
    return 'Molad(day=%s, halakim=%s)' % (self.day, self.halakim)


class JewishDate(object):

  def __init__(self, year, month, day):
    self.year = year
    self.month = month
    self.day = day
    self.isLeapYear = IsLeapYear(year)

  def englishMonthName(self):
    names = ('Tishrei', 'Cheshvan', 'Kislev', 'Tevet', 'Shevat', 'Adar I',
             'Adar II', 'Nisan', 'Iyar', 'Sivan', 'Tamuz', 'Av', 'Elul')
    if self.month == ADAR_II and not self.isLeapYear:
      return 'Adar II'
    else:
      return names[self.month - 1]

  def __str__(self):
    return '%s %s %s' % (self.day, self.englishMonthName(), self.year)

  def __repr__(self):
    return '%s(%s, %s, %s)' % (type(self).__name__,
                               self.year, self.month, self.day)

def Tishrei1(metonicCycleYear, molad):
  """Calculate which day a year starts on.

  Args:
    cycleYear: year of 19-year cycle (0-18)
    molad: a Molad object
  
  Returns:
    the serial day number of the first day of the year

  Given the year within the 19 year metonic cycle and the time of a molad (new
  moon) which starts that year, this routine will calculate what day will be the
  actual start of the year (Tishrei 1 or Rosh Ha-Shanah).  This first day of the
  year will be the day of the molad unless one of 4 rules (called dehiyyot)
  delays it.  These 4 rules can delay the start of the year by as much as 2
  days.
  """
  tishrei1 = molad.day
  dow = molad.dayOfWeek()
  lastWasLeapYear = ((metonicCycleYear - 1) % 19) in LEAP_YEARS

  # Apply rules 2, 3, and 4
  if (molad.halakim >= NOON
      or (metonicCycleYear not in LEAP_YEARS
          and dow == TUESDAY
          and molad.halakim >= AM3_11_20)
      or (lastWasLeapYear
          and dow == MONDAY
          and molad.halakim >= AM9_32_43)):
    tishrei1 += 1
    dow = (dow + 1) % 7

  # Apply rule 1 after the others because it can cause an additional delay of
  # one day.
  if dow in (WEDNESDAY, FRIDAY, SUNDAY):
    tishrei1 += 1

  return tishrei1

def MoladOfMetonicCycle(metonicCycle):
  """Calculate the date and time of the molad that starts a metonic cycle.
  
  Args:
    metonicCycle: the number of the metonic cycle

  Returns:
    a Molad object representing the molad
  
  Since the length of a metonic cycle is a constant, this is a simple
  calculation, except that it requires an intermediate value which is bigger
  than 32 bits. Since Python automatically uses unlimited precision integers
  when necessary, this is does not pose a challenge, unlike in C.
  """
  return Molad(halakim=NEW_MOON_OF_CREATION).addMetonicCycles(metonicCycle)

def FindTishreiMolad(inputDay):
  """Find the closes molad of Tishrei to a given day number.

  Args:
    inputDay: a serial day number

  Returns:
    a tuple (metonicCycle, metonicYear, molad)
  
  It's not really the *closest* molad that we want here. If the input day is in
  the first two months, we want the molad at the start of the year.  If the
  input day is in the fourth to last months, we want the molad at the end of the
  year. If the input day is in the third month, it doesn't matter which molad is
  returned, because both will be required.  This type of "rounding" allows us to
  avoid calculating the length of the year in most cases.
  """
  # Estimate the metonic cycle number.  Note that this may be an under estimate
  # because there are 6939.6896 days in a metonic cycle not 6940, but it will
  # never be an over estimate.  The loop below will correct for any error in
  # this estimate.
  metonicCycle = (inputDay + 310) // 6940

  # Calculate the time of the starting molad for this metonic cycle.
  molad = MoladOfMetonicCycle(metonicCycle)

	# If the above was an under estimate, increment the cycle number until the
  # correct one is found.  For modern dates this loop is about 98.6% likely to
  # not execute, even once, because the above estimate is really quite close.
  while molad.day < inputDay - 6940 + 310:
    metonicCycle += 1
    molad.addMetonicCycles(1)

	# Find the molad of Tishrei closest to this date.
  metonicYear = 0
  while metonicYear < 18:  # Not quite the same as a for loop over range(18)
    if molad.day > inputDay - 74:
      break
    molad.addLunarCycles(monthsInMetonicYear(metonicYear))
    metonicYear += 1

  return metonicCycle, metonicYear, molad

def FindStartOfYear(year):
  """Find the serial day number of the the first day of a Jewish calendar year.
  
  Args:
    year: the number of a Jewish calendar year
  
  Returns:
    the tuple (metonicCycle, metonicYear, molad, tishrei1)
  """
  metonicCycle, metonicYear = divmod(year - 1, 19)
  molad = MoladOfMetonicCycle(metonicCycle)

  molad.addLunarCycles(YEAR_OFFSET[metonicYear])
  tishrei1 = Tishrei1(metonicYear, molad)
  return (metonicCycle, metonicYear, molad, tishrei1)

def SdnToJewish(sdn):
  """Get the Jewish year, month, and day of a serial day number (SDN).

  Args:
    sdn: a serial day number

  Returns:
    If the input day is before the first day of year 1, None. Otherwise,
    a JewishDate with year > 0; month in the range 1 to 13; day in the range 1
    to 30 inclusive.
  """
  # TODO(eitan): maybe raise an exception instead of returning None
  if sdn <= JEWISH_SDN_OFFSET:
    return None
  inputDay = sdn - JEWISH_SDN_OFFSET

  metonicCycle, metonicYear, molad = FindTishreiMolad(inputDay)
  tishrei1 = Tishrei1(metonicYear, molad)

  if inputDay >= tishrei1:
    # It found Tishrei 1 at the start of the year
    year = metonicCycle * 19 + metonicYear + 1
    if inputDay < tishrei1 + 59:
      if inputDay < tishrei1 + 30:
        month = TISHREI
        day = inputDay - tishrei1 + 1
      else:
        month = CHESHVAN
        day = inputDay - tishrei1 - 29
      return JewishDate(year, month, day)
    else:
      # Date is in Kislev
      molad.addLunarCycles(monthsInMetonicYear(metonicYear))
      nextTishrei1 = Tishrei1((metonicYear + 1) % 19, molad)
  else:
    # It found Tishrei 1 at the end of the year
    nextTishrei1 = tishrei1
    year = metonicCycle * 19 + metonicYear
    if inputDay >= nextTishrei1 - 177:
      # It is one of the last 6 months of the year
      for month, offset in (
          (13, 30), (12, 60), (11, 89), (10, 119), (9, 148), (8, 178)):
        if inputDay > nextTishrei1 - offset:
          day = inputDay - nextTishrei1 + offset
          break
      return JewishDate(year, month, day)
    else:
      day = inputDay - nextTishrei1 + 207
      if day > 0:
        month = ADAR_II
        return JewishDate(year, month, day)
      if IsLeapYear(year):
        day += 30
        if day > 0:
          month = ADAR_I
          return JewishDate(year, month, day)
      day += 30
      if day > 0:
        month = SHEVAT
        return JewishDate(year, month, day)
      day += 29
      if day > 0:
        month = TEVET
        return JewishDate(year, month, day)

      # We need the length of the year to figure this out, so find Tishrei 1 of
      # this year.
      metonicCycle, metonicYear, molad = FindTishreiMolad(molad.day - 365)
      tishrei1 = Tishrei1(metonicYear, molad)

  yearLength = nextTishrei1 - tishrei1
  day = inputDay - tishrei1 - 29
  cheshvanLength = 30 if yearLength in (355, 385) else 29
  if day <= cheshvanLength:
    month = CHESHVAN
    return JewishDate(year, month, day)
  else:
    day -= cheshvanLength
  # There's only one option left
  month = KISLEV
  return JewishDate(year, month, day)
