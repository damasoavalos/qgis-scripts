import bezier
import numpy as np

from qgis.PyQt.QtCore import QCoreApplication, QVariant
from qgis.core import (QgsProcessing,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterEnum,
                       QgsGeometryUtils,
                       QgsVectorLayer,
                       QgsFeature,
                       QgsPoint,
                       QgsGeometry,
                       QgsField,
                       QgsFeatureSink,
                       QgsProject,
                       QgsWkbTypes)

from sys import path
import os
path.append(os.path.dirname(os.path.realpath(__file__)))
import utils


class SmoothBezier(QgsProcessingAlgorithm):
    INPUT = 'INPUT'
    OUTPUT = 'OUTPUT'
    NUMBERS_OF_POINTS_TO_PLOT = 'NUMBERS_OF_POINTS_TO_PLOT'

    def __init__(self):
        super().__init__()

    def tr(self, string):
        # Returns a translatable string with the self.tr() function.
        return QCoreApplication.translate('Processing', string)

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterFeatureSource(self.INPUT, self.tr('Line'), [QgsProcessing.TypeVectorLine], None))
        self.addParameter(QgsProcessingParameterNumber(self.NUMBERS_OF_POINTS_TO_PLOT, self.tr('Numbers of points to plot'), type=QgsProcessingParameterNumber.Integer, minValue=10, defaultValue=25))
        self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT, self.tr('Line smoothed'), type=QgsProcessing.TypeVectorLine))

    def create_temp_layer(self, _input_layer):
        # Convert its geometry type enum to a string we can pass to utils.createOutputVector function
        in_layer_geometry_type = ['Point', 'Linestring', 'Polygon'][_input_layer.geometryType()]
        _temp_layer = utils.create_output_vector(_input_layer, in_layer_geometry_type)

        _temp_layer_pr = _temp_layer.dataProvider()
        _temp_layer_pr.addAttributes([QgsField('f_id', QVariant.Int)])
        _temp_layer.updateFields()
        return _temp_layer

    def add_feature_to_layer(self, _temp_layer, _output_curve_points, _fid):
        out_feat = QgsFeature()
        out_feat.setGeometry(QgsGeometry.fromPolyline(_output_curve_points))
        out_feat.setAttributes([_fid])
        _temp_layer_pr = _temp_layer.dataProvider()
        _temp_layer_pr.addFeature(out_feat)
        _temp_layer.updateExtents()
        return _temp_layer

    def get_line_centroid(self, _point_a_x, _point_a_y, _point_b_x, _point_b_y):
        point_centroid = QgsGeometry.fromPolyline([QgsPoint(_point_a_x, _point_a_y), QgsPoint(_point_b_x, _point_b_y)]).centroid()
        return point_centroid

    def number_of_vertices(self, _vertex_iterator):
        count = 0
        for vertex in _vertex_iterator:
            count += 1
        return count

    def processAlgorithm(self, parameters, context, feedback):

        # import pydevd_pycharm
        # pydevd_pycharm.settrace('127.0.0.1', port=53100, stdoutToServer=True, stderrToServer=True)

        input_layer = self.parameterAsVectorLayer(parameters, self.INPUT, context)
        numbers_of_points_to_plot = self.parameterAsInt(parameters, self.NUMBERS_OF_POINTS_TO_PLOT, context)

        temp_layer = self.create_temp_layer(input_layer)

        features = input_layer.getFeatures()
        for j, feature in enumerate(features):
            output_curve_points = []
            geom = feature.geometry()
            number_of_vertices = self.number_of_vertices(geom.vertices())
            for i in range(number_of_vertices):
                # Find adjacents vertices for each vertice
                adjacent_vertices = geom.adjacentVertices(i)

                # Do nothing with the first and last vertice
                if adjacent_vertices[0] > -1 and adjacent_vertices[1] > -1:

                    point_center_x = geom.vertexAt(i).x()
                    point_center_y = geom.vertexAt(i).y()

                    # Calculate the Bézier curve using the centroid of each line,
                    # except the first and last line for which we used the first and last vertice of those lines.
                    if i == 1:
                        point_a_x = geom.vertexAt(adjacent_vertices[0]).x()
                        point_a_y = geom.vertexAt(adjacent_vertices[0]).y()

                        point_c = self.get_line_centroid(point_center_x, point_center_y, geom.vertexAt(adjacent_vertices[1]).x(), geom.vertexAt(adjacent_vertices[1]).y()).asPoint()
                        point_c_x = point_c.x()
                        point_c_y = point_c.y()
                    elif i == number_of_vertices - 2:
                        point_a = self.get_line_centroid(geom.vertexAt(adjacent_vertices[0]).x(), geom.vertexAt(adjacent_vertices[0]).y(), point_center_x, point_center_y).asPoint()
                        point_a_x = point_a.x()
                        point_a_y = point_a.y()

                        point_c_x = geom.vertexAt(adjacent_vertices[1]).x()
                        point_c_y = geom.vertexAt(adjacent_vertices[1]).y()
                    else:
                        point_a = self.get_line_centroid(geom.vertexAt(adjacent_vertices[0]).x(), geom.vertexAt(adjacent_vertices[0]).y(), point_center_x, point_center_y).asPoint()
                        point_a_x = point_a.x()
                        point_a_y = point_a.y()

                        point_c = self.get_line_centroid(point_center_x, point_center_y, geom.vertexAt(adjacent_vertices[1]).x(), geom.vertexAt(adjacent_vertices[1]).y()).asPoint()
                        point_c_x = point_c.x()
                        point_c_y = point_c.y()

                    # Calculate the quadratic Bézier curve using three points(aka vertices), center point, point a and point b
                    points = np.asfortranarray([[point_a_x, point_center_x, point_c_x], [point_a_y, point_center_y, point_c_y]])
                    bezier_curve = bezier.Curve(points, degree=2)

                    # Once the Bézier curve is calculated we need to obtain the coordinates values of different points in the curve to represent it on the map.
                    # The more points we use the more smooth is going to be the curve representation.
                    points_to_plot = np.linspace(0.0, 1.0, numbers_of_points_to_plot)
                    points_in_bezier_curve = bezier_curve.evaluate_multi(points_to_plot)

                    # translate the points in the Bézier curve into a list of qgis points to create the lines in the map
                    for n in range(numbers_of_points_to_plot):
                        output_curve_point = QgsPoint(points_in_bezier_curve[0][n], points_in_bezier_curve[1][n])
                        output_curve_points.append(output_curve_point)
            self.add_feature_to_layer(temp_layer, output_curve_points, (j + 1))

        # OUTPUT
        parameters['OUTPUT'].destinationName = 'Line-Smoothed-Bezier-{}'.format(input_layer.name())
        (sink, dest_id) = self.parameterAsSink(parameters, self.OUTPUT, context, input_layer.fields(), QgsWkbTypes.LineString, input_layer.crs())
        sink.addFeatures(temp_layer.getFeatures(), QgsFeatureSink.FastInsert)
        return {self.OUTPUT: dest_id}

    def name(self):
        return 'SmoothBezier'

    def displayName(self):
        return self.tr('Smooth Bezier')

    def group(self):
        return self.tr('Smooth Scripts')

    def groupId(self):
        return 'smoothscripts'

    def createInstance(self):
        return SmoothBezier()

    def flags(self):
        return super().flags() | QgsProcessingAlgorithm.FlagNoThreading
