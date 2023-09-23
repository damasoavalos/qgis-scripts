import math
from pyproj import CRS

from qgis import processing
from qgis.core import (
                       QgsDistanceArea,
                       QgsVectorLayer,
                       QgsCoordinateReferenceSystem
                      )


def delete(var):
    var_exists = False
    try:
        var
    except NameError:
        var_exists = False
    else:
        var_exists = True
    if var_exists:
        del var


def angleDiff(angle1, angle2):
    return 180 - abs(abs(angle1 - angle2) - 180)


def reprojectLayer(_in_layer, to_epsg, _context, _feedback):
    if _feedback.isCanceled():
        return {}

    _parameter = {'INPUT': _in_layer,
                  'TARGET_CRS': to_epsg,
                  'OUTPUT': 'memory:temp'}
    _reprojectedLayer = processing.run('native:reprojectlayer', _parameter, context=_context)['OUTPUT']
    return _reprojectedLayer


def calculateDistance(_feature):
    calculator = QgsDistanceArea()
    calculator.setEllipsoid('WGS84')

    geom = _feature.geometry()
    _distance = calculator.measureLength(geom)
    delete(calculator)
    return _distance


def calculateAzimuth(v1, v2):
    _azimuth = None
    if v1.isEmpty() is False and v2.isEmpty() is False:
        _azimuth = math.trunc(v1.azimuth(v2))
        if _azimuth < 0:
            _azimuth += 360
    else:
        _azimuth = 0
    return _azimuth


def getStartEndPoints(_feature_line):
    first_vertex = None
    last_vertex = None
    for part in _feature_line.geometry().constGet():
        first_vertex = part[0]
        last_vertex = part[-1]
    return first_vertex, last_vertex


def createOutputVector(_in_layer, _geometry_type):
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


def isEven(number):
    even = False
    if number % 2 == 0:
        even = True  # Even
    else:
        even = False  # Odd
    return even


def getUtmZoneFromGeometry(feature, _feedback):
    if _feedback.isCanceled():
        return {}

    # Return the UTM Zone of the feature's geometry as a string
    centroid = feature.geometry().centroid()
    longitude = centroid.asPoint().x()
    latitude = centroid.asPoint().y()
    zone_number = math.floor(((longitude + 180) / 6) % 60) + 1

    if latitude >= 0:
        zone_letter = 'N'
    else:
        zone_letter = 'S'

    return '{0}{1}'.format(zone_number, zone_letter)


def getUtmZoneFromExtent(_extent, _feedback):
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


def reprojectToUtm(_in_layer, _utm_zone, _context, _feedback):
    if _feedback.isCanceled():
        return {}

    # we are going to hardcode "'WGS 84 / UTM zone" this part of the srs, for now.
    _stringUtmCrs = CRS.from_user_input('WGS 84 / UTM zone {}'.format(_utm_zone)).to_string()
    _parameter = {'INPUT': _in_layer,
                  'TARGET_CRS': _stringUtmCrs,
                  'OUTPUT': 'memory:temp'}
    _utm_layer = processing.run('native:reprojectlayer', _parameter, context=_context, feedback=_feedback)['OUTPUT']
    return _utm_layer


def reprojectToWGS84(_in_layer, _context, _feedback):
    if _feedback.isCanceled():
        return {}

    _parameter = {'INPUT': _in_layer,
                  'TARGET_CRS': QgsCoordinateReferenceSystem('EPSG:4326'),
                  'OUTPUT': 'memory:temp'}
    _wgs84_layer = processing.run('native:reprojectlayer', _parameter, context=_context, feedback=_feedback)['OUTPUT']
    return _wgs84_layer