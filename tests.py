import sys
import unittest
from dataset import BoundingBox, Point

start = Point(17, 17)
end = Point(42, 42)
width = abs(end.x - start.x)
height = abs(end.y - start.y)


def parse_arguments():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", help="Verbose.", required=False, default=False, action="store_true")
    args = parser.parse_args()
    return args


class BoundingBoxTests(unittest.TestCase):
    def compare_points(self, first: Point, second: Point):
        self.assertEqual(first, second, str(first) + " is not equal to " + str(second))

    def test_start_and_end(self):
        b = BoundingBox(start=start, end=end)
        self.compare_points(b.start, start)
        self.compare_points(b.end, end)

    def test_start_and_ends(self):
        b = BoundingBox(start=start, end_x=end.x, end_y=end.y)
        self.compare_points(b.start, start)
        self.compare_points(b.end, end)

    def test_starts_and_end(self):
        b = BoundingBox(start_x=start.x, start_y=start.y, end=end)
        self.compare_points(b.start, start)
        self.compare_points(b.end, end)

    def test_starts_and_ends(self):
        b = BoundingBox(start_x=start.x, start_y=start.y, end_x=end.x, end_y=end.y)
        self.compare_points(b.start, start)
        self.compare_points(b.end, end)

    def test_start_and_width_height(self):
        b = BoundingBox(start=start, width=width, height=height)
        self.compare_points(b.start, start)
        self.compare_points(b.end, end)

    def test_starts_and_width_height(self):
        b = BoundingBox(start_x=start.x, start_y=start.y, width=width, height=height)
        self.compare_points(b.start, start)
        self.compare_points(b.end, end)

    def test_start_and_end_x_raises(self):
        with self.assertRaises(ValueError):
            b = BoundingBox(start=start, end_x=end.x)

    def test_starts_and_end_x_raises(self):
        with self.assertRaises(ValueError):
            b = BoundingBox(start_x=start.x, start_y=start.y, end_x=end.x)

    def test_start_and_end_y_raises(self):
        with self.assertRaises(ValueError):
            b = BoundingBox(start=start, end_y=end.y)

    def test_starts_and_end_y_raises(self):
        with self.assertRaises(ValueError):
            b = BoundingBox(start_x=start.x, start_y=start.y, end_y=end.y)

    def test_start_and_width_raises(self):
        with self.assertRaises(ValueError):
            b = BoundingBox(start=start, width=width)

    def test_starts_and_width_raises(self):
        with self.assertRaises(ValueError):
            b = BoundingBox(start_x=start.x, start_y=start.y, width=width)

    def test_start_and_height_raises(self):
        with self.assertRaises(ValueError):
            b = BoundingBox(start=start, height=height)

    def test_starts_and_height_raises(self):
        with self.assertRaises(ValueError):
            b = BoundingBox(start_x=start.x, start_y=start.y, height=height)

    def test_empty_raises(self):
        with self.assertRaises(ValueError):
            b = BoundingBox()

    def test_start_raises(self):
        with self.assertRaises(ValueError):
            b = BoundingBox(start=start)

    def test_starts_raises(self):
        with self.assertRaises(ValueError):
            b = BoundingBox(start_x=start.x, start_y=start.y)

    def test_end_raises(self):
        with self.assertRaises(ValueError):
            b = BoundingBox(end=end)

    def test_ends_raises(self):
        with self.assertRaises(ValueError):
            b = BoundingBox(end_x=end.x, end_y=end.y)


def main():
    args = parse_arguments()

    if args.verbose:
        suite = unittest.TestLoader().loadTestsFromTestCase(BoundingBoxTests)
        unittest.TextTestRunner(verbosity=2).run(suite)
    else:
        unittest.main()

    return 0


if __name__ == '__main__':
    sys.exit(main())