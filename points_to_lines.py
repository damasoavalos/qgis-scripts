# import os
# import sys
# import re

# from osgeo import ogr, osr
from geopy import distance
from pyproj import CRS

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
from qgis import processing
# import processing


class PointsToLines(QgsProcessingAlgorithm):
    INPUT = 'INPUT'    
    HEADINGFIELD = 'HEADINGFIELD' 
    DISTANCEFIELD = 'DISTANCEFIELD'  
    SORTBYFIELD = 'SORTBYFIELD' 
    GROUPBYFIELD = 'GROUPBYFIELD'  
    ANGLE = 'ANGLE'   
    OUTPUT = 'OUTPUT'

    def __init__(self):
        super().__init__()
        self.outLayer = None        

    # use the vincenty formula to get accurate distance measurements
    def sphere_distance(self, from_point, to_point):
        distance.geodesic.ELLIPSOID = 'WGS-84'
        return distance.distance(from_point, to_point).meters

    def angle_diff(self, angle1, angle2):
        return 180 - abs(abs(angle1 - angle2) - 180)
    
    def reproject_layer(self, _in_layer, to_epsg, _context, _feedback):
        if _feedback.isCanceled():
            return {}
                  
        # _stringWebMercatorCrs = CRS.from_user_input('WGS 84').to_string()  # this line return 'EPSG:4326'.
        _parameter = {'INPUT': _in_layer, 'TARGET_CRS': to_epsg, 'OUTPUT': 'memory:temp'}
        _reprojectedLayer = processing.run('native:reprojectlayer', _parameter, context=_context)['OUTPUT'] 
        return _reprojectedLayer
    
    def get_stats(self, _features, _field_name, _feedback):
        if _feedback.isCanceled():
            return {}
        
        # field = _layer.fields().at(_layer.fields().lookupField(_field_name))
        # request = QgsFeatureRequest().setFlags(QgsFeatureRequest.NoGeometry).setSubsetOfAttributes([_field_name], _layer.fields())
        # features = _layer.getFeatures(request)
       
        stat = QgsStatisticalSummary()
        for ft in _features:    
            stat.addVariant(ft[_field_name])    
        stat.finalize()      
                       
        return {
            'median': round(stat.median(), 4),
            'minimum': round(stat.min(), 4),
            'maximum': round(stat.max(), 4),
            'minority': round(stat.minority(), 4),
            'majority': round(stat.majority(), 4),
            'sum': round(stat.sum(), 4)
            }
         
    def add_line(self, _points_list, _dist, _feedback):
        if _feedback.isCanceled():
            return {}

        out_feat = QgsFeature()
        out_feat.setGeometry(QgsGeometry.fromPolyline(_points_list))
        start_point = out_feat.geometry().asPolyline()[0]
        end_point = out_feat.geometry().asPolyline()[-1]
        _heading = start_point.azimuth(end_point)
        if _heading < 181:
            _heading += 180
        out_feat.setAttributes([_heading, round(_dist, 2), len(_points_list)])
        return out_feat

    def process_features(self, _features, _angle, _stat, _heading_attribute, _distance_attribute, _temp_pr, _feedback):
        if _feedback.isCanceled():
            return {}

        _pointsList = []                        
        _distance = 0         
        for i, feature in enumerate(_features):
            if i == 0:
                feature1 = feature
                continue
            # if float(feature[_distance_attribute]) < 1:
            #     continue

            feature2 = feature
            point1 = QgsPoint(feature1.geometry().asPoint().x(), feature1.geometry().asPoint().y())
            point2 = QgsPoint(feature2.geometry().asPoint().x(), feature2.geometry().asPoint().y())
            heading1 = int(feature1[_heading_attribute])
            heading2 = int(feature2[_heading_attribute])
           
            if not _pointsList:
                _pointsList.append(point1)   
                
            point_distance = self.sphere_distance((point1.y(), point1.x()), (point2.y(), point2.x()))
            if self.angle_diff(heading1, heading2) <= _angle and point_distance < _stat['majority']*2:
                _distance = _distance + point_distance
                _pointsList.append(point2)
            else:
                if _distance > 0:                  
                    _temp_pr.addFeature(self.add_line(_pointsList, _distance, _feedback))
                # _temp_pr.addFeature(self.addLine(_points_list, _distance, _feedback))
                _pointsList.clear()
                _distance = 0
            feature1 = feature2
        # this is to make sure the last line get added
        if _distance > 0:
            _temp_pr.addFeature(self.add_line(_pointsList, _distance, _feedback))
            _pointsList.clear()
            _distance = 0
        # return _sink

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterFeatureSource(self.INPUT, 'As-applied data points', [QgsProcessing.TypeVectorPoint], None))
        self.addParameter(QgsProcessingParameterField(self.HEADINGFIELD, 'Heading field', 'heading', self.INPUT, QgsProcessingParameterField.Any, False))
        self.addParameter(QgsProcessingParameterField(self.DISTANCEFIELD, 'Distance field', 'distance', self.INPUT, QgsProcessingParameterField.Any, False))
        self.addParameter(QgsProcessingParameterField(self.SORTBYFIELD, 'Field to sort by', 'timestamp', self.INPUT, QgsProcessingParameterField.Any, False))
        self.addParameter(QgsProcessingParameterField(self.GROUPBYFIELD, 'Field to group by', 'VehicleID', self.INPUT, QgsProcessingParameterField.Any, True))
        self.addParameter(QgsProcessingParameterNumber(self.ANGLE, 'Angle (180° to create the whole path)', QgsProcessingParameterNumber.Integer, 1, 180, 5))
        self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT, 'As-applied lines', QgsProcessing.TypeVectorLine))

    def processAlgorithm(self, parameters, context, feedback):
               
        input_layer = self.parameterAsVectorLayer(parameters, self.INPUT, context)
        heading_attribute = self.parameterAsString(parameters, self.HEADINGFIELD, context)
        distance_attribute = self.parameterAsString(parameters, self.DISTANCEFIELD, context)
        sort_by_attribute = self.parameterAsString(parameters, self.SORTBYFIELD, context)
        group_by_attribute = self.parameterAsString(parameters, self.GROUPBYFIELD, context)
        angle = self.parameterAsDouble(parameters, self.ANGLE, context)

        # # Create spatial reference
        # sr4326 = osr.SpatialReference()
        # sr4326.ImportFromEPSG(4326)

        # sr3857 = osr.SpatialReference()
        # sr3857.ImportFromEPSG(3857)
        # transform = osr.CoordinateTransformation(sr4326, sr3857)
        
        # let's make sure the layer is in "wgs 84" so "distance.geodesic.ELLIPSOID" can be calculated it
        input_layer_crs = input_layer.crs()  # save it to use to create the output with same CRS
        if input_layer_crs.authid() != 'EPSG:4326':
            in_layer = self.reproject_layer(input_layer, 'epsg:4326', context, feedback)
            # feedback.pushInfo("Layer reprojected to 'WGS 84'")
        else:
            in_layer = input_layer.clone()

        # # define outFeatFields fields
        # outFeatFields = QgsFields()
        # outFeatFields.append(QgsField(heading_attribute, QVariant.Int))
        # outFeatFields.append(QgsField(distance_attribute, QVariant.Double))

        _uri = 'Linestring?crs=epsg:4326&field=heading:integer&field=distance:double&field=numofpoints:integer&field=timediff:integer&index=yes'
        sink_layer = QgsVectorLayer(_uri, 'tempSinkLayer', 'memory')
        sink_layer_pr = sink_layer.dataProvider()
        
        if group_by_attribute:
            idx = in_layer.fields().indexOf(group_by_attribute)
            values = in_layer.uniqueValues(idx)

            for value in values:
                expression = "{0} = '{1}'".format(group_by_attribute, value)
                request = QgsFeatureRequest().setFilterExpression(expression)
                clause = QgsFeatureRequest.OrderByClause(sort_by_attribute, ascending=False)
                orderby = QgsFeatureRequest.OrderBy([clause])
                request.setOrderBy(orderby)
               
                stat_in_layer = self.get_stats(in_layer.getFeatures(request), distance_attribute, feedback)
                self.process_features(in_layer.getFeatures(request), angle, stat_in_layer, heading_attribute, distance_attribute, sink_layer_pr, feedback)
        else:
            
            request = QgsFeatureRequest()
            clause = QgsFeatureRequest.OrderByClause(sort_by_attribute, ascending=False)
            orderby = QgsFeatureRequest.OrderBy([clause])
            request.setOrderBy(orderby)

            stat_in_layer = self.get_stats(in_layer.getFeatures(request), distance_attribute, feedback)
            self.process_features(in_layer.getFeatures(request), angle, stat_in_layer, heading_attribute, distance_attribute, sink_layer_pr, feedback)
        
        # Reproject output layer to input layer crs 
        if input_layer_crs.authid() != 'EPSG:4326':
            sink_layer = self.reproject_layer(sink_layer, input_layer_crs.authid(), context, feedback)
        
        stat_sink_layer = self.get_stats(sink_layer.getFeatures(), 'distance', feedback)
        feedback.pushInfo("Total distance: {:,} meters".format(stat_sink_layer['sum']))
            
        parameters['OUTPUT'].destinationName = 'As-applied lines angle {}'.format(int(angle))
        (sink, dest_id) = self.parameterAsSink(parameters, self.OUTPUT, context, sink_layer.fields(), QgsWkbTypes.LineString, input_layer_crs)
        sink.addFeatures(sink_layer.getFeatures(), QgsFeatureSink.FastInsert)
        input_layer = None
        in_layer = None
        sink_layer = None

        # results = {}
        # # outputs = {}
        # results[self.OUTPUT] = dest_id
        # # return {self.OUTPUT: dest_id}
        return {self.OUTPUT: dest_id}     # results

    def name(self):
        return 'PointsToLines'  

    def displayName(self):
        return 'Points To Lines'

    def group(self):
        return 'First Pass Tools'

    def groupId(self):
        return 'firstpasstools'

    def createInstance(self):
        return PointsToLines()
