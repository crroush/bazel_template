import unittest

from tools.coverage.check import SOURCES, check_report


def report(hits=1):
    return "\n".join(
        f"SF:{source}\nDA:1,{hits}\nend_of_record" for source in SOURCES
    )


class CoverageCheckTest(unittest.TestCase):
    def test_complete_report(self):
        self.assertIn("100.0%", check_report(report())[-1])

    def test_missing_or_empty_language_fails(self):
        for text in ("", report().replace("DA:1,1", "LF:0"),
                     report().replace(SOURCES[0], "unrelated.cc")):
            with self.subTest(text=text), self.assertRaises(ValueError):
                check_report(text)

    def test_unexecuted_language_fails(self):
        with self.assertRaises(ValueError):
            check_report(report(0))

    def test_threshold_fails(self):
        with self.assertRaises(ValueError):
            check_report(report().replace("DA:1,1", "DA:1,1\nDA:2,0"))

    def test_duplicate_records_do_not_inflate_coverage(self):
        self.assertEqual(check_report(report()), check_report(report() + "\n" + report()))


if __name__ == "__main__":
    unittest.main()
