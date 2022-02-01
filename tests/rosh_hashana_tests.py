import unittest
import datetime
import jewish
from random import randint

ADU_DAYS = [6, 2, 4]  # sunday, wednesday, friday


class TestLoAduRosh(unittest.TestCase):
    def setUp(self):
        today = datetime.date.today()
        self.jewish_today = jewish.JewishDate.from_date(today)

    def test_next_rosh_hashanah(self):
        next_rosh_hashanah = jewish.JewishDate(
            self.jewish_today.year + 1, 1, 1)
        self.assertNotIn(next_rosh_hashanah, ADU_DAYS)

    def test_random_years(self):  # 1000 +/- years from this year
        for i in range(100):
            year_offset = randint(-1000, 1000)
            rosh_hashanah = jewish.JewishDate(
                self.jewish_today.year + year_offset, 1, 1)
            self.assertNotIn(rosh_hashanah, ADU_DAYS)


if __name__ == '__main__':
    unittest.main()
