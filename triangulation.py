import os
from math import floor
from pyproj import CRS
import codecs
from measurement.measures import Distance

from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtCore import QCoreApplication

from qgis.core import (QgsApplication,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterExtent,
                       QgsCoordinateReferenceSystem,
                       QgsCoordinateTransform,
                       QgsProcessingParameterMapLayer,
                       QgsProcessingParameterVectorLayer,
                       QgsProcessing,
                       QgsWkbTypes,
                       QgsFeatureSink,
                       QgsProcessingParameterFeatureSink,
                       QgsStatisticalSummary,
                       QgsFeatureRequest,
                       QgsProcessingFeatureSource,
                       QgsProcessingParameterFileDestination,
                       QgsProcessingOutputHtml)
import processing


class Triangulation(QgsProcessingAlgorithm):

    INPUT = 'INPUT'    
    OUTPUT = 'OUTPUT' 
    EXTENT = 'EXTENT'
    MEDIAN_WIDTH = 'MEDIAN WIDTH'
    OUTPUT_HTML_FILE = 'OUTPUT_HTML_FILE'

    def tr(self, string):
        # Returns a translatable string with the self.tr() function.        
        return QCoreApplication.translate('Processing', string)

    def __init__(self):
        super().__init__()
        self.stringCrs = 'epsg:4326'
        
    def initAlgorithm(self, config=None): 
        self.addParameter(QgsProcessingParameterVectorLayer(self.INPUT, 'Input layer', types=[QgsProcessing.TypeVectorPoint]))       
        self.addParameter(QgsProcessingParameterExtent(self.EXTENT, 'Input extent to calculate UTM zone'))
        # self.addParameter(QgsProcessingParameterNumber(self.MULTIPLIER, 'Multiplier to filter minimum triangulation', type=QgsProcessingParameterNumber.Integer, defaultValue=3,  minValue=1))
        self.addParameter(QgsProcessingParameterFileDestination(self.OUTPUT_HTML_FILE, 'Statistics (save this file for future reference)', 'HTML files (*.html)', defaultValue=None, optional=False, createByDefault=True))
        self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT, 'Output Triangulation', type=QgsProcessing.TypeVectorPolygon))       
     
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

    def reproject_to_utm(self, _in_layer, _utm_zone, _context, _feedback):
        if _feedback.isCanceled():
            return {}

        # we are going to hardcode "'WGS 84 / UTM zone" this part of the srs, for now.
        _stringUtmCrs = CRS.from_user_input('WGS 84 / UTM zone {}'.format(_utm_zone)).to_string()
        _parameter = {'INPUT': _in_layer, 'TARGET_CRS': _stringUtmCrs, 'OUTPUT': 'memory:temp'}
        _utmLayer = processing.run('native:reprojectlayer', _parameter, context=_context, feedback=_feedback)['OUTPUT'] 
        return _utmLayer

    def get_stats(self, _layer, _field_name, _um):
        
        field = _layer.fields().at(_layer.fields().lookupField(_field_name))
        request = QgsFeatureRequest().setFlags(QgsFeatureRequest.NoGeometry).setSubsetOfAttributes([_field_name], _layer.fields())       
        features = _layer.getFeatures(request)        

        stat = QgsStatisticalSummary()
        for ft in features:    
            stat.addVariant(ft[field.name()])    
        stat.finalize()
        if _um == 'ft':
            median_ft = round(stat.median(), 4)            
            min_ft = round(stat.min(), 4)
            max_ft = round(stat.max(), 4)
            minority_ft = round(stat.minority(), 4)
            majority_ft = round(stat.majority(), 4)

            median_m = round(Distance(ft=stat.median()).m, 4)
            min_m = round(Distance(ft=stat.min()).m, 4)
            max_m = round(Distance(ft=stat.max()).m, 4)
            minority_m = round(Distance(ft=stat.minority()).m, 4)
            majority_m = round(Distance(ft=stat.majority()).m, 4)

        elif _um == 'm':
            median_ft = round(Distance(m=stat.median()).ft, 4)
            min_ft = round(Distance(m=stat.min()).ft, 4)
            max_ft = round(Distance(m=stat.max()).ft, 4)
            minority_ft = round(Distance(m=stat.minority()).ft, 4)
            majority_ft = round(Distance(m=stat.majority()).ft, 4)

            median_m = round(stat.median(), 4)            
            min_m = round(stat.min(), 4)
            max_m = round(stat.max(), 4)
            minority_m = round(stat.minority(), 4)
            majority_m = round(stat.majority(), 4)

        # we are assuming that the value is in feet so, we need to convert it to meters. UTM unit is metered
        data = []        
        data.append("Analyzed field: '{}'".format(_field_name.capitalize()))        
        data.append("Median: {0} {1} | {2} {3}".format(median_ft, "ft", median_m, "m"))        
        data.append("NULL (missing) values: {}".format(stat.countMissing()))
        data.append("Minimum value: {0} {1} | {2} {3}".format(min_ft, "ft", min_m, "m"))       
        data.append("Maximum value: {0} {1} | {2} {3}".format(max_ft, "ft", max_m, "m"))        
        data.append("Minority (rarest occurring value): {0} {1} | {2} {3}".format(minority_ft, "ft", minority_m, "m"))      
        data.append("Majority (most frequently occurring value): {0} {1} | {2} {3}".format(majority_ft, "ft", majority_m, "m"))
        # data.append("{}".format("-"*50))
               
        return data

    def create_html(self, output_file, alg_data):
        with codecs.open(output_file, 'w', encoding='utf-8') as f:
            f.write('<html><head>\n')
            f.write('<meta http-equiv="Content-Type" content="text/html; charset=utf-8" /></head><body>\n')
            for s in alg_data:
                if 'Analyzed field:' in s:                
                    f.write('<span style="font-weight:bold">' + str(s) + '</span><br>\n')
                else:
                    f.write('<span>' + str(s) + '</span><br>\n')
                    if 'Majority' in s:
                        f.write('<hr>\n')
                        f.write('<br>\n')
            f.write('</body></html>\n')

    def processAlgorithm(self, parameters, context, feedback):     
        rect = self.parameterAsExtent(parameters, self.EXTENT, context)
        in_layer = self.parameterAsLayer(parameters, self.INPUT, context)
        _stats = []
        results = {}
        # multiplier = self.parameterAsInt(parameters, self.MULTIPLIER, context)

        # -Find UTM zone- 
        utm_zone = self.find_utm_zone(rect, feedback)
        feedback.pushInfo('UTM Zone: {0}'.format(utm_zone))
        
        # -Reproject to UTM- 
        utm_layer = self.reproject_to_utm(in_layer, utm_zone, context, feedback)
        feedback.pushInfo("Layer reprojected to 'UTM Zone: {0}'".format(utm_zone))
                
        _stats.extend(self.get_stats(utm_layer, 'Width', 'ft'))

        # -Delaunay triangulation-
        feedback.setProgressText(self.tr('Creating Delaunay triangles…'))
        parameter = {'INPUT': utm_layer, 'OUTPUT': 'memory:triangulationTemp'}
        triangulation_layer = processing.run('qgis:delaunaytriangulation', parameter, context=context, feedback=feedback)['OUTPUT']

        # -Add geometry attributes (area, perimeter) to triangulationLayer-
        feedback.setProgressText(self.tr('Creating geometry attributes area and perimeter…'))
        parameter = {'INPUT': triangulation_layer, 'CALC_METHOD': 0, 'OUTPUT': 'memory:triangulationAttrTemp'}
        triangulation_attr_layer = processing.run('qgis:exportaddgeometrycolumns', parameter, context=context, feedback=feedback)['OUTPUT']

        _stats.extend(self.get_stats(triangulation_attr_layer, 'area', 'm'))
        _stats.extend(self.get_stats(triangulation_attr_layer, 'perimeter', 'm'))
        for item in _stats:
            feedback.pushInfo(item) 

        # self.addParameter(QgsProcessingParameterFileDestination(self.OUTPUT_HTML_FILE, 'Statistics', 'HTML files (*.html)', None, True))
        # parameters['OUTPUT_HTML_FILE'] = 'TEMPORARY_OUTPUT'
        output_file = self.parameterAsFileOutput(parameters, self.OUTPUT_HTML_FILE, context)
        if output_file:
            self.create_html(output_file, _stats)
            results[self.OUTPUT_HTML_FILE] = output_file

        # TODO name the output layer based on the name of the input layer + 'Triangulation'
        out_crs = QgsCoordinateReferenceSystem(CRS.from_user_input('WGS 84 / UTM zone {}'.format(utm_zone)).to_string())
        (sink, dest_id) = self.parameterAsSink(parameters, self.OUTPUT, context, triangulation_attr_layer.fields(), QgsWkbTypes.Polygon, out_crs)
        sink.addFeatures(triangulation_attr_layer.getFeatures(), QgsFeatureSink.FastInsert)
        results[self.OUTPUT] = dest_id
        return results

    def name(self):
        return 'triangulation'

    def displayName(self):
        return '2.- Triangulation'

    def group(self):
        return 'First Pass Boundary Tools'

    def groupId(self):
        return 'fpboundarytools'

    def createInstance(self):
        return Triangulation()

    # def icon(self):
    #     return QgsApplication.getThemeIcon("/algorithms/mAlgorithmExtractLayerExtent.svg")

    # def svgIconPath(self):
    #     return QgsApplication.iconPath("/algorithms/mAlgorithmExtractLayerExtent.svg")

    # def tags(self):
    #     return 'polygon,vector,raster,extent,envelope,bounds,bounding,boundary,layer,round,rounded'.split(',')
