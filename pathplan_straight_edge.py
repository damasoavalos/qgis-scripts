import math
import codecs

from qgis import processing
from qgis.PyQt.QtCore import QCoreApplication, QVariant
from qgis.PyQt.QtGui import QColor
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
                       QgsProcessingParameterProviderConnection,
                       QgsProcessingLayerPostProcessorInterface,
                       QgsProcessingParameterString,
                       QgsProject,
                       QgsDataSourceUri,
                       edit,
                       QgsProcessingOutputVectorLayer,
                       QgsProcessingContext,
                       QgsProcessingParameterFileDestination,
                       QgsVectorDataProvider)


class Renamer(QgsProcessingLayerPostProcessorInterface):
    def __init__(self, layer_name):
        self.name = layer_name
        super().__init__()

    def postProcessLayer(self, layer, context, feedback):
        layer.setName(self.name)


class PathPlanStraightEdge(QgsProcessingAlgorithm):
    INPUT = 'INPUT'
    THRESHOLD_ANGLE = 'THRESHOLD_ANGLE'
    NUMBERS_OF_LINES = 'NUMBERS_OF_LINES'
    UNIQUE_VALUE_COLUMN = 'UNIQUE_VALUE_COLUMN'
    OUTPUT_STRAIGHT_EDGES = 'OUTPUT_STRAIGHT_EDGES'
    PATH_PLAN_NAME = 'PATH_PLAN_NAME'
    OUTPUT_HTML_FILE = 'OUTPUT_HTML_FILE'

    def __init__(self):
        super().__init__()

    def tr(self, string):
        # Returns a translatable string with the self.tr() function.
        return QCoreApplication.translate('Processing', string)

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterFeatureSource(self.INPUT, self.tr('Polygon'), [QgsProcessing.TypeVectorPolygon], None))
        self.addParameter(QgsProcessingParameterNumber(self.THRESHOLD_ANGLE, self.tr('Threshold angle'), type=QgsProcessingParameterNumber.Integer, minValue=1, maxValue=10, defaultValue=5))
        self.addParameter(QgsProcessingParameterNumber(self.NUMBERS_OF_LINES, self.tr('Number of lines to return'), type=QgsProcessingParameterNumber.Integer, minValue=1, maxValue=10, defaultValue=1))
        self.addParameter(QgsProcessingParameterField(self.UNIQUE_VALUE_COLUMN, self.tr('Column with unique values'), 'boundary_id', self.INPUT, QgsProcessingParameterField.Any, optional=False))
        self.addParameter(QgsProcessingParameterString(self.PATH_PLAN_NAME, self.tr('Path plan name'), multiLine=False))
        self.addOutput(QgsProcessingOutputVectorLayer(self.OUTPUT_STRAIGHT_EDGES, self.tr('Straight edges layer'), QgsProcessing.TypeVectorLine))
        self.addParameter(QgsProcessingParameterFileDestination(self.OUTPUT_HTML_FILE, 'Output HTML file', 'HTML files (*.html)', defaultValue=None, optional=False, createByDefault=True))

    def createHTML(self, _output_html_file, _output_file_data, _boundaryid_layer, _number_match):
        str_html = ''
        str_boundaryid = ''
        str_difference = ''
        with codecs.open(_output_html_file, 'w', encoding='utf-8') as f:
            # html heading
            str_html = '<html>' \
                       '<head>' \
                       '<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />'

            # style
            str_html = str_html + '<style type="text/css">' \
                                  '.shell {margin:10px;}' \
                                  '.tftable {font-size:12px;color:#333333;border-width:1px;border-color:#729ea5;border-collapse:collapse;}' \
                                  '.tftable th {font-size:12px;background-color:#acc8cc;border-width:1px;padding:4px;border-style:solid;border-color:#729ea5;text-align:center;}' \
                                  '.tftable tr {background-color:#d4e3e5;}' \
                                  '.tftable td {font-size:12px;border-width:1px;padding:3px;border-style:solid;border-color:#729ea5;text-align:center;}' \
                                  '.tftable td:hover {background-color:#ffffff;}' \
                                  '</style>' \
                                  '</head>' \
                                  '<body>'
            # body
            str_title1 = '<h3 class="shell">Total boundaries: ' + str(_boundaryid_layer.featureCount()) + '</h3>'
            str_title2 = '<h3 class="shell">Match: ' + str(_number_match) + '</h3>'
            str_title3 = '<h3 class="shell">Do not match: ' + str(_boundaryid_layer.featureCount() - _number_match) + '</h3>'
            str_title4 = '<h3 class="shell">Percent: ' + str(round((_number_match * 100) / _boundaryid_layer.featureCount())) + '% </h3>'
            str_html = str_html + str_title1 + str_title2 + str_title3 + str_title4

            boundaryid_request = QgsFeatureRequest()
            boundaryid_clause_order = QgsFeatureRequest.OrderByClause('match', ascending=False)
            boundaryid_orderby = QgsFeatureRequest.OrderBy([boundaryid_clause_order])
            boundaryid_request.setOrderBy(boundaryid_orderby)
            boundaryid_records = _boundaryid_layer.getFeatures(boundaryid_request)
            for boundaryid_record in boundaryid_records:
                str_boundaryid = '<div class="shell">' \
                                '<table class="tftable" border="1">' \
                                '<tr><th>Boundary id</th></tr>' \
                                '<tr><td>' + str(boundaryid_record['boundary_id']) + '</td></tr></table></div>'
                str_html = str_html + str_boundaryid

                request = QgsFeatureRequest()
                clause_order = QgsFeatureRequest.OrderByClause('difference', ascending=True)
                orderby = QgsFeatureRequest.OrderBy([clause_order])
                request.setOrderBy(orderby)
                request.setFilterExpression("boundary_id = '{0}'".format(boundaryid_record['boundary_id']))
                for record in _output_file_data.getFeatures(request):
                    str_record = '<div class="shell">' \
                                 '<table class="tftable" border="1">' \
                                 '<tr><th>Straight edge bearing</th><th>Optimal bearing</th><th>Difference</th><th>Match</th></tr>' \
                                 '<tr><td>' + str(record['straight_edge_bearing']) + '</td><td>' + str(record['optimal_bearing']) + '</td><td>' + str(record['difference']) + '</td><td>' + record['match'] + '</td></tr>'\
                                 '</table>' \
                                 '</div>'
                    str_html = str_html + str_record

                # str_html = str_html + str_difference

            str_html = str_html + '</body>' \
                                  '</html>'
            f.write(str_html)

    def createVisualOutput(self, _sink_straight_layer, context):
        _sink_straight_layer.renderer().symbol().setColor(QColor.fromRgb(12, 5, 232, 255))
        _sink_straight_layer.renderer().symbol().setWidth(2)
        _sink_straight_layer.triggerRepaint()

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
        field_index_bearing = _layer.fields().indexFromName('bearing')
        with edit(_layer):
            for _feature in _features:
                line_geom = _feature.geometry().asPolyline()
                start_point = line_geom[0]
                end_point = line_geom[-1]
                _azimuth = self.calculateAzimuth(start_point, end_point)
                _layer.changeAttributeValue(_feature.id(), field_index_bearing, _azimuth)

    def getStartEndPoints(self, _feature_line):
        first_vertex = None
        last_vertex = None
        for part in _feature_line.geometry().constGet():
            first_vertex = part[0]
            last_vertex = part[-1]
        return first_vertex, last_vertex

    def deleteColumns(self, _layer):
        with edit(_layer):
            field_to_delete = []
            for field in _layer.fields():
                if field.name() != 'straight_edge_bearing' and field.name() != 'optimal_bearing' and field.name() != 'difference' and field.name() != 'match' and field.name() != 'boundary_id':
                    field_to_delete.append(_layer.fields().indexFromName(field.name()))

            caps = _layer.dataProvider().capabilities()
            if caps & QgsVectorDataProvider.DeleteAttributes:
                res = _layer.dataProvider().deleteAttributes(field_to_delete)
                _layer.updateFields()

    def deleteColumn(self, _layer, _column):
        with edit(_layer):
            column_index = _layer.fields().indexFromName(_column)
            caps = _layer.dataProvider().capabilities()
            if caps & QgsVectorDataProvider.DeleteAttributes:
                res = _layer.dataProvider().deleteAttributes([column_index])
                _layer.updateFields()

    def populateOutputResult(self, _sink_straight_layer, _path_plan_name, _threshold_angle, _feedback):
        if _feedback.isCanceled():
            return {}

        _sql = "select pp.*, " \
               "straight.bearing as straight_edge_bearing, " \
               "round(trim(pp.optimal_bearings, '{ }')) as optimal_bearing, " \
               "0 as difference, " \
               "'false' as match " \
               "from '" + _sink_straight_layer + "' straight inner join '" + _path_plan_name + "' pp on straight.input_id = pp.boundary_id"

        _param = {'INPUT_DATASOURCES': None,
                  'INPUT_QUERY': _sql,
                  'INPUT_UID_FIELD': '',
                  'INPUT_GEOMETRY_FIELD': '',
                  'INPUT_GEOMETRY_TYPE': 6,
                  'INPUT_GEOMETRY_CRS': None,
                  'OUTPUT': 'memory:'}

        _result_layer = processing.run("qgis:executesql", _param)['OUTPUT']

        _records = _result_layer.getFeatures()
        field_index_straight_edge_bearing = _result_layer.fields().indexFromName('straight_edge_bearing')
        field_index_difference = _result_layer.fields().indexFromName('difference')
        field_index_match = _result_layer.fields().indexFromName('match')
        counter = 100. / _result_layer.featureCount()
        with edit(_result_layer):
            for _record in _records:
                diff = int(self.angleDiff(int(_record['straight_edge_bearing']), int(_record['optimal_bearing'])))
                opposite_diff = int(self.angleDiff(int((_record['straight_edge_bearing'] + 180) % 360), int(_record['optimal_bearing'])))
                if diff <= _threshold_angle:
                    _result_layer.changeAttributeValue(_record.id(), field_index_difference, diff)
                    _result_layer.changeAttributeValue(_record.id(), field_index_match, 'true')
                elif opposite_diff <= _threshold_angle:
                    _result_layer.changeAttributeValue(_record.id(), field_index_straight_edge_bearing, int((_record['straight_edge_bearing'] + 180) % 360))
                    _result_layer.changeAttributeValue(_record.id(), field_index_difference, opposite_diff)
                    _result_layer.changeAttributeValue(_record.id(), field_index_match, 'true')
                else:
                    _result_layer.changeAttributeValue(_record.id(), field_index_difference, diff)
                    _result_layer.changeAttributeValue(_record.id(), field_index_match, 'false')
                _feedback.setProgress(_record.id() * counter)
        self.deleteColumn(_result_layer, 'optimal_bearings')

        # distinct boundary_id
        _sql_bondary_id = "select distinct boundary_id, 'false' as match from '" + _path_plan_name + "'"
        _param_bondary_id = {'INPUT_DATASOURCES': None,
                             'INPUT_QUERY': _sql_bondary_id,
                             'INPUT_UID_FIELD': '',
                             'INPUT_GEOMETRY_FIELD': '',
                             'INPUT_GEOMETRY_TYPE': 1,
                             'INPUT_GEOMETRY_CRS': None,
                             'OUTPUT': 'memory:'}
        _boundaryid_layer = processing.run("qgis:executesql", _param_bondary_id)['OUTPUT']

        _boundaryid_records = _boundaryid_layer.getFeatures()
        boundary_field_index_match = _boundaryid_layer.fields().indexFromName('match')
        _number_match = 0
        with edit(_boundaryid_layer):
            for _boundaryid_record in _boundaryid_records:
                request = QgsFeatureRequest()
                clause_order = QgsFeatureRequest.OrderByClause('difference', ascending=True)
                orderby = QgsFeatureRequest.OrderBy([clause_order])
                request.setOrderBy(orderby)
                request.setFilterExpression("boundary_id = '{0}'".format(_boundaryid_record['boundary_id']))
                for record in _result_layer.getFeatures(request):
                    if record['match'] == 'true':
                        _boundaryid_layer.changeAttributeValue(_boundaryid_record.id(), boundary_field_index_match, 'true')
                        _number_match += 1
                        break

        return _result_layer, _boundaryid_layer, _number_match

    def loadPathPlanLayer(self, _path_plan_name, _feedback):
        if _feedback.isCanceled():
            return {}

        uri = QgsDataSourceUri()
        # TODO create a config file to read these parameters from
        uri.setConnection('ldc01-dev-launchpaddb.vergetech.dev',                    # host
                          '5432',                                                   # port
                          'launchpad',                                              # database
                          'launchpad',                                              # username
                          'RnbNuQd9UsdRarxhCpNgytcwoFMDMjA2Jb7ZfA8ERfoYwiKqqZ')     # password
        path_plan_sql_where = "position('{0}' in name) > 0 and ST_NumGeometries(boundary::geometry) = 1".format(_path_plan_name)
        path_plan_sql_select = "(select id, " \
                               "field_id, " \
                               "boundary_id, " \
                               "boundary::geometry, " \
                               "track_width, " \
                               "status, " \
                               "name, " \
                               "area, " \
                               "tracks::geometry, " \
                               "track_distance, " \
                               "number_of_tracks, " \
                               "activity, " \
                               "track_width_original_unit, " \
                               "optimal_bearings::text " \
                               "from public.path_plans)"

        uri.setDataSource('', path_plan_sql_select, 'tracks', path_plan_sql_where, 'id')
        _layer = QgsVectorLayer(uri.uri(True), _path_plan_name, "postgres")
        QgsProject.instance().addMapLayer(_layer)
        return _layer

    def processAlgorithm(self, parameters, context, feedback):

        # import pydevd_pycharm
        # pydevd_pycharm.settrace('127.0.0.1', port=53100, stdoutToServer=True, stderrToServer=True)

        input_layer = self.parameterAsVectorLayer(parameters, self.INPUT, context)
        threshold_angle = self.parameterAsInt(parameters, self.THRESHOLD_ANGLE, context)
        number_of_lines = self.parameterAsInt(parameters, self.NUMBERS_OF_LINES, context)
        unique_value_column = self.parameterAsString(parameters, self.UNIQUE_VALUE_COLUMN, context)
        path_plan_name = self.parameterAsString(parameters, self.PATH_PLAN_NAME, context)
        result = {}

        # let's make sure the layer is in "wgs 84"
        input_layer_crs = input_layer.crs()  # save it to use to create the output with same CRS
        if input_layer_crs.authid() != 'EPSG:4326':
            in_layer = self.ReprojectLayer(input_layer, 'epsg:4326', context, feedback)
            feedback.pushInfo(self.tr("Layer reprojected to 'WGS 84'"))
        else:
            input_layer.selectAll()
            in_layer = processing.run("native:saveselectedfeatures", {'INPUT': input_layer, 'OUTPUT': 'memory:'})['OUTPUT']
            input_layer.removeSelection()

        _uri = 'MultiLineString?crs=epsg:4326&field=bearing:integer&field=rank:integer&field=distance:double&field=input_id:string&index=yes'
        sink_straight_layer = QgsVectorLayer(_uri, 'straight_edges', 'memory')

        # TODO delete the following lines once everything is done
        # records = []
        # for feat in in_layer.getFeatures():
        #     geometries = feat.geometry().asGeometryCollection()
        #     if len(geometries) == 1:
        #         records.append(feat)

        feedback.setProgressText(self.tr('Working with input layer…'))
        records = in_layer.getFeatures()
        counter = 50. / in_layer.featureCount()
        for record in records:

            in_layer.removeSelection()
            in_layer.select(record.id())

            polygon_layer = processing.run("native:saveselectedfeatures", {'INPUT': in_layer, 'OUTPUT': 'memory:'})['OUTPUT']
            polygonstolines_result = processing.run("native:polygonstolines", {'INPUT': polygon_layer, 'OUTPUT': 'memory:'})['OUTPUT']
            explodelines_result = processing.run("native:explodelines", {'INPUT': polygonstolines_result, 'OUTPUT': 'memory:'})['OUTPUT']

            # define and add in_layer_fields 'bearing'
            in_layer_fields = QgsFields()
            in_layer_fields.append(QgsField('bearing', QVariant.Int))
            layer_provider = explodelines_result.dataProvider()
            layer_provider.addAttributes(in_layer_fields)
            explodelines_result.updateFields()

            self.updateAzimuthAttribute(explodelines_result, context, feedback)

            _uri = 'Linestring?crs=epsg:4326&field=bearing:integer&field=rank:integer&field=distance:double&field=input_id:string&index=yes'
            straight_edges_layer = QgsVectorLayer(_uri, 'tempStraightEdgesLayer', 'memory')
            straight_edges_layer_pr = straight_edges_layer.dataProvider()

            features = explodelines_result.getFeatures()
            feature_1 = None
            feature_2 = None
            line_azimuth = None
            linestring = []
            _rank = -1
            for i, feature in enumerate(features):

                if i == 0:
                    feature_1 = feature
                    continue

                feature_2 = feature

                azimuth_1 = feature_1["bearing"]
                azimuth_2 = feature_2["bearing"]

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
                    out_feat.setAttributes([_azimuth, _rank, _distance, _input_id])
                    straight_edges_layer_pr.addFeature(out_feat)
                    linestring.clear()
                feature_1 = feature_2

            request = QgsFeatureRequest()
            clause = QgsFeatureRequest.OrderByClause('distance', ascending=False)
            orderby = QgsFeatureRequest.OrderBy([clause])
            request.setOrderBy(orderby)
            request.setLimit(number_of_lines)

            _features = straight_edges_layer.getFeatures(request)
            field_index_rank = straight_edges_layer.fields().indexFromName('rank')
            with edit(straight_edges_layer):
                for i, _feature in enumerate(_features):
                    straight_edges_layer.changeAttributeValue(_feature.id(), field_index_rank, i + 1)

            with edit(sink_straight_layer):
                sink_straight_layer.addFeatures(straight_edges_layer.getFeatures(request))

            feedback.setProgress(record.id() * counter)

        feedback.setProgressText(self.tr('Working with input layer…  Done'))

        feedback.setProgressText(self.tr('Creating Plan Path layer…'))
        plan_layer = self.loadPathPlanLayer(path_plan_name, feedback)
        QgsProject.instance().addMapLayer(sink_straight_layer)
        feedback.setProgressText(self.tr('Plan Path layer…  Done'))

        feedback.setProgressText(self.tr('Creating table result…'))
        result_layer, boundaryid_layer, number_match = self.populateOutputResult('straight_edges', path_plan_name, threshold_angle, feedback)
        QgsProject.instance().removeMapLayer(QgsProject.instance().mapLayersByName(path_plan_name)[0].id())
        # QgsProject.instance().addMapLayer(result_layer)
        feedback.setProgressText(self.tr('Table result…  Done'))

        feedback.pushInfo(self.tr('Match {0}'.format(str(number_match))))
        feedback.pushInfo(self.tr("Don't match {0}".format(str(result_layer.featureCount() - number_match))))
        feedback.pushInfo(self.tr("Total records {0}".format(str(result_layer.featureCount()))))
        feedback.pushInfo(self.tr("Percent {0}%".format(str(round((number_match*100)/result_layer.featureCount())))))

        output_html_file = self.parameterAsFileOutput(parameters, self.OUTPUT_HTML_FILE, context)
        if output_html_file:
            self.createHTML(output_html_file, result_layer, boundaryid_layer, number_match)
        result[self.OUTPUT_HTML_FILE] = output_html_file

        self.createVisualOutput(sink_straight_layer, context)

        # adding layer to load on completion
        context.temporaryLayerStore().addMapLayer(result_layer)
        context.addLayerToLoadOnCompletion(result_layer.id(), QgsProcessingContext.LayerDetails(QgsProcessingContext.LayerDetails('path_plan_and_results',
                                                                                                                                  context.project(),
                                                                                                                                  self.OUTPUT_STRAIGHT_EDGES)))

        return result

    def name(self):
        return 'PathPlanStraightEdge'

    def displayName(self):
        return 'Path plan vs Straight edge'

    def group(self):
        return 'First Pass Tools'

    def groupId(self):
        return 'firstpasstools'

    def createInstance(self):
        return PathPlanStraightEdge()

    def flags(self):
        return super().flags() | QgsProcessingAlgorithm.FlagNoThreading
