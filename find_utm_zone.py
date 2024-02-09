import os
# import pydevd_pycharm
from math import floor
from pyproj import CRS

# from qgis.PyQt.QtGui import QIcon
# from qgis.PyQt.QtCore import QCoreApplication

from qgis.core import (QgsApplication,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterExtent,
                       QgsProcessingParameterVectorLayer,
                       QgsProcessing,
                       QgsProcessingParameterFeatureSink)
# import processing
from qgis import processing


class FindUtmZone(QgsProcessingAlgorithm):
    INPUT = 'INPUT'
    OUTPUT = 'OUTPUT'
    EXTENT = 'EXTENT'

    def tr(self, string):
        # Returns a translatable string with the self.tr() function.        
        return 'Processing'

    def __init__(self):
        super().__init__()

    def initAlgorithm(self, config=None):
        # self.addParameter(QgsProcessingParameterVectorLayer(self.INPUT, 'Input layer', types=[QgsProcessing.TypeVectorPoint]))
        # self.addParameter(QgsProcessingParameterVectorLayer(self.INPUT, 'Input layer'))
        self.addParameter(QgsProcessingParameterExtent(self.EXTENT, 'Input extent to calculate UTM zone'))
        # self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT, 'Output Triangulation', type=QgsProcessing.TypeVectorPolygon))

    def find_utm_zone(self, _rect, _feedback):
        if _feedback.isCanceled():
            return {}

        minx = _rect.xMinimum()
        miny = _rect.yMinimum()
        height = _rect.height()
        width = _rect.width()
        longitude = minx + width / 2.0
        latitude = miny + height / 2.0
        zone_number = floor(((longitude + 180) / 6) % 60) + 1

        if latitude >= 0:
            zone_letter = 'N'
        else:
            zone_letter = 'S'
        return '{0}{1}'.format(zone_number, zone_letter)

    # def ReprojectToUtm(self, _in_layer, _utmZone, _context, _feedback):
    #    if _feedback.isCanceled():
    #           return {} 

    #    # we are going to hardcode "'WGS 84 / UTM zone" this part of the srs, for now.
    #    _stringUtmCrs = CRS.from_user_input('WGS 84 / UTM zone {}'.format(_utmZone)).to_string()
    #    _parameter = {'INPUT': _in_layer, 'TARGET_CRS': _stringUtmCrs, 'OUTPUT': 'memory:temp'}
    #    _utmLayer = processing.run('native:reprojectlayer', _parameter, context=_context, feedback=_feedback)['OUTPUT'] 
    #    return _utmLayer

    def processAlgorithm(self, parameters, context, feedback):
        # pydevd_pycharm.settrace('127.0.0.1', port=53100, stdoutToServer=True, stderrToServer=True)
        # in_layer = self.parameterAsLayer(parameters, self.INPUT, context)
        rect = self.parameterAsExtent(parameters, self.EXTENT, context)

        results = {}

        # -Find UTM zone- 
        utm_zone = self.find_utm_zone(rect, feedback)
        feedback.pushInfo('UTM Zone: {0}'.format(utm_zone))

        # -Reproject to UTM-
        # utmLayer  = self.ReprojectToUtm(inLayer, utmZone, context, feedback)
        # feedback.pushInfo("Layer reprojected to 'UTM Zone: {0}'".format(utmZone))

        return results

    def name(self):
        return 'findutmzone'

    def displayName(self):
        return 'Find Utm Zone'

    def group(self):
        return 'First Pass Tools'

    def groupId(self):
        return 'firstpasstools'

    def createInstance(self):
        return FindUtmZone()

    # def icon(self):
    #    return QgsApplication.getThemeIcon("/algorithms/mAlgorithmExtractLayerExtent.svg")

    # def svgIconPath(self):
    #    return QgsApplication.iconPath("/algorithms/mAlgorithmExtractLayerExtent.svg")

    # def tags(self):
    #    return 'polygon,vector,raster,extent,envelope,bounds,bounding,boundary,layer,round,rounded'.split(',')
