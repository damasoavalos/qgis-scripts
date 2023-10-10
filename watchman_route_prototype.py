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
    # polygon = [(0, 0), (4, 0), (4, 4), (0, 4)]
    polygon = [(-113.98565731933435, 51.37608388363282), (-113.99083576956154, 51.36656998670381),
               (-113.99757979776439, 51.35320235937316), (-113.99420778366297, 51.34681961839546),
               (-113.99011319511123, 51.33405413644006), (-113.97794985853109, 51.328875686212875),
               (-113.96398008582518, 51.33309070383965), (-113.96181236247428, 51.341882026318366),
               (-113.95940378097326, 51.35741737699993), (-113.95302103999556, 51.37427744750706),
               (-113.96325751137488, 51.37752903253344), (-113.97313269552906, 51.3793354686592),
               (-113.97566170610513, 51.38174405016022), (-113.98565731933435, 51.37608388363282)]

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
