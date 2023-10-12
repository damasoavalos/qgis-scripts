import matplotlib.pyplot as plt
import numpy as np
import json
import os


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


def shift_polygon_coordinates(_coordinates):
    """
    Shift the coordinates of a polygon by replacing the first pair with the second and closing the polygon.
    Parameters:
        _coordinates (list): List of tuples representing the coordinates (x, y) of the polygon.
    Returns:
        list: New list of shifted coordinates.
    """

    if len(_coordinates) < 3:
        return "A valid polygon must have at least 3 coordinates."

    # Remove the first coordinate
    shifted_coordinates = _coordinates[1:]

    # Add the second coordinate to the end to close the polygon
    shifted_coordinates.append(_coordinates[1])

    return shifted_coordinates


def shift_polygon_coordinates_reverse(_coordinates):
    """
    Shift and close the coordinates of a polygon by moving the last coordinate to the beginning and adding the penultimate coordinate to the beginning.

    Parameters:
        _coordinates (list): List of tuples representing the coordinates (x, y) of the polygon.

    Returns:
        list: New list of shifted and closed coordinates.
    """

    if len(_coordinates) < 3:
        return "A valid polygon must have at least 3 coordinates."

    # Move the last coordinate to the beginning
    shifted_coordinates_reverse = _coordinates[:-1]

    # Add the penultimate coordinate (which is now the second in the shifted list) to the beginning to close the polygon
    shifted_coordinates_reverse.insert(0, _coordinates[-2])

    return shifted_coordinates_reverse


def save_to_json_file(_data, _file_name):

    # Specify the relative path to the JSON file
    # _file_path = os.path.join('repos', 'qgis-scripts', 'data-json', '{}.json'.format(_file_name))
    _file_path = os.path.join(os.getcwd(), 'data-json', '{}.json'.format(_file_name))

    # Ensure the directory exists
    os.makedirs(os.path.dirname(_file_path), exist_ok=True)
    # Open the file for writing
    with open(_file_path, "w") as _file:
        # Write the data to the file
        json.dump(_data, _file, indent=4)  # The indent parameter is optional, and makes the file more readable


def read_from_json_file(_file_name):
    # Specify the relative path to the JSON file
    _file_path = os.path.join(os.getcwd(), 'data-json', _file_name)

    # Open the file for reading
    with open(_file_path, "r") as _file:
        # Load the data from the file
        return json.load(_file)


if __name__ == "__main__":
    # Define a convex polygon (in this example, a square)
    # polygon = [(0, 0), (4, 0), (4, 4), (0, 4), (0, 0)]

    polygon = read_from_json_file('data.json')

    # new_polygon = polygon
    # save_to_json_file(new_polygon, 'new-polygon_0')

    # new_polygon = shift_polygon_coordinates(new_polygon)
    # save_to_json_file(new_polygon, 'new-polygon_1')

    # new_polygon = shift_polygon_coordinates(new_polygon)
    # save_to_json_file(new_polygon, 'new-polygon_2')

    # new_polygon = shift_polygon_coordinates(new_polygon)
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
    save_to_json_file(new_polygon_reverse, 'new-polygon_reverse_0')

    new_polygon_reverse = shift_polygon_coordinates_reverse(new_polygon_reverse)
    save_to_json_file(new_polygon_reverse, 'new-polygon_reverse_1')

    new_polygon_reverse = shift_polygon_coordinates_reverse(new_polygon_reverse)
    save_to_json_file(new_polygon_reverse, 'new-polygon_reverse_2')

    new_polygon_reverse = shift_polygon_coordinates_reverse(new_polygon_reverse)
    save_to_json_file(new_polygon_reverse, 'new-polygon_reverse_3')

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
