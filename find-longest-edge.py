import math


def distance(point1, point2):
    """Calculate the distance between two points represented as (x, y) tuples."""
    x1, y1 = point1
    x2, y2 = point2

    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)


def find_longest_edge(_polygon):
    """Find the longest edge of a polygon.
    Parameters:
        _polygon (list): A list of (x, y) tuples representing the vertices of the polygon.
    Returns:
        tuple: A tuple containing the coordinates of the endpoints of the longest edge and its length.
    """

    _max_length = 0
    _longest_edge = None

    # Loop through each edge of the polygon
    for i in range(len(_polygon)):
        point1 = _polygon[i]
        point2 = _polygon[(i + 1) % len(_polygon)]  # Wrap around to the first point for the last edge

        edge_length = distance(point1, point2)
        if edge_length > _max_length:
            _max_length = edge_length
            _longest_edge = (point1, point2)

    return _longest_edge, _max_length


# Example usage:
if __name__ == "__main__":
    polygon = [(0, 0), (4, 0), (4, 3), (0, 3)]
    longest_edge, max_length = find_longest_edge(polygon)
    print(f"The longest edge is between {longest_edge} with a length of {max_length:.2f}")
