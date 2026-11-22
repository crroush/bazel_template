import unittest

from examples.pyo3.greeting import greet


class GreetingTest(unittest.TestCase):
    def test_greeting(self):
        self.assertEqual(greet("world"), "Hello, world from Rust!")

    def test_unicode(self):
        self.assertEqual(greet("世界"), "Hello, 世界 from Rust!")

    def test_invalid_type(self):
        with self.assertRaises(TypeError):
            greet(42)


if __name__ == "__main__":
    unittest.main()
