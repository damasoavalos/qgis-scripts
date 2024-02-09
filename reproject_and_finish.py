from pyproj import CRS

from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtCore import QCoreApplication, QVariant
from qgis.utils import iface

from qgis.core import (QgsApplication,
                       QgsProcessing,
                       QgsWkbTypes,
                       QgsFeatureSink,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterVectorLayer,                       
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterField,
                       QgsProcessingParameterExtent,
                       QgsProcessingParameterEnum,
                       QgsProcessingParameterBoolean)
import processing

class reprojectandfinish(QgsProcessingAlgorithm):

    INPUT = 'INPUT'     
    VALUEFIELD = 'VALUEFIELD'
    OUTPUT = 'OUTPUT'    

    def tr(self, string):
        # Returns a translatable string with the self.tr() function.        
        return QCoreApplication.translate('Processing', string)
    
    def __init__(self):
        super().__init__()
        self.stringCrs = 'epsg:4326'
        
    def initAlgorithm(self, config=None):         

        self.addParameter(QgsProcessingParameterVectorLayer(self.INPUT, 'Input layer', types=[QgsProcessing.TypeVectorPolygon]))           
        self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT, 'Boundaries', type=QgsProcessing.TypeVectorPolygon))

    def ReprojectToWgs84(self, _inLayer, _context, _feedback):
        if _feedback.isCanceled():
               return {} 
                  
        _stringWgs84Crs = CRS.from_user_input('WGS 84').to_string()
        _parameter = {'INPUT': _inLayer, 'TARGET_CRS': _stringWgs84Crs, 'OUTPUT': 'memory:temp'}
        _wgs84Layer = processing.run('native:reprojectlayer', _parameter, context=_context, feedback=_feedback)['OUTPUT'] 
        return _wgs84Layer
                     
    def processAlgorithm(self, parameters, context, feedback):
        inLayer = self.parameterAsLayer(parameters, self.INPUT, context)        
                        
        # -Reproject to WGS 84- 
        wgs84Layer  = self.ReprojectToWgs84(inLayer, context, feedback)
        feedback.pushInfo("Layer reprojected to 'WGS 84'") 

        feedback.setProgressText(self.tr('Creating single parts…'))
        singlepartsLayer = processing.run("native:multiparttosingleparts", {'INPUT': inLayer, 'OUTPUT': 'memory:'}, feedback=feedback, context=context)['OUTPUT']
                

        (sink, dest_id) = self.parameterAsSink(parameters, self.OUTPUT, context, wgs84Layer.fields(), QgsWkbTypes.Polygon, wgs84Layer.crs())      
        sink.addFeatures(singlepartsLayer.getFeatures(), QgsFeatureSink.FastInsert) 
        result = {self.OUTPUT: dest_id}
       
        return result

    def name(self):
        return 'reprojectandfinish'

    def displayName(self):
        return '5.- Reproject And Finish'

    def group(self):
        return 'First Pass Boundary Tools'

    def groupId(self):
        return 'fpboundarytools'

    def createInstance(self):
        return reprojectandfinish()

    #def icon(self):
    #    return QgsApplication.getThemeIcon("/algorithms/mAlgorithmExtractLayerExtent.svg")

    #def svgIconPath(self):
    #    return QgsApplication.iconPath("/algorithms/mAlgorithmExtractLayerExtent.svg")

    #def tags(self):
    #    return 'polygon,vector,raster,extent,envelope,bounds,bounding,boundary,layer,round,rounded'.split(',')    
