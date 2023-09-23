import math
#import utm

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

class pointstorectangles(QgsProcessingAlgorithm):
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

    def FindUtmZone(self, _rect, _feedback):
        if _feedback.isCanceled():
               return {}  

        minx = _rect.xMinimum()
        miny = _rect.yMinimum()
        height = _rect.height()
        width = _rect.width()
        longitude = minx + width / 2.0
        latitude = miny + height / 2.0
        zone_number = math.floor(((longitude + 180) / 6) % 60) + 1
        #_utm = utm.from_latlon(latitude, longitude, True)

        if latitude >= 0:
            zone_letter = 'N'
        else:
            zone_letter = 'S'
        return '{0}{1}'.format(zone_number, zone_letter)         
        
    def ReprojectToUtm(self, _inLayer, _utmZone, _context, _feedback):
        if _feedback.isCanceled():
               return {} 

        # we are going to hardcode "'WGS 84 / UTM zone" this part of the srs, for now.
        _stringUtmCrs = CRS.from_user_input('WGS 84 / UTM zone {}'.format(_utmZone)).to_string()
        _parameter = {'INPUT': _inLayer, 'TARGET_CRS': _stringUtmCrs, 'OUTPUT': 'memory:temp'}
        _utmLayer = processing.run('native:reprojectlayer', _parameter, context=_context, feedback=_feedback)['OUTPUT'] 
        return _utmLayer
    
    def ReprojectToWgs84(self, _inLayer, _context, _feedback):
        if _feedback.isCanceled():
               return {} 
                  
        _stringWgs84Crs = CRS.from_user_input('WGS 84').to_string()
        _parameter = {'INPUT': _inLayer, 'TARGET_CRS': _stringWgs84Crs, 'OUTPUT': 'memory:temp'}
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
               
        inputLayer = self.parameterAsVectorLayer(parameters, self.INPUT, context)        
        headingAttribute = self.parameterAsString(parameters, self.HEADINGFIELD, context)
        distanceAttribute = self.parameterAsString(parameters, self.DISTANCEFIELD, context)
        widthAttribute = self.parameterAsString(parameters, self.WIDTHFIELD, context) 
        rect = self.parameterAsExtent(parameters, self.EXTENT, context) 
        
        parameters['OUTPUT'].destinationName = '{}-rectangles'.format(inputLayer.sourceName())
        (sink, dest_id) = self.parameterAsSink(parameters, self.OUTPUT, context, inputLayer.fields(), QgsWkbTypes.Polygon, inputLayer.crs()) 

         # -Find UTM zone- 
        if rect.isNull():
            utmZone = self.FindUtmZone(inputLayer.extent(), feedback)
        else:
            utmZone = self.FindUtmZone(rect, feedback)
        feedback.pushInfo('UTM Zone: {0}'.format(utmZone)) 
        
        # -Reproject to UTM- 
        utmLayer  = self.ReprojectToUtm(inputLayer, utmZone, context, feedback)
        feedback.pushInfo("Layer reprojected to 'UTM Zone: {0}'".format(utmZone)) 
            
        _uri = 'polygon?crs={}&index=yes'.format(utmLayer.crs().authid().lower())
        sinkLayer = QgsVectorLayer(_uri, 'tempSinkLayer', 'memory')
        sinkLayer_pr = sinkLayer.dataProvider() 
        sinkLayer_pr.addAttributes(inputLayer.fields())
        sinkLayer.updateFields()
        
        total = 100.0 / utmLayer.featureCount()
        for currentFeature, feature in enumerate(utmLayer.getFeatures(), start=1):
            if feedback.isCanceled():
                return {}

            feedback.setProgress(int(currentFeature * total))
            geom = feature.geometry()
            p = geom.asPoint()
            
            #width_1 = (feature.attribute(widthAttribute) * 0.3048)
            #length_1 = (feature.attribute(distanceAttribute) * 0.3048) 
            #============================================================
            width = lengthunits.LengthUnit(feature.attribute(widthAttribute), 'ft', 'm').doconvert()
            length = lengthunits.LengthUnit(feature.attribute(distanceAttribute), 'ft', 'm').doconvert()
            direction = feature.attribute(headingAttribute)       
            center = (p.x(), p.y())

            poly = QgsFeature()
            points = self.rectangle(width, length, -direction, center, feedback)
            pointsXY = []
            for point in points:
                pointsXY.append(QgsPointXY(point))
            poly.setGeometry(QgsGeometry.fromPolygonXY([pointsXY])) 
            poly.setAttributes(feature.attributes())
            sinkLayer_pr.addFeature(poly)        
        
        # -Reproject to WGS 84- 
        wgs84Layer = self.ReprojectToWgs84(sinkLayer, context, feedback)
        feedback.pushInfo("Layer reprojected to 'WGS 84'")     
        sink.addFeatures(wgs84Layer.getFeatures(), QgsFeatureSink.FastInsert)  

        inputLayer = None            

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
        return pointstorectangles()

