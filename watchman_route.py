from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsProcessing,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterVectorDestination)

import matplotlib.pyplot as plt
import numpy as np


class WatchmanRoute(QgsProcessingAlgorithm):
    """
    Algorithm to implement a solution to a Watchman Route problem
    """

    def plot_polygon(self, _polygon, color='b'):
        """Plot a polygon."""
        x, y = zip(*_polygon)
        plt.fill(x, y, alpha=0.2, color=color)
        plt.plot(x + (x[0],), y + (y[0],), color=color)

    def plot_path(self, points, color='r'):
        """Plot a path between points."""
        x, y = zip(*points)
        plt.plot(x, y, color=color)

    def triangulate_convex_polygon(self, _polygon):
        """Triangulate a convex polygon."""
        _triangles = []
        for i in range(1, len(_polygon) - 1):
            _triangle = [_polygon[0], _polygon[i], _polygon[i + 1]]
            _triangles.append(_triangle)

        return _triangles

    def find_shortest_path(self, _triangles):
        """Find the shortest path to traverse all triangles."""
        _path = []
        for _triangle in _triangles:
            centroid = np.mean(_triangle, axis=0).tolist()
            _path.append(centroid)

        return _path

    def initAlgorithm(self, config=None):
        """
        Here we define the inputs and outputs of the algorithm.
        """
        # 'INPUT' is the recommended name for the main input
        # parameter.
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                'INPUT_POLYGON',
                self.tr('Input polygon'),
                types=[QgsProcessing.TypeVectorPolygon],
                defaultValue=None
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        # === Start processAlgorithm =============================================================================================================
        # === Here is where the processing itself takes place. ========

        import pydevd_pycharm
        pydevd_pycharm.settrace('127.0.0.1', port=53100, stdoutToServer=True, stderrToServer=True)
        input_polygon = self.parameterAsVectorLayer(parameters, 'INPUT_POLYGON', context)

        features = input_polygon.getFeatures()
        for feature in features:
            geom = feature.geometry()
            # Iterate through all vertices of the polygon
            polygon = []
            for vertex in geom.vertices():
                polygon.append((vertex.x(), vertex.y()))

            # triangles = self.triangulate_convex_polygon(polygon)
            #
            # # Find the shortest path to traverse all triangles
            # path = self.find_shortest_path(triangles)
            #
            # # Plot the polygon
            # self.plot_polygon(polygon)
            #
            # # Plot the triangles
            # for triangle in triangles:
            #     self.plot_polygon(triangle, color='g')
            #
            # # Plot the path
            # self.plot_path([polygon[0]] + path + [polygon[0]], color='r')
            # plt.axis('equal')
            #
            # plt.show()

        # === End processAlgorithm =============================================================================================================

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        # Must return a new copy of your algorithm.
        return WatchmanRoute()

    def name(self):
        """
        Returns the unique algorithm name.
        """
        return 'watchmanroute'

    def displayName(self):
        """
        Returns the translated algorithm name.
        """
        return self.tr('Watchman Route')

    def group(self):
        """
        Returns the name of the group this algorithm belongs to.
        """
        return self.tr('Ideas')

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs
        to.
        """
        return 'ideasscripts'

    def shortHelpString(self):
        """
        Returns a localised short help string for the algorithm.
        """
        return self.tr('Implement a solution to a Watchman Route problem')
