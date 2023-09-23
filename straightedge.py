import math

from qgis import processing
from qgis.PyQt.QtCore import QCoreApplication, QVariant
from qgis.core import (QgsProcessing,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFeatureSink,
                       QgsVectorLayer,
                       QgsFeature,
                       QgsGeometry,
                       QgsFeatureSink,
                       QgsWkbTypes,
                       QgsFields,
                       QgsField,
                       QgsDistanceArea,
                       QgsFeatureRequest,
                       QgsProcessingParameterField,
                       edit)


class StraightEdge(QgsProcessingAlgorithm):
    INPUT = 'INPUT'
    THRESHOLD_ANGLE = 'THRESHOLD_ANGLE'
    NUMBERS_OF_LINES = 'NUMBERS_OF_LINES'
    UNIQUE_VALUE_COLUMN = 'UNIQUE_VALUE_COLUMN'
    OUTPUT = 'OUTPUT'

    def __init__(self):
        super().__init__()

    def tr(self, string):
        # Returns a translatable string with the self.tr() function.
        return QCoreApplication.translate('Processing', string)

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterFeatureSource(self.INPUT, self.tr('Polygon'), [QgsProcessing.TypeVectorPolygon], None))
        self.addParameter(QgsProcessingParameterNumber(self.THRESHOLD_ANGLE, self.tr('Threshold angle'), type=QgsProcessingParameterNumber.Integer, minValue=1, maxValue=10, defaultValue=5))
        self.addParameter(QgsProcessingParameterNumber(self.NUMBERS_OF_LINES, self.tr('Number of lines to return'), type=QgsProcessingParameterNumber.Integer, minValue=1, maxValue=10, defaultValue=3))
        self.addParameter(QgsProcessingParameterField(self.UNIQUE_VALUE_COLUMN, self.tr('Column with unique values'), 'id', self.INPUT, QgsProcessingParameterField.Any, optional=False))
        self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT, self.tr('Straight edges'), type=QgsProcessing.TypeVectorLine))

    def delete(self, var):
        var_exists = False
        try:
            var
        except NameError:
            var_exists = False
        else:
            var_exists = True
        if var_exists:
            del var

    def angleDiff(self, angle1, angle2):
        return 180 - abs(abs(angle1 - angle2) - 180)

    def ReprojectLayer(self, _in_layer, to_epsg, _context, _feedback):
        if _feedback.isCanceled():
            return {}

        _parameter = {'INPUT': _in_layer,
                      'TARGET_CRS': to_epsg,
                      'OUTPUT': 'memory:temp'}
        _reprojectedLayer = processing.run('native:reprojectlayer', _parameter, context=_context)['OUTPUT']
        return _reprojectedLayer

    def calculateDistance(self, _feature):
        calculator = QgsDistanceArea()
        calculator.setEllipsoid('WGS84')

        geom = _feature.geometry()
        _distance = calculator.measureLength(geom)
        self.delete(calculator)
        return _distance

    def calculateAzimuth(self, v1, v2):
        _azimuth = None
        if v1.isEmpty() is False and v2.isEmpty() is False:
            _azimuth = math.trunc(v1.azimuth(v2))
            if _azimuth < 0:
                _azimuth += 360
        else:
            _azimuth = 0
        return _azimuth

    def updateAzimuthAttribute(self, _layer, _context, _feedback):
        if _feedback.isCanceled():
            return {}

        _features = _layer.getFeatures()
        field_index_azimuth = _layer.fields().indexFromName('azimuth')
        with edit(_layer):
            for _feature in _features:
                line_geom = _feature.geometry().asPolyline()
                start_point = line_geom[0]
                end_point = line_geom[-1]
                _azimuth = self.calculateAzimuth(start_point, end_point)
                _layer.changeAttributeValue(_feature.id(), field_index_azimuth, _azimuth)

    def getStartEndPoints(self, _feature_line):
        first_vertex = None
        last_vertex = None
        for part in _feature_line.geometry().constGet():
            first_vertex = part[0]
            last_vertex = part[-1]
        return first_vertex, last_vertex

    def processAlgorithm(self, parameters, context, feedback):

        # import pydevd_pycharm
        # pydevd_pycharm.settrace('127.0.0.1', port=53100, stdoutToServer=True, stderrToServer=True)

        input_layer = self.parameterAsVectorLayer(parameters, self.INPUT, context)
        threshold_angle = self.parameterAsInt(parameters, self.THRESHOLD_ANGLE, context)
        number_of_lines = self.parameterAsInt(parameters, self.NUMBERS_OF_LINES, context)
        unique_value_column = self.parameterAsString(parameters, self.UNIQUE_VALUE_COLUMN, context)

        # let's make sure the layer is in "wgs 84"
        input_layer_crs = input_layer.crs()  # save it to use to create the output with same CRS
        if input_layer_crs.authid() != 'EPSG:4326':
            in_layer = self.ReprojectLayer(input_layer, 'epsg:4326', context, feedback)
            feedback.pushInfo(self.tr("Layer reprojected to 'WGS 84'"))
        else:
            input_layer.selectAll()
            in_layer = processing.run("native:saveselectedfeatures", {'INPUT': input_layer, 'OUTPUT': 'memory:'})['OUTPUT']
            input_layer.removeSelection()

        parameters['OUTPUT'].destinationName = 'Straight edges-{}'.format(input_layer.name())

        sink_fields = QgsFields()
        sink_fields.append(QgsField('azimuth', QVariant.Int))
        sink_fields.append(QgsField('distance', QVariant.Double))
        sink_fields.append(QgsField('input_id', QVariant.String))
        (sink, dest_id) = self.parameterAsSink(parameters, self.OUTPUT, context, sink_fields, QgsWkbTypes.LineString, in_layer.crs())

        records = in_layer.getFeatures()
        for record in records:

            in_layer.removeSelection()
            in_layer.select(record.id())

            polygon_layer = processing.run("native:saveselectedfeatures", {'INPUT': in_layer, 'OUTPUT': 'memory:'})['OUTPUT']

            polygonstolines_result = processing.run("native:polygonstolines", {'INPUT': polygon_layer, 'OUTPUT': 'memory:'})['OUTPUT']

            explodelines_result = processing.run("native:explodelines", {'INPUT': polygonstolines_result, 'OUTPUT': 'memory:'})['OUTPUT']

            # define and add in_layer_fields 'azimuth' and 'distance'
            in_layer_fields = QgsFields()
            in_layer_fields.append(QgsField('azimuth', QVariant.Int))
            layer_provider = explodelines_result.dataProvider()
            layer_provider.addAttributes(in_layer_fields)
            explodelines_result.updateFields()

            self.updateAzimuthAttribute(explodelines_result, context, feedback)

            _uri = 'Linestring?crs=epsg:4326&field=azimuth:integer&field=distance:double&field=input_id:string&index=yes'
            sink_layer = QgsVectorLayer(_uri, 'tempSinkLayer', 'memory')
            sink_layer_pr = sink_layer.dataProvider()

            features = explodelines_result.getFeatures()
            feature_1 = None
            feature_2 = None
            line_azimuth = None
            linestring = []
            for i, feature in enumerate(features):

                if i == 0:
                    feature_1 = feature
                    continue

                feature_2 = feature

                azimuth_1 = feature_1["azimuth"]
                azimuth_2 = feature_2["azimuth"]

                if not linestring:
                    linestring.append(feature_1.geometry())
                    line_azimuth = azimuth_1

                azimuth_diff = self.angleDiff(azimuth_1, azimuth_2)
                if azimuth_diff <= threshold_angle:
                    linestring.append(feature_2.geometry())
                else:
                    out_feat = QgsFeature()
                    out_feat.setGeometry(QgsGeometry().collectGeometry(linestring))
                    start_point = self.getStartEndPoints(out_feat)[0]
                    end_point = self.getStartEndPoints(out_feat)[1]
                    _azimuth = self.calculateAzimuth(start_point, end_point)
                    _distance = self.calculateDistance(out_feat)
                    _input_id = str(record[unique_value_column])
                    out_feat.setAttributes([_azimuth, _distance, _input_id])
                    sink_layer_pr.addFeature(out_feat)
                    linestring.clear()
                feature_1 = feature_2

            request = QgsFeatureRequest()
            clause = QgsFeatureRequest.OrderByClause('distance', ascending=False)
            orderby = QgsFeatureRequest.OrderBy([clause])
            request.setOrderBy(orderby)
            request.setLimit(number_of_lines)
            sink_layer_features = sink_layer.getFeatures(request)

            sink.addFeatures(sink_layer_features, QgsFeatureSink.FastInsert)

        return {self.OUTPUT: dest_id}

    def name(self):
        return 'StraightEdge'

    def displayName(self):
        return self.tr('Straight Edge')

    def group(self):
        return self.tr('First Pass Tools')

    def groupId(self):
        return 'firstpasstools'

    def createInstance(self):
        return StraightEdge()

    def flags(self):
        return super().flags() | QgsProcessingAlgorithm.FlagNoThreading
