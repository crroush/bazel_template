import unittest

from examples.python.greeting import greet, greet_many


class GreetingTest(unittest.TestCase):
    def test_default(self):
        self.assertEqual(greet(), "Hello, world from C++!")

    def test_unicode_round_trip(self):
        self.assertEqual(greet("世界"), "Hello, 世界 from C++!")

    def test_requires_string(self):
        with self.assertRaises(TypeError):
            greet(123)

    def test_greet_many_preserves_shape_and_unicode(self):
        result = greet_many([["Bazel", "世界"], ["x86", "ARM64"]])
        self.assertEqual(result.shape, (2, 2))
        self.assertEqual(
            result.tolist(),
            [
                ["Hello, Bazel from C++!", "Hello, 世界 from C++!"],
                ["Hello, x86 from C++!", "Hello, ARM64 from C++!"],
            ],
        )

    def test_greet_many_empty_input(self):
        self.assertEqual(greet_many([[]]).shape, (1, 0))


if __name__ == "__main__":
    unittest.main()
