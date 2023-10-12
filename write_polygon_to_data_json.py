
from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsProcessing,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFileDestination)

import json


class WritePolygonToDataJson(QgsProcessingAlgorithm):
    """
    Algorithm to implement a solution to a Watchman Route problem
    """

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
                defaultValue='polygon'
            )
        )

        self.addParameter(
            QgsProcessingParameterFileDestination(
                'OUTPUT_JSON_FILE',
                self.tr('Output JSON file'),
                'JSON files (*.json)',
                defaultValue='/home/damaso/repos/qgis-scripts/data-json/data_999.json',
                optional=False,
                createByDefault=True
            )
        )

    def processAlgorithm(self, parameters, context, feedback):

        # === Start processAlgorithm =============================================================================================================
        # === Here is where the processing itself takes place. ========

        # import pydevd_pycharm
        # pydevd_pycharm.settrace('127.0.0.1', port=53100, stdoutToServer=True, stderrToServer=True)

        input_polygon = self.parameterAsVectorLayer(parameters, 'INPUT_POLYGON', context)
        output_json_file = self.parameterAsFileOutput(parameters, 'OUTPUT_JSON_FILE', context)

        features = input_polygon.getFeatures()
        for feature in features:
            geom = feature.geometry()
            # Iterate through all vertices of the polygon
            polygon = []
            for vertex in geom.vertices():
                polygon.append((vertex.x(), vertex.y()))

            # Open the file for writing
            with open(output_json_file, "w") as file:
                # Write the data to the file
                json.dump(polygon, file, indent=4)  # The indent parameter is optional, and makes the file more readable

            return {}

        # === End processAlgorithm =============================================================================================================

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        # Must return a new copy of your algorithm.
        return WritePolygonToDataJson()

    def name(self):
        """
        Returns the unique algorithm name.
        """
        return 'WritePolygonToDataJson'

    def displayName(self):
        """
        Returns the translated algorithm name.
        """
        return self.tr('Write Polygon to data.json')

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
        return self.tr('Write a polygon as WKT to a data.json file')
