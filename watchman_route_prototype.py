import matplotlib.pyplot as plt
import numpy as np
import os
from sys import path
path.append(os.path.dirname(os.path.realpath(__file__)))
import utils


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
    # polygon = [(0, 0), (4, 0), (4, 4), (0, 4), (0, 0)]

    polygon = utils.read_from_json_file('data.json')

    # new_polygon = polygon
    # save_to_json_file(new_polygon, 'new-polygon_0')

    # new_polygon = utils.shift_polygon_coordinates(new_polygon)
    # save_to_json_file(new_polygon, 'new-polygon_1')

    # new_polygon = utils.shift_polygon_coordinates(new_polygon)
    # save_to_json_file(new_polygon, 'new-polygon_2')

    # new_polygon = utils.shift_polygon_coordinates(new_polygon)
    # save_to_json_file(new_polygon, 'new-polygon_3')

    # # Triangulate the polygon
    # triangles = triangulate_convex_polygon(new_polygon)
    #
    # # Find the shortest path to traverse all triangles
    # path = find_shortest_path(triangles)
    #
    # # Plot the polygon
    # plot_polygon(new_polygon)
    #
    # # Plot the triangles
    # for triangle in triangles:
    #     plot_polygon(triangle, color='g')
    #
    # # Plot the path
    # plot_path([new_polygon[0]] + path + [new_polygon[0]], color='r')
    # plt.axis('equal')
    #
    # plt.show()

# == Reverse ==============================================================================================
    new_polygon_reverse = polygon
    utils.save_to_json_file(new_polygon_reverse, 'new-polygon_reverse_0')

    new_polygon_reverse = utils.shift_polygon_coordinates_reverse(new_polygon_reverse)
    utils.save_to_json_file(new_polygon_reverse, 'new-polygon_reverse_1')

    new_polygon_reverse = utils.shift_polygon_coordinates_reverse(new_polygon_reverse)
    utils.save_to_json_file(new_polygon_reverse, 'new-polygon_reverse_2')

    new_polygon_reverse = utils.shift_polygon_coordinates_reverse(new_polygon_reverse)
    utils.save_to_json_file(new_polygon_reverse, 'new-polygon_reverse_3')

    # Triangulate the polygon
    triangles = triangulate_convex_polygon(new_polygon_reverse)

    # Find the shortest path to traverse all triangles
    path = find_shortest_path(triangles)

    # Plot the polygon
    plot_polygon(new_polygon_reverse)

    # Plot the triangles
    for triangle in triangles:
        plot_polygon(triangle, color='g')

    # Plot the path
    plot_path([new_polygon_reverse[0]] + path + [new_polygon_reverse[0]], color='r')
    plt.axis('equal')

    plt.show()
