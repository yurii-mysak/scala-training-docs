"""
LC 735 - Asteroid Collision
https://leetcode.com/problems/asteroid-collision/

Each asteroid moves at the same speed; sign gives direction (positive =
right, negative = left), magnitude gives size. Same-direction asteroids
never meet. When a right-moving asteroid is later followed by a
left-moving one, they collide: the smaller explodes, equal sizes both
explode, and if the survivor is still moving left it keeps colliding with
whatever is now behind it. Return the surviving asteroids, left to right.

Companion doc: lc735-asteroid-collision.md
"""
from __future__ import annotations

from typing import List


def asteroid_collision(asteroids: List[int]) -> List[int]:
    """Monotonic stack: only a right-moving top can collide with a
    left-moving newcomer, so the stack only ever needs to look at its own
    top -- never deeper -- to decide the next collision.
    """
    stack: List[int] = []

    for a in asteroids:
        alive = True
        while alive and a < 0 and stack and stack[-1] > 0:
            top = stack[-1]
            if top < -a:
                stack.pop()       # top explodes; `a` keeps moving left
            elif top == -a:
                stack.pop()       # both explode
                alive = False
            else:
                alive = False     # `a` explodes; top survives untouched
        if alive:
            stack.append(a)

    return stack


if __name__ == "__main__":
    demos = [
        [5, 10, -5],
        [8, -8],
        [10, 2, -5],
        [-2, -1, 1, 2],
        [1, -2, -2, -2],
    ]
    for asteroids in demos:
        print(f"asteroid_collision({asteroids}) = {asteroid_collision(asteroids)}")
