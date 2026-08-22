import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lc735_asteroid_collision import asteroid_collision


class TestAsteroidCollision(unittest.TestCase):
    def test_larger_survives(self) -> None:
        self.assertEqual(asteroid_collision([5, 10, -5]), [5, 10])

    def test_equal_sizes_both_explode(self) -> None:
        self.assertEqual(asteroid_collision([8, -8]), [])

    def test_chain_reaction_survivor_keeps_colliding(self) -> None:
        self.assertEqual(asteroid_collision([10, 2, -5]), [10])

    def test_diverging_asteroids_never_collide(self) -> None:
        self.assertEqual(asteroid_collision([-2, -1, 1, 2]), [-2, -1, 1, 2])

    def test_smaller_right_mover_destroyed_first(self) -> None:
        self.assertEqual(asteroid_collision([1, -2, -2, -2]), [-2, -2, -2])

    def test_all_moving_left_no_collisions(self) -> None:
        self.assertEqual(asteroid_collision([-3, -1, -2]), [-3, -1, -2])

    def test_all_moving_right_no_collisions(self) -> None:
        self.assertEqual(asteroid_collision([1, 2, 3]), [1, 2, 3])

    def test_single_asteroid(self) -> None:
        self.assertEqual(asteroid_collision([4]), [4])

    def test_empty_input(self) -> None:
        self.assertEqual(asteroid_collision([]), [])

    def test_long_chain_wipes_out_multiple_survivors(self) -> None:
        # A single large left-mover should demolish an entire run of
        # smaller right-movers in front of it.
        self.assertEqual(asteroid_collision([1, 2, 3, -10]), [-10])


if __name__ == "__main__":
    unittest.main()
