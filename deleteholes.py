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

class deleteholes(QgsProcessingAlgorithm):

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
        
        paramValueField = QgsProcessingParameterNumber(self.VALUEFIELD, 'Remove holes with area less than', type=QgsProcessingParameterNumber.Double, minValue=1)
        paramValueField.setMetadata( {'widget_wrapper': { 'decimals': 1 }})
        self.addParameter(paramValueField) 
        
        self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT, 'Output without holes', type=QgsProcessing.TypeVectorPolygon))

    def ReprojectToWgs84(self, _inLayer, _context, _feedback):
        if _feedback.isCanceled():
               return {} 
                  
        _stringWgs84Crs = CRS.from_user_input('WGS 84').to_string()
        _parameter = {'INPUT': _inLayer, 'TARGET_CRS': _stringWgs84Crs, 'OUTPUT': 'memory:temp'}
        _wgs84Layer = processing.run('native:reprojectlayer', _parameter, context=_context, feedback=_feedback)['OUTPUT'] 
        return _wgs84Layer
                     
    def processAlgorithm(self, parameters, context, feedback):
        inLayer = self.parameterAsLayer(parameters, self.INPUT, context)        
        value = self.parameterAsDouble(parameters, self.VALUEFIELD, context)
              
        feedback.setProgressText(self.tr('Dissolving Delaunay triangles…'))
        deleteholesLayer = processing.run("native:deleteholes", {'INPUT': inLayer, 'MIN_AREA': value, 'OUTPUT': 'memory:'}, feedback=feedback, context=context)['OUTPUT']
        
        (sink, dest_id) = self.parameterAsSink(parameters, self.OUTPUT, context, deleteholesLayer.fields(), QgsWkbTypes.Polygon, deleteholesLayer.crs())      
        sink.addFeatures(deleteholesLayer.getFeatures(), QgsFeatureSink.FastInsert) 
        result = {self.OUTPUT: dest_id}
       
        return result

    def name(self):
        return 'deleteholes'

    def displayName(self):
        return '4.- Delete Holes'

    def group(self):
        return 'First Pass Boundary Tools'

    def groupId(self):
        return 'fpboundarytools'

    def createInstance(self):
        return deleteholes()

    #def icon(self):
    #    return QgsApplication.getThemeIcon("/algorithms/mAlgorithmExtractLayerExtent.svg")

    #def svgIconPath(self):
    #    return QgsApplication.iconPath("/algorithms/mAlgorithmExtractLayerExtent.svg")

    #def tags(self):
    #    return 'polygon,vector,raster,extent,envelope,bounds,bounding,boundary,layer,round,rounded'.split(',')    
