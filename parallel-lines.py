from shapely.geometry import Polygon, LineString
import geopandas as gpd
import matplotlib.pyplot as plt

import os
from sys import path
path.append(os.path.dirname(os.path.realpath(__file__)))
import utils

if __name__ == "__main__":
    # Create a simple polygon (a square in this example)
    polygon = Polygon(utils.read_from_json_file('data.json'))
    # polygon = Polygon([(0, 0), (0, 10), (10, 10), (10, 0), (0, 0)])

    # Determine parameters
    orientation_angle = 45  # Angle in degrees, 0 means horizontal lines
    line_spacing = 500  # Spacing between lines

    # Find the bounding box of the polygon
    min_x, min_y, max_x, max_y = polygon.bounds

    # Initialize list to store lines
    lines = []

    # Generate lines
    start_y = min_y  # Start from the bottom-most y-coordinate
    while start_y <= max_y:
        # Create line at the current y-coordinate
        line = LineString([(min_x, start_y), (max_x, start_y)])

        # If line intersects polygon, add to list
        if line.intersects(polygon):
            lines.append(line.intersection(polygon))

        # Increment y-coordinate based on spacing
        start_y += line_spacing

    # Create GeoDataFrames for plotting
    gdf_polygon = gpd.GeoDataFrame({'geometry': [polygon]})
    gdf_lines = gpd.GeoDataFrame({'geometry': lines})

    # Plotting
    fig, ax = plt.subplots()
    gdf_polygon.boundary.plot(ax=ax, linewidth=2, color='black', label='Polygon')
    gdf_lines.plot(ax=ax, linewidth=1, color='red', label='Parallel Lines')
    plt.legend()
    plt.axis('equal')
    plt.show()
