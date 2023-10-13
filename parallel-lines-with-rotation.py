from shapely.geometry import Polygon, LineString
from shapely.affinity import rotate
import geopandas as gpd
import matplotlib.pyplot as plt

import os
from sys import path
path.append(os.path.dirname(os.path.realpath(__file__)))
import utils


def create_parallel_lines(_param):
    # Initialize list to store lines
    _lines = []

    # Generate lines
    _start_y = _param['extended_min_y']  # Start from the bottom-most y-coordinate
    while _start_y <= _param['extended_max_y']:
        # Create line at the current y-coordinate
        _line = LineString([(_param['extended_min_x'], _start_y), (_param['extended_max_x'], _start_y)])

        # Rotate line by orientation angle
        _line_rotated = rotate(_line, _param['orientation_angle'], origin='centroid')

        # If rotated line intersects polygon, add to list
        if _line_rotated.intersects(_param['polygon']):
            _lines.append(_line_rotated.intersection(_param['polygon']))

        # Increment y-coordinate based on spacing
        _start_y += _param['line_spacing']

    # Create GeoDataFrames for plotting
    gdf_polygon = gpd.GeoDataFrame({'geometry': [polygon]})
    gdf_lines_rotated = gpd.GeoDataFrame({'geometry': _lines})

    # Plotting
    fig, ax = plt.subplots()
    gdf_polygon.boundary.plot(ax=ax, linewidth=2, color='black', label='Polygon')
    gdf_lines_rotated.plot(ax=ax, linewidth=1, color='blue', label='Rotated Parallel Lines')
    plt.legend()
    plt.axis('equal')
    plt.title(str('Azimuth - {}'.format(_param['orientation_angle'])))
    plt.show()


if __name__ == "__main__":
    # Create a simple polygon (a square for this example)
    polygon = Polygon(utils.read_from_json_file('data.json'))
    # polygon = Polygon([(0, 0), (0, 10), (10, 10), (10, 0), (0, 0)])

    # Set parameters
    orientation_angle = 0  # Angle in degrees, 30 means lines will be rotated by 30 degrees
    line_spacing = 400  # Spacing between lines

    # Get the bounding box of the polygon
    min_x, min_y, max_x, max_y = polygon.bounds

    # Calculate a larger bounding box to accommodate rotation
    buffer_distance = max(max_x - min_x, max_y - min_y)
    extended_min_x = min_x - buffer_distance
    extended_min_y = min_y - buffer_distance
    extended_max_x = max_x + buffer_distance
    extended_max_y = max_y + buffer_distance

    parameters = {
        'polygon': polygon,
        'orientation_angle': orientation_angle,
        'line_spacing': line_spacing,
        'extended_min_x': extended_min_x,
        'extended_min_y': extended_min_y,
        'extended_max_x': extended_max_x,
        'extended_max_y': extended_max_y
    }
    orientation_angles = [0, 45, 90, 135, 180, 225, 270, 315, 360]
    for orientation_angle in orientation_angles:
        parameters['orientation_angle'] = orientation_angle
        create_parallel_lines(parameters)
