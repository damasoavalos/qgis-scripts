import codecs
from operator import itemgetter

from qgis.core import (QgsProcessing,
                       QgsProcessingAlgorithm,
                       QgsDistanceArea,
                       QgsUnitTypes,
                       QgsProcessingParameterFileDestination,
                       QgsProcessingParameterFeatureSource,
                       QgsFeatureRequest,
                       QgsVectorLayer,
                       QgsPalLayerSettings,
                       QgsTextFormat,
                       QgsTextBufferSettings,
                       QgsVectorLayerSimpleLabeling,
                       QgsField,
                       QgsFeature,
                       QgsProject)

from qgis.PyQt.QtGui import QColor, QFont
from qgis.PyQt.QtCore import QCoreApplication, QVariant
from qgis import processing


class IntersectionOverUnion(QgsProcessingAlgorithm):
    INPUT_VECTOR = 'INPUT_VECTOR'
    INPUT_OVERLAY = 'INPUT_OVERLAY'
    OUTPUT_HTML_FILE = 'OUTPUT_HTML_FILE'

    def __init__(self):
        super().__init__()

    def tr(self, string):
        # Returns a translatable string with the self.tr() function.
        return QCoreApplication.translate('Processing', string)

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterFeatureSource(self.INPUT_VECTOR, 'Input vector', types=[QgsProcessing.TypeVectorPolygon], defaultValue=None))
        self.addParameter(QgsProcessingParameterFeatureSource(self.INPUT_OVERLAY, 'Overlay layer (Imagery)', types=[QgsProcessing.TypeVectorPolygon], defaultValue=None))
        self.addParameter(QgsProcessingParameterFileDestination(self.OUTPUT_HTML_FILE, 'Output HTML file', 'HTML files (*.html)', defaultValue=None, optional=False, createByDefault=True))

    def createHTML(self, _output_html_file, _output_file_data, _input_vector_name, _input_overlay_name):
        str_html = ''
        str_featureid = ''
        str_iou = ''
        str_difference = ''
        with codecs.open(_output_html_file, 'w', encoding='utf-8') as f:
            # html heading
            str_html = '<html>' \
                       '<head>' \
                       '<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />'

            # style
            str_html = str_html + '<style type="text/css">' \
                                  '.shell {margin:5px;display:inline-block;}' \
                                  '.tftable {font-size:12px;color:#333333;border-width:1px;border-color:#729ea5;border-collapse:collapse;}' \
                                  '.tftable th {font-size:12px;background-color:#acc8cc;border-width:1px;padding:4px;border-style:solid;border-color:#729ea5;text-align:center;}' \
                                  '.tftable tr {background-color:#d4e3e5;}' \
                                  '.tftable td {font-size:12px;border-width:1px;padding:3px;border-style:solid;border-color:#729ea5;text-align:center;}' \
                                  '.tftable td:hover {background-color:#ffffff;}' \
                                  '</style>' \
                                  '</head>' \
                                  '<body>'
            # body
            str_title = '<h3 class="shell">' + _input_vector_name + ' / ' + _input_overlay_name + '</h3><br><br>'
            str_html = str_html + str_title

            for idx, record in enumerate(_output_file_data):
                str_featureid = '<div class="shell">' \
                                '<table class="tftable" border="1">' \
                                '<tr><th>Feature id</th></tr>' \
                                '<tr><td>' + str(record['Record Id']) + '</td></tr>' \
                                '</table>' \
                                '</div>'
                str_html = str_html + str_featureid

                str_iou = '<div class="shell">' \
                          '<table class="tftable" border="1">' \
                          '<tr><th>Intersection over Union</th><th>Intersection Area</th><th>Union Area</th></tr>' \
                          '<tr><td>' + str(record['IntersectionOverUnion']) + '</td><td>' + record['Intersection Area'] + '</td><td>' + record['Union Area'] + '</td></tr>' \
                          '</table>' \
                          '</div>'
                str_html = str_html + str_iou

                str_difference = '<div class="shell">' \
                                 '<table class="tftable" border="1">' \
                                 '<tr><th>Difference Area</th><th>Difference Perimeter</th></tr>' \
                                 '<tr><td>' + record['Difference Area'] + '</td><td>' + record['Difference Perimeter'] + '</td></tr>' \
                                 '</table>' \
                                 '</div><br>'

                str_html = str_html + str_difference

            str_html = str_html + '</body>' \
                                  '</html>'
            f.write(str_html)

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

    def createVisualOutput(self, _input_vector, _input_overlay, _output_vector_layer, context):
        # label
        layer_settings = QgsPalLayerSettings()
        text_format = QgsTextFormat()
        text_format.setFont(QFont("Arial", 12))
        text_format.setSize(12)
        buffer_settings = QgsTextBufferSettings()
        buffer_settings.setEnabled(True)
        buffer_settings.setSize(1)
        buffer_settings.setColor(QColor("white"))
        text_format.setBuffer(buffer_settings)
        layer_settings.setFormat(text_format)
        layer_settings.fieldName = "f_id"
        layer_settings.placement = 1
        layer_settings.enabled = True
        layer_settings = QgsVectorLayerSimpleLabeling(layer_settings)
        _output_vector_layer.setLabelsEnabled(True)
        _output_vector_layer.setLabeling(layer_settings)
        _output_vector_layer.triggerRepaint()

        # selection
        _input_vector.removeSelection()
        _input_overlay.removeSelection()

        QgsProject.instance().layerTreeRoot().findLayer(_input_vector.id()).setItemVisibilityChecked(False)
        QgsProject.instance().layerTreeRoot().findLayer(_input_overlay.id()).setItemVisibilityChecked(False)

    def calculateGeometryAttributes(self, _layer):
        calculator = QgsDistanceArea()
        calculator.setEllipsoid('WGS84')

        geometry_attributes = {'area': 0,
                               'area_formatted': '',
                               'perimeter': 0,
                               'perimeter_formatted': ''
                               }
        _features = _layer.getFeatures()
        for feature in _features:
            geom = feature.geometry()
            geometry_attributes['area'] = geometry_attributes['area'] + calculator.measureArea(geom)
            geometry_attributes['perimeter'] = geometry_attributes['perimeter'] + calculator.measurePerimeter(geom)

        geometry_attributes['area_formatted'] = calculator.formatArea(geometry_attributes['area'], 1, QgsUnitTypes.AreaUnit.AreaSquareMeters)
        geometry_attributes['perimeter_formatted'] = calculator.formatDistance(geometry_attributes['perimeter'], 1, QgsUnitTypes.DistanceUnit.DistanceMeters)
        self.delete(calculator)
        return geometry_attributes

    def calculateIOU(self, _input_vector, _input_overlay, _output_vector_layer, _output_iou_layer, _id, context, feedback):
        output_record = []
        record_data = {}

        _features = _input_overlay.getFeatures()
        for _feature in _features:

            if feedback.isCanceled():
                _input_vector.removeSelection()
                _input_overlay.removeSelection()
                return {}

            _input_overlay.select(_feature.id())
            _selected_input_overlay = processing.run("native:saveselectedfeatures", {'INPUT': _input_overlay, 'OUTPUT': 'memory:'})['OUTPUT']

            input_params = {'INPUT': _input_vector,
                            'OVERLAY': _selected_input_overlay,
                            'OUTPUT': 'memory:'}

            intersection_result = processing.run("native:intersection",
                                                 input_params,
                                                 # feedback=feedback,
                                                 context=context)['OUTPUT']
            ga_intersection_result = intersection_result.clone()
            intersection_geometry_attribute = self.calculateGeometryAttributes(ga_intersection_result)

            union_result = processing.run("native:union",
                                          input_params,
                                          # feedback=feedback,
                                          context=context)['OUTPUT']
            dissolve_params = {'INPUT': union_result,
                               'OUTPUT': 'memory:'}
            dissolve_result = processing.run("native:dissolve",
                                             dissolve_params,
                                             # feedback=feedback,
                                             context=context)['OUTPUT']
            ga_dissolve_result = dissolve_result.clone()
            union_geometry_attribute = self.calculateGeometryAttributes(ga_dissolve_result)

            difference_result = processing.run("native:symmetricaldifference",
                                               input_params,
                                               # feedback=feedback,
                                               context=context)['OUTPUT']
            ga_difference_result = difference_result.clone()
            difference_geometry_attribute = self.calculateGeometryAttributes(ga_difference_result)

            input_vector_geometry_attribute = self.calculateGeometryAttributes(_input_vector.clone())
            input_overlay_geometry_attribute = self.calculateGeometryAttributes(_selected_input_overlay.clone())

            iou_formatted = round((intersection_geometry_attribute['area'] / union_geometry_attribute['area']), 2)

            record_data = {'Vector Layer Area': input_vector_geometry_attribute['area_formatted'],
                           'Overlay Layer Area': input_overlay_geometry_attribute['area_formatted'],
                           'Difference Area': difference_geometry_attribute['area_formatted'],

                           'VectorLayerArea': input_vector_geometry_attribute['area'],
                           'OverlayLayerArea': input_overlay_geometry_attribute['area'],
                           'DifferenceArea': difference_geometry_attribute['area'],

                           'Vector Layer Perimeter': input_vector_geometry_attribute['perimeter_formatted'],
                           'Overlay Layer Perimeter': input_overlay_geometry_attribute['perimeter_formatted'],
                           'Difference Perimeter': difference_geometry_attribute['perimeter_formatted'],

                           'VectorLayerPerimeter': input_vector_geometry_attribute['perimeter'],
                           'OverlayLayerPerimeter': input_overlay_geometry_attribute['perimeter'],
                           'DifferencePerimeter': difference_geometry_attribute['perimeter'],

                           'Intersection Area': intersection_geometry_attribute['area_formatted'],
                           'Union Area': union_geometry_attribute['area_formatted'],

                           'IntersectionArea': intersection_geometry_attribute['area'],
                           'UnionArea': union_geometry_attribute['area'],

                           'IntersectionOverUnion': iou_formatted,
                           'Record Id': _id
                           }

            self.addFeatureOutputOverlay(_output_iou_layer, _feature, record_data)

            output_record.append(record_data)
            self.delete(_selected_input_overlay)
            _input_overlay.removeSelection()

        for _input_vector_feature in _input_vector.getFeatures():
            self.addFeatureOutputVector(_output_vector_layer, _input_vector_feature, record_data)

        return output_record

    def createOutputVector(self):
        # create layer
        _vl = QgsVectorLayer('Polygon', 'output_vector', 'memory')
        _pr = _vl.dataProvider()
        # add fields
        _pr.addAttributes([QgsField('f_id', QVariant.Int),
                          QgsField('area', QVariant.Double),
                          QgsField('perimeter', QVariant.Double)])
        _vl.updateFields()  # tell the vector layer to fetch changes from the provider
        return _vl

    def createOutputOverlay(self):
        # create layer
        _vl = QgsVectorLayer('Polygon', 'output_overlay', 'memory')
        _pr = _vl.dataProvider()
        # add fields
        _pr.addAttributes([QgsField('vector_layer_f_id', QVariant.Int),
                           QgsField('area', QVariant.Double),
                           QgsField('perimeter', QVariant.Double),
                           QgsField('iou', QVariant.Double),
                           QgsField('intersection_area', QVariant.Double),
                           QgsField('union_area', QVariant.Double)]
                          )
        _vl.updateFields()  # tell the vector layer to fetch changes from the provider
        return _vl

    def addFeatureOutputVector(self, _layer, _feature, _record_data):
        _pr = _layer.dataProvider()
        # add a feature
        _feat = QgsFeature(_layer.fields())
        _feat.setGeometry(_feature.geometry())
        _feat.setAttribute('f_id', _record_data['Record Id'])
        _feat.setAttribute('area', _record_data['VectorLayerArea'])
        _feat.setAttribute('perimeter', _record_data['VectorLayerPerimeter'])
        _pr.addFeature(_feat)
        # update layer's extent when new features have been added
        # because change of extent in provider is not propagated to the layer
        _layer.updateExtents()

    def addFeatureOutputOverlay(self, _layer, _feature, _record_data):
        _pr = _layer.dataProvider()
        # add a feature
        _feat = QgsFeature(_layer.fields())
        _feat.setGeometry(_feature.geometry())
        _feat.setAttribute('vector_layer_f_id', _record_data['Record Id'])
        _feat.setAttribute('area', _record_data['OverlayLayerArea'])
        _feat.setAttribute('perimeter', _record_data['OverlayLayerPerimeter'])
        _feat.setAttribute('iou', _record_data['IntersectionOverUnion'])
        _feat.setAttribute('intersection_area', _record_data['IntersectionArea'])
        _feat.setAttribute('union_area', _record_data['UnionArea'])
        _pr.addFeature(_feat)
        # update layer's extent when new features have been added
        # because change of extent in provider is not propagated to the layer
        _layer.updateExtents()

    def processAlgorithm(self, parameters, context, feedback):
        # import pydevd_pycharm
        # pydevd_pycharm.settrace('127.0.0.1', port=53100, stdoutToServer=True, stderrToServer=True)
        input_vector = self.parameterAsVectorLayer(parameters, self.INPUT_VECTOR, context)
        input_overlay = self.parameterAsVectorLayer(parameters, self.INPUT_OVERLAY, context)

        result = {}
        output_records = []

        output_vector_layer = self.createOutputVector()
        output_iou_layer = self.createOutputOverlay()

        input_vector.removeSelection()
        input_overlay.removeSelection()

        # set order by field
        request = QgsFeatureRequest()
        clause = QgsFeatureRequest.OrderByClause('fid', ascending=True)
        orderby = QgsFeatureRequest.OrderBy([clause])
        request.setOrderBy(orderby)
        features = input_vector.getFeatures(request)
        count = input_vector.featureCount()
        counter = 100 / count
        feedback.setProgressText('Computing "Intersection over Union"...')
        for feature in features:

            if feedback.isCanceled():
                input_vector.removeSelection()
                input_overlay.removeSelection()
                return {}

            input_vector.removeSelection()
            input_vector.select(feature.id())

            selected_input_vector = processing.run("native:saveselectedfeatures", {'INPUT': input_vector, 'OUTPUT': 'memory:'})['OUTPUT']

            selection_params = {'INPUT': input_overlay,
                                'PREDICATE': [0, 5],
                                'INTERSECT': selected_input_vector,
                                'METHOD': 0}

            processing.run("native:selectbylocation",
                           selection_params,
                           # feedback=feedback,
                           context=context)

            if input_overlay.selectedFeatureCount() != 0:
                selected_input_overlay = processing.run("native:saveselectedfeatures", {'INPUT': input_overlay, 'OUTPUT': 'memory:'})['OUTPUT']
                output_record = self.calculateIOU(selected_input_vector, selected_input_overlay, output_vector_layer, output_iou_layer, feature.id(), context, feedback)
                output_records.extend(output_record)
                self.delete(selected_input_overlay)

            self.delete(selected_input_vector)
            feedback.setProgress(feature.id() * counter)

        # output
        output_html_file = self.parameterAsFileOutput(parameters, self.OUTPUT_HTML_FILE, context)
        output_records_sorted = sorted(output_records, key=itemgetter('IntersectionOverUnion'), reverse=True)
        if output_html_file:
            # input_vector
            # input_overlay
            self.createHTML(output_html_file, output_records_sorted, input_vector.name(), input_overlay.name())
        result[self.OUTPUT_HTML_FILE] = output_html_file
        QgsProject.instance().addMapLayer(output_iou_layer)
        QgsProject.instance().addMapLayer(output_vector_layer)
        self.createVisualOutput(input_vector, input_overlay, output_vector_layer, context)

        feedback.pushInfo('Done')
        return result

    def name(self):
        return "IntersectionOverUnion"

    def displayName(self):
        return "Intersection over Union"

    def createInstance(self):
        return type(self)()

    def group(self):
        return 'First Pass Tools'

    def groupId(self):
        return 'firstpasstools'

    def shortHelpString(self):
        return self.tr("IOU(Intersection over Union)\n\n"
                       "is a term used to describe the extent of overlap of two boxes.\n"
                       "The greater the region of overlap, the greater the IOU.\n"
                       )

    def flags(self):
        return super().flags() | QgsProcessingAlgorithm.FlagNoThreading
