import matplotlib.pyplot as plt
import numpy as np


def plot_polygon(_polygon, color='b'):
    """Plot a polygon."""
    x, y = zip(*_polygon)
    plt.fill(x, y, alpha=0.2, color=color)
    plt.plot(x + (x[0],), y + (y[0],), color=color)


def plot_path(points, color='r'):
    """Plot a path between points."""
    x, y = zip(*points)
    plt.plot(x, y, color=color)


def triangulate_convex_polygon(_polygon):
    """Triangulate a convex polygon."""
    _triangles = []
    for i in range(1, len(_polygon) - 1):
        _triangle = [_polygon[0], _polygon[i], _polygon[i + 1]]
        _triangles.append(_triangle)

    return _triangles


def find_shortest_path(_triangles):
    """Find the shortest path to traverse all triangles."""
    _path = []
    for _triangle in _triangles:
        centroid = np.mean(_triangle, axis=0).tolist()
        _path.append(centroid)

    return _path


if __name__ == "__main__":
    # Define a convex polygon (in this example, a square)
    polygon = [(0, 0), (4, 0), (4, 4), (0, 4)]

    # Triangulate the polygon
    triangles = triangulate_convex_polygon(polygon)

    # Find the shortest path to traverse all triangles
    path = find_shortest_path(triangles)

    # Plot the polygon
    plot_polygon(polygon)

    # Plot the triangles
    for triangle in triangles:
        plot_polygon(triangle, color='g')

    # Plot the path
    plot_path([polygon[0]] + path + [polygon[0]], color='r')
    plt.axis('equal')

    plt.show()
