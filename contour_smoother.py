
from qgis.PyQt.QtCore import QCoreApplication, QVariant
from qgis.core import (QgsProcessing,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterBoolean,
                       QgsProcessingParameterEnum,
                       QgsGeometryUtils,
                       QgsVectorLayer,
                       QgsFeature,
                       QgsPoint,
                       QgsGeometry,
                       QgsField,
                       QgsFeatureSink,
                       QgsProject,
                       QgsWkbTypes,
                       QgsCoordinateReferenceSystem
                       )
from qgis import processing

from sys import path
import os
path.append(os.path.dirname(os.path.realpath(__file__)))
import utils


class ContourSmoother(QgsProcessingAlgorithm):
    INPUT_CONTOUR_LINES = 'INPUT_CONTOUR_LINES'
    INPUT_BOUNDARIES = 'INPUT_BOUNDARIES'
    NUMBER_OF_ITERATIONS = 'NUMBER_OF_ITERATIONS'
    SIMPLIFY = 'SIMPLIFY'
    OUTPUT = 'OUTPUT'

    def __init__(self):
        super().__init__()

    def tr(self, string):
        # Returns a translatable string with the self.tr() function.
        return QCoreApplication.translate('Processing', string)

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterFeatureSource(self.INPUT_CONTOUR_LINES, self.tr('Contour Lines'), [QgsProcessing.TypeVectorLine], None))
        self.addParameter(QgsProcessingParameterFeatureSource(self.INPUT_BOUNDARIES, self.tr('Boundaries'), [QgsProcessing.TypeVectorPolygon], None))
        self.addParameter(QgsProcessingParameterNumber(self.NUMBER_OF_ITERATIONS, self.tr('Number of Iiterations'), type=QgsProcessingParameterNumber.Integer, minValue=1, defaultValue=5))
        self.addParameter(QgsProcessingParameterBoolean(self.SIMPLIFY, self.tr('Simplify?'), defaultValue=True))
        self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT, self.tr('Contour smoothed'), type=QgsProcessing.TypeVectorLine))

    def processAlgorithm(self, parameters, context, feedback):

        # import pydevd_pycharm
        # pydevd_pycharm.settrace('127.0.0.1', port=53100, stdoutToServer=True, stderrToServer=True)

        input_layer_contour = self.parameterAsVectorLayer(parameters, self.INPUT_CONTOUR_LINES, context)
        input_layer_boundaries = self.parameterAsVectorLayer(parameters, self.INPUT_BOUNDARIES, context)
        number_of_iterations = self.parameterAsInt(parameters, self.NUMBER_OF_ITERATIONS, context)
        simplify = self.parameterAsInt(parameters, self.SIMPLIFY, context)

        parameters['OUTPUT'].destinationName = 'contour_smoother_{}'.format(input_layer_contour.name())
        # (sink, dest_id) = self.parameterAsSink(parameters, self.OUTPUT, context, input_layer_contour.fields(), QgsWkbTypes.LineString, input_layer_contour.crs())
        (sink, dest_id) = self.parameterAsSink(parameters, self.OUTPUT, context, input_layer_contour.fields(), QgsWkbTypes.LineString, QgsCoordinateReferenceSystem('EPSG:4326'))

        features_boundary = input_layer_boundaries.getFeatures()
        for i, feature in enumerate(features_boundary):
            utm_zone = utils.get_utm_zone_from_geometry(feature, feedback)
            input_layer_boundaries.select(feature.id())
            _selected_input_layer_boundaries = processing.run("native:saveselectedfeatures", {'INPUT': input_layer_boundaries, 'OUTPUT': 'memory:'})['OUTPUT']
            utm_layer_boundary = utils.reproject_to_utm(_selected_input_layer_boundaries, utm_zone, context, feedback)
            utm_layer_contour = utils.reproject_to_utm(input_layer_contour, utm_zone, context, feedback)

            buffer_params = {
                'INPUT': utm_layer_boundary,
                'DISTANCE': 100,  # 100 meters hardcode for now
                'SEGMENTS': 5,
                'END_CAP_STYLE': 0,
                'JOIN_STYLE': 0,
                'MITER_LIMIT': 2,
                'DISSOLVE': False,
                'OUTPUT': 'memory:'
                }
            buffered_layer_boundary = processing.run('native:buffer', buffer_params)['OUTPUT']

            clip_params = {
                'INPUT': utm_layer_contour,
                'OVERLAY': buffered_layer_boundary,
                'OUTPUT': 'memory:'
                }
            clipped_layer_contour = processing.run("native:clip", clip_params)['OUTPUT']
            layer_contour = clipped_layer_contour.clone()

            for x in range(number_of_iterations):
                # Smooth
                smooth_params = {
                    'INPUT': layer_contour,
                    'ITERATIONS': 10,
                    'MAX_ANGLE': 180,
                    'OFFSET': 0.25,
                    'OUTPUT': 'memory:'
                }
                smoothed_layer_contour = processing.run('native:smoothgeometry', smooth_params)['OUTPUT']

                # Simplify
                if simplify:
                    simplify_params = {
                        'INPUT': smoothed_layer_contour,
                        'METHOD': 0,
                        'TOLERANCE': 100,
                        'OUTPUT': 'memory:'
                    }
                    simplified_layer_contour = processing.run('native:simplifygeometries', simplify_params)['OUTPUT']
                    layer_contour = simplified_layer_contour.clone()

            wgs84_layer_contour = utils.reproject_to_wgs84(layer_contour, context, feedback)
            sink.addFeatures(wgs84_layer_contour.getFeatures(), QgsFeatureSink.FastInsert)
            input_layer_boundaries.removeSelection()
        return {self.OUTPUT: dest_id}

    def name(self):
        return 'ContourSmoother'

    def displayName(self):
        return self.tr('Contour Smoother')

    def group(self):
        return self.tr('Smooth Scripts')

    def groupId(self):
        return 'smoothscripts'

    def createInstance(self):
        return ContourSmoother()

    def flags(self):
        return super().flags() | QgsProcessingAlgorithm.FlagNoThreading
