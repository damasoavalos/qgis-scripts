# import os
# import sys
# import re

# from osgeo import ogr, osr
# from geopy import distance
# from pyproj import CRS

from qgis.core import (QgsProcessing,
                       QgsProcessingAlgorithm,
                       QgsProcessingMultiStepFeedback,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterField,
                       QgsProcessingParameterVectorLayer,
                       QgsProcessingParameterFeatureSink,
                       QgsFeatureRequest,
                       QgsStatisticalSummary,
                       QgsVectorLayer,
                       QgsFeature,
                       QgsField,
                       QgsFields,
                       QgsGeometry,
                       QgsPoint,
                       QgsFeatureSink,
                       QgsWkbTypes,
                       QgsApplication)

from qgis.core import QgsCoordinateReferenceSystem
from qgis.PyQt.QtCore import QCoreApplication, QVariant
import processing


class Namefields(QgsProcessingAlgorithm):
    INPUT = 'INPUT'    
    # HEADINGFIELD = 'HEADINGFIELD'
    # DISTANCEFIELD = 'DISTANCEFIELD'
    # SORTBYFIELD = 'SORTBYFIELD'
    GROUPBYFIELD = 'GROUPBYFIELD'  
    # ANGLE = 'ANGLE'
    OUTPUT = 'OUTPUT'

    def __init__(self):
        super().__init__()
        self.outLayer = None        

    # # use the vincenty formula to get accurate distance measurements
    # def sphereDistance(self, from_point, to_point):
    #    distance.VincentyDistance.ELLIPSOID = 'WGS-84'
    #    return distance.distance(from_point, to_point).meters

    # def angle_diff(self, angle1, angle2):
    #     return 180 - abs(abs(angle1 - angle2) - 180)
    
    def reproject_layer(self, _in_layer, to_epsg, _context, _feedback):
        if _feedback.isCanceled():
            return {}
                  
    #    #_stringWebMercatorCrs = CRS.from_user_input('WGS 84').to_string()  # this line return 'EPSG:4326'.           
    #    _parameter = {'INPUT': _in_layer, 'TARGET_CRS': to_epsg, 'OUTPUT': 'memory:temp'}
    #    _reprojectedLayer = processing.run('native:reprojectlayer', _parameter, context=_context)['OUTPUT'] 
    #    return _reprojectedLayer
    
    #def GetStats(self, _features, _field_name, _feedback):  
    #    if _feedback.isCanceled():
    #           return {} 
        
    #    # field = _layer.fields().at(_layer.fields().lookupField(_field_name))
    #    # request = QgsFeatureRequest().setFlags(QgsFeatureRequest.NoGeometry).setSubsetOfAttributes([_field_name], _layer.fields())
    #    # features = _layer.getFeatures(request)
       
    #    stat = QgsStatisticalSummary()
    #    for ft in _features:    
    #        stat.addVariant(ft[_field_name])    
    #    stat.finalize()      
                       
    #    return {
    #        'median': round(stat.median(), 4),
    #        'minimum': round(stat.min(), 4),
    #        'maximum': round(stat.max(), 4),
    #        'minority': round(stat.minority(), 4),
    #        'majority': round(stat.majority(), 4),
    #        'sum': round(stat.sum(), 4)
    #        }
         
    #def addLine(self, _points_list, _dist, _feedback):
    #    if _feedback.isCanceled():
    #           return {} 

    #    outFeat = QgsFeature()
    #    outFeat.setGeometry(QgsGeometry.fromPolyline(_points_list))
    #    startP = outFeat.geometry().asPolyline()[0]
    #    endP = outFeat.geometry().asPolyline()[-1]
    #    _heading = startP.azimuth(endP)
    #    if _heading < 181:
    #        _heading += 180
    #    outFeat.setAttributes([_heading, round(_dist, 2), len(_points_list)])
    #    return outFeat

    #def processFeatures(self, _features, _angle, _stat, _heading_attribute, _distance_attribute, _temp_pr, _feedback):
    #    if _feedback.isCanceled():
    #           return {} 

    #    _points_list = []
    #    _distance = 0         
    #    for i, feature in enumerate(_features):
    #        if i == 0:
    #            feature1 = feature
    #            continue
    #        # if float(feature[_distance_attribute]) < 1:
    #        #     continue

    #        feature2 = feature
    #        point1 = QgsPoint(feature1.geometry().asPoint().x(), feature1.geometry().asPoint().y())
    #        point2 = QgsPoint(feature2.geometry().asPoint().x(), feature2.geometry().asPoint().y())
    #        heading1 = int(feature1[_heading_attribute])
    #        heading2 = int(feature2[_heading_attribute])
           
    #        if not _points_list:
    #            _points_list.append(point1)
                
    #        pointDistance = self.sphereDistance((point1.y(), point1.x()), (point2.y(), point2.x()))   
    #        if self.angleDiff(heading1, heading2) <= _angle and pointDistance < _stat['majority']*2:                 
    #            _distance = _distance + pointDistance
    #            _points_list.append(point2)
    #        else:
    #            if _distance > 0:                  
    #                _temp_pr.addFeature(self.addLine(_points_list, _distance, _feedback))
    #            # _temp_pr.addFeature(self.addLine(_points_list, _distance, _feedback))
    #            _points_list.clear()
    #            _distance = 0
    #        feature1 = feature2
    #    # this is to make sure the last line get added
    #    if _distance > 0:
    #        _temp_pr.addFeature(self.addLine(_points_list, _distance, _feedback))
    #        _points_list.clear()
    #        _distance = 0
    #    # return _sink

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterFeatureSource(self.INPUT, 'As-applied data points', types=[QgsProcessing.TypeVectorPolygon], defaultValue=None))        
        # self.addParameter(QgsProcessingParameterField(name=self.HEADINGFIELD,
        #                                               description='Heading field',
        #                                               defaultValue='heading',
        #                                               parentLayerParameterName=self.INPUT,
        #                                               type=QgsProcessingParameterField.Any,
        #                                               optional=False))
        # self.addParameter(QgsProcessingParameterField(name=self.DISTANCEFIELD,
        #                                               description='Distance field',
        #                                               defaultValue='distance',
        #                                               parentLayerParameterName=self.INPUT,
        #                                               type=QgsProcessingParameterField.Any,
        #                                               optional=False))
        # self.addParameter(QgsProcessingParameterField(name=self.SORTBYFIELD,
        #                                               description='Field to sort by',
        #                                               defaultValue='timestamp',
        #                                               parentLayerParameterName=self.INPUT,
        #                                               type=QgsProcessingParameterField.Any,
        #                                               optional=False))
        self.addParameter(QgsProcessingParameterField(name=self.GROUPBYFIELD,
                                                      description='Field to group by',
                                                      defaultValue='VehicleID',
                                                      parentLayerParameterName=self.INPUT,
                                                      type=QgsProcessingParameterField.Any,
                                                      optional=True))
        # self.addParameter(QgsProcessingParameterNumber(self.ANGLE,
        #                                                'Angle (180° to create the whole path)',
        #                                                type=QgsProcessingParameterNumber.Integer,
        #                                                minValue=1,
        #                                                maxValue=180,
        #                                                defaultValue=5))
        self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT,
                                                            'As-applied lines',
                                                            type=QgsProcessing.TypeVectorLine))

    def processAlgorithm(self, parameters, context, feedback):
               
        input_layer = self.parameterAsVectorLayer(parameters, self.INPUT, context)
        group_by_attribute = self.parameterAsString(parameters, self.GROUPBYFIELD, context)
        (sink, dest_id) = self.parameterAsSink(parameters, self.OUTPUT, context, input_layer.fields(), QgsWkbTypes.MultiPolygon, input_layer.crs())

        ids = (640, 719, 972, 1249, 1251, 1356, 1453, 3308, 3439, 3445, 3448, 3451, 3453, 3929, 3930, 3931, 3932, 3934, 3935, 3936, 3937, 3938, 3939, 3940, 3941, 3998, 4035, 4085, 5000, 5717, 6076, 6079, 6081, 6276, 8373, 8787, 8905, 9221, 9369, 9958, 11604, 11687, 12094, 12274, 12728, 12730, 12780, 13037, 13380, 13404, 13517, 13519, 13520, 13521, 13522, 13681, 14204, 14331, 14710, 15132, 15526)

        for _id in ids:
            expression = "{0} = {1}".format(group_by_attribute, _id)
            request = QgsFeatureRequest().setFilterExpression(expression) 
            clause = QgsFeatureRequest.OrderByClause('id', ascending=True)
            orderby = QgsFeatureRequest.OrderBy([clause])
            request.setOrderBy(orderby)
            features = input_layer.getFeatures(request)
            i = 0
            for feature in features:
                i += 1
                feature['fieldname'] = '{0}-{1}'.format(feature['farmid'], i)
                sink.addFeature(feature) 
                   
            # # (sink, dest_id) = self.parameterAsSink(parameters, self.OUTPUT, context, input_layer.fields(), QgsWkbTypes.Polygon, input_layer.crs())
            # sink.addFeatures(input_layer.getFeatures(), QgsFeatureSink.FastInsert)
       
        results = {}
        outputs = {}
        results[self.OUTPUT] = dest_id       
        return {self.OUTPUT: dest_id}     # results

    def name(self):
        return 'namefields'  

    def displayName(self):
        return 'Name Fields'

    def group(self):
        return 'First Pass Tools'

    def groupId(self):
        return 'firstpasstools'

    def createInstance(self):
        return Namefields()

