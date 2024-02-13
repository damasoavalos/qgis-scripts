import math
# import utm

from pyproj import CRS
from unitconvert import lengthunits

from qgis.core import (QgsProcessing,
                       QgsProcessingAlgorithm,
                       QgsProcessingMultiStepFeedback,                      
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterField,                       
                       QgsProcessingParameterExtent,
                       QgsProcessingParameterFeatureSink,                     
                       QgsPointXY,                     
                       QgsVectorLayer,
                       QgsFeature,                      
                       QgsGeometry,
                       QgsPoint,
                       QgsFeatureSink,
                       QgsWkbTypes)

import processing


class PointsToRectangles(QgsProcessingAlgorithm):
    INPUT = 'INPUT'    
    HEADINGFIELD = 'HEADINGFIELD' 
    DISTANCEFIELD = 'DISTANCEFIELD'  
    WIDTHFIELD = 'WIDTHFIELD'
    OUTPUT = 'OUTPUT'
    EXTENT = 'EXTENT'

    def __init__(self):
        super().__init__()
        self.outLayer = None       

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterFeatureSource(self.INPUT, 'As-applied data points', types=[QgsProcessing.TypeVectorPoint], defaultValue=None))        
        self.addParameter(QgsProcessingParameterField(name=self.HEADINGFIELD, description='Heading field', defaultValue='heading', parentLayerParameterName=self.INPUT, type=QgsProcessingParameterField.Any, optional=False))
        self.addParameter(QgsProcessingParameterField(name=self.DISTANCEFIELD, description='Distance field', defaultValue='distance', parentLayerParameterName=self.INPUT, type=QgsProcessingParameterField.Any, optional=False))
        self.addParameter(QgsProcessingParameterField(name=self.WIDTHFIELD, description='Width field', defaultValue='width', parentLayerParameterName=self.INPUT, type=QgsProcessingParameterField.Any, optional=False))
        self.addParameter(QgsProcessingParameterExtent(self.EXTENT, 'Input extent to calculate UTM zone', optional=True))  
        self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT, 'As-applied rectangles', type=QgsProcessing.TypeVectorPolygon))

    def find_utm_zone(self, _rect, _feedback):
        if _feedback.isCanceled():
            return {}

        minx = _rect.xMinimum()
        miny = _rect.yMinimum()
        height = _rect.height()
        width = _rect.width()
        longitude = minx + width / 2.0
        latitude = miny + height / 2.0
        zone_number = math.floor(((longitude + 180) / 6) % 60) + 1
        # _utm = utm.from_latlon(latitude, longitude, True)

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
    
    def reproject_to_wgs84(self, _in_layer, _context, _feedback):
        if _feedback.isCanceled():
            return {}
                  
        _stringWgs84Crs = CRS.from_user_input('WGS 84').to_string()
        _parameter = {'INPUT': _in_layer, 'TARGET_CRS': _stringWgs84Crs, 'OUTPUT': 'memory:temp'}
        _wgs84Layer = processing.run('native:reprojectlayer', _parameter, context=_context, feedback=_feedback)['OUTPUT'] 
        return _wgs84Layer

    def translate(self, point, translation):
        return point[0] + translation[0], point[1] + translation[1]

    def rotate(self, point, angle, _feedback):
        if _feedback.isCanceled():
            return {}

        angle *= math.pi / 180.
        px, py = point
        qx = math.cos(angle) * px - math.sin(angle) * py
        qy = math.sin(angle) * px + math.cos(angle) * py
        return qx, qy

    def rectangle(self, width, height, angle, center, _feedback):
        if _feedback.isCanceled():
            return {}

        p1 = (-width/2, -height/2)
        p2 = (-width/2, +height/2)
        p3 = (+width/2, +height/2)
        p4 = (+width/2, -height/2)
        rotated = [self.rotate(p, angle, _feedback) for p in [p1, p2, p3, p4]]
        translated = [self.translate(p, center) for p in rotated]
        points = [QgsPoint(x, y) for x, y in translated]                
        return points        
        
    def processAlgorithm(self, parameters, context, feedback):
               
        input_layer = self.parameterAsVectorLayer(parameters, self.INPUT, context)
        heading_attribute = self.parameterAsString(parameters, self.HEADINGFIELD, context)
        distance_attribute = self.parameterAsString(parameters, self.DISTANCEFIELD, context)
        width_attribute = self.parameterAsString(parameters, self.WIDTHFIELD, context)
        rect = self.parameterAsExtent(parameters, self.EXTENT, context) 
        
        parameters['OUTPUT'].destinationName = '{}-rectangles'.format(input_layer.sourceName())
        (sink, dest_id) = self.parameterAsSink(parameters, self.OUTPUT, context, input_layer.fields(), QgsWkbTypes.Polygon, input_layer.crs())

        # -Find UTM zone-
        if rect.isNull():
            utm_zone = self.find_utm_zone(input_layer.extent(), feedback)
        else:
            utm_zone = self.find_utm_zone(rect, feedback)
        feedback.pushInfo('UTM Zone: {0}'.format(utm_zone))
        
        # -Reproject to UTM- 
        utm_layer = self.reproject_to_utm(input_layer, utm_zone, context, feedback)
        feedback.pushInfo("Layer reprojected to 'UTM Zone: {0}'".format(utm_zone))
            
        _uri = 'polygon?crs={}&index=yes'.format(utm_layer.crs().authid().lower())
        sink_layer = QgsVectorLayer(_uri, 'tempSinkLayer', 'memory')
        sink_layer_pr = sink_layer.dataProvider()
        sink_layer_pr.addAttributes(input_layer.fields())
        sink_layer.updateFields()
        
        total = 100.0 / utm_layer.featureCount()
        for currentFeature, feature in enumerate(utm_layer.getFeatures(), start=1):
            if feedback.isCanceled():
                return {}

            feedback.setProgress(int(currentFeature * total))
            geom = feature.geometry()
            p = geom.asPoint()
            
            # width_1 = (feature.attribute(widthAttribute) * 0.3048)
            # length_1 = (feature.attribute(distanceAttribute) * 0.3048)
            # ============================================================
            width = lengthunits.LengthUnit(feature.attribute(width_attribute), 'ft', 'm').doconvert()
            length = lengthunits.LengthUnit(feature.attribute(distance_attribute), 'ft', 'm').doconvert()
            direction = feature.attribute(heading_attribute)
            center = (p.x(), p.y())

            poly = QgsFeature()
            points = self.rectangle(width, length, -direction, center, feedback)
            points_xy = []
            for point in points:
                points_xy.append(QgsPointXY(point))
            poly.setGeometry(QgsGeometry.fromPolygonXY([points_xy]))
            poly.setAttributes(feature.attributes())
            sink_layer_pr.addFeature(poly)
        
        # -Reproject to WGS 84- 
        wgs84_layer = self.reproject_to_wgs84(sink_layer, context, feedback)
        feedback.pushInfo("Layer reprojected to 'WGS 84'")     
        sink.addFeatures(wgs84_layer.getFeatures(), QgsFeatureSink.FastInsert)

        input_layer = None

        return {self.OUTPUT: dest_id}     # results

    def name(self):
        return 'pointstorectangles'  

    def displayName(self):
        return 'Points To Rectangles'

    def group(self):
        return 'First Pass Tools'

    def groupId(self):
        return 'firstpasstools'

    def createInstance(self):
        return PointsToRectangles()

