from pyproj import CRS

from qgis import processing
from qgis.core import (
                       QgsDistanceArea,
                       QgsVectorLayer,
                       QgsCoordinateReferenceSystem
                      )

import math
import os
import json


def delete(_var):
    # var_exists = False
    try:
        _var
    except NameError:
        var_exists = False
    else:
        var_exists = True
    if var_exists:
        del _var


def angle_diff(_angle1, _angle2):
    return 180 - abs(abs(_angle1 - _angle2) - 180)


def reproject_layer(_in_layer, _to_epsg, _context, _feedback):
    if _feedback.isCanceled():
        return {}

    _parameter = {'INPUT': _in_layer,
                  'TARGET_CRS': _to_epsg,
                  'OUTPUT': 'memory:temp'}
    _reprojectedLayer = processing.run('native:reprojectlayer', _parameter, context=_context)['OUTPUT']
    return _reprojectedLayer


def calculate_distance(_feature):
    calculator = QgsDistanceArea()
    calculator.setEllipsoid('WGS84')

    geom = _feature.geometry()
    _distance = calculator.measureLength(geom)
    delete(calculator)
    return _distance


def calculate_azimuth(_v1, _v2):
    _azimuth = None
    if _v1.isEmpty() is False and _v2.isEmpty() is False:
        _azimuth = math.trunc(_v1.azimuth(_v2))
        if _azimuth < 0:
            _azimuth += 360
    else:
        _azimuth = 0
    return _azimuth


def get_start_end_points(_feature_line):
    first_vertex = None
    last_vertex = None
    for part in _feature_line.geometry().constGet():
        first_vertex = part[0]
        last_vertex = part[-1]
    return first_vertex, last_vertex


def create_output_vector(_in_layer, _geometry_type):
    # Get its list of fields
    _in_fields = _in_layer.dataProvider().fields()

    # Convert its CRS to a string we can pass to QgsVectorLayer's constructor
    _in_layerCRS = _in_layer.crs().authid()

    # Make the output layer
    _out_layer = QgsVectorLayer(_geometry_type + '?crs=' + _in_layerCRS, _in_layer.name() + u'_copy', 'memory')

    # Copy the fields from _in_layer into the new layer
    _out_layer.startEditing()
    _out_layer.dataProvider().addAttributes(_in_fields.toList())
    _out_layer.commitChanges()

    return _out_layer


def is_even(_number):
    # even = False
    if _number % 2 == 0:
        even = True  # Even
    else:
        even = False  # Odd
    return even


def get_utm_zone_from_geometry(_feature, _feedback):
    if _feedback.isCanceled():
        return {}

    # Return the UTM Zone of the feature's geometry as a string
    centroid = _feature.geometry().centroid()
    longitude = centroid.asPoint().x()
    latitude = centroid.asPoint().y()
    zone_number = math.floor(((longitude + 180) / 6) % 60) + 1

    if latitude >= 0:
        zone_letter = 'N'
    else:
        zone_letter = 'S'

    return '{0}{1}'.format(zone_number, zone_letter)


def get_utm_zone_from_extent(_extent, _feedback):
    if _feedback.isCanceled():
        return {}
    # Return the UTM Zone of the extent as a string
    minx = _extent.xMinimum()
    miny = _extent.yMinimum()
    height = _extent.height()
    width = _extent.width()
    longitude = minx + width / 2.0
    latitude = miny + height / 2.0
    zone_number = math.floor(((longitude + 180) / 6) % 60) + 1

    if latitude >= 0:
        zone_letter = 'N'
    else:
        zone_letter = 'S'
    return '{0}{1}'.format(zone_number, zone_letter)


def reproject_to_utm(_in_layer, _utm_zone, _context, _feedback):
    if _feedback.isCanceled():
        return {}

    # we are going to hardcode "WGS 84 / UTM zone" this part of the srs, for now.
    _stringUtmCrs = CRS.from_user_input('WGS 84 / UTM zone {}'.format(_utm_zone)).to_string()
    _parameter = {'INPUT': _in_layer,
                  'TARGET_CRS': _stringUtmCrs,
                  'OUTPUT': 'memory:temp'}
    _utm_layer = processing.run('native:reprojectlayer', _parameter, context=_context, feedback=_feedback)['OUTPUT']
    return _utm_layer


def reproject_to_wgs84(_in_layer, _context, _feedback):
    if _feedback.isCanceled():
        return {}

    _parameter = {'INPUT': _in_layer,
                  'TARGET_CRS': QgsCoordinateReferenceSystem('EPSG:4326'),
                  'OUTPUT': 'memory:temp'}
    _wgs84_layer = processing.run('native:reprojectlayer', _parameter, context=_context, feedback=_feedback)['OUTPUT']
    return _wgs84_layer

# ===== Ideas-to-make-money =================================================================================================


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
