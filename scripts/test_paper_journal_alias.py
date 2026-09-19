import unittest
from paper_policy import TOP, norm

class JournalIdentityTest(unittest.TestCase):
    def test_publisher_full_name_maps_to_existing_series_b(self):
        self.assertEqual(norm('Journal of the Royal Statistical Society Series B: Statistical Methodology'), norm('Journal of the Royal Statistical Society, Series B'))
        self.assertIn(norm('Journal of the Royal Statistical Society Series B: Statistical Methodology'), TOP)

    def test_other_series_not_promoted(self):
        self.assertNotIn(norm('Journal of the Royal Statistical Society Series A: Statistics in Society'), TOP)
