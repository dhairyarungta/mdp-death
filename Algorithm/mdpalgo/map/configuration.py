class Pose(object):
    def __init__(self, target: list = None):
        """target is a list of (x, y, direction)"""
        self.x: int = 0
        self.y: int = 0
        self.direction: int = 0

        if target:
            self.set_pose(target)

    def set_pose(self, target: list):
        """target is a list of (x, y, direction)"""
        if len(target) != 3:
            raise ValueError("pose must have 3 elements (x, y, direction)")

        self.x = int(target[0])
        self.y = int(target[1])
        self.direction = int(target[2])

    def to_tuple(self) -> tuple:
        return (self.x, self.y, self.direction)

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y and self.direction == other.direction
