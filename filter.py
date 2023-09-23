from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtCore import QCoreApplication, QVariant

from qgis.core import (QgsApplication,
                       QgsProcessing,
                       QgsWkbTypes,
                       QgsField,
                       QgsFields,
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

class filter(QgsProcessingAlgorithm):

    INPUT = 'INPUT'    
    FILTERFIELD = 'FILTERFIELD'  
    OPERATOR = 'OPERATOR'
    MULTIPLIER = 'MULTIPLIER'
    VALUEFIELD = 'VALUEFIELD'
    OUTPUT = 'OUTPUT'
    CLEAR = 'CLEAR'

    OPERATORS = ['=',
                 '<>',
                 '>',
                 '>=',
                 '<',
                 '<=']

    def tr(self, string):
        # Returns a translatable string with the self.tr() function.        
        return QCoreApplication.translate('Processing', string)
    
    def __init__(self):
        super().__init__()        
        
    def initAlgorithm(self, config=None): 

        self.operators = ['=',
                          '≠',
                          '>',
                          '≥',
                          '<',
                          '≤']

        self.addParameter(QgsProcessingParameterVectorLayer(self.INPUT, 'Input layer', types=[QgsProcessing.TypeVectorPolygon]))        
        self.addParameter(QgsProcessingParameterField(name=self.FILTERFIELD, description='Field to filter', defaultValue='perimeter', parentLayerParameterName=self.INPUT, type=QgsProcessingParameterField.Numeric))
        
        paramValueField = QgsProcessingParameterNumber(self.VALUEFIELD, 'Value', type=QgsProcessingParameterNumber.Double, minValue=1)
        # only show two decimal places in parameter's widgets, not 6:
        paramValueField.setMetadata( {'widget_wrapper': { 'decimals': 1 }})
        self.addParameter(paramValueField) 
        
        self.addParameter(QgsProcessingParameterEnum(self.OPERATOR, 'Operator', self.operators, defaultValue=5)) 

        paramMultiplier = QgsProcessingParameterNumber(self.MULTIPLIER, 'Multiplier to filter minimum triangulation', type=QgsProcessingParameterNumber.Double, defaultValue=3,  minValue=1)
        # only show two decimal places in parameter's widgets, not 6:
        paramMultiplier.setMetadata( {'widget_wrapper': { 'decimals': 1 }})
        self.addParameter(paramMultiplier) 
        
        self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT, 'Output filter', type=QgsProcessing.TypeVectorPolygon, optional=True, createByDefault=False))

        self.addParameter(QgsProcessingParameterBoolean(self.CLEAR, 'Select to remove the filter', defaultValue=False))
             
    def processAlgorithm(self, parameters, context, feedback):
        inLayer = self.parameterAsLayer(parameters, self.INPUT, context)
        attribute = self.parameterAsString(parameters, self.FILTERFIELD, context)
        operator = self.OPERATORS[self.parameterAsEnum(parameters, self.OPERATOR, context)]
        value = self.parameterAsDouble(parameters, self.VALUEFIELD, context)
        multiplierValue = self.parameterAsDouble(parameters, self.MULTIPLIER, context)
        clear = self.parameterAsBool(parameters, self.CLEAR, context)
        if clear:
            expression_string = ''
            inLayer.setSubsetString(expression_string) 
            feedback.pushInfo('Filter removed') 
        else:
            expression_string = '{0} {1} {2}'.format(attribute, operator, (value * multiplierValue))
            inLayer.setSubsetString(expression_string)      
            feedback.pushInfo('Filter "{}" added'.format(expression_string))             
          
        outputFilterFields = QgsFields()
        #outputFilterFields.append(QgsField('fid', QVariant.Int))    

        (sink, dest_id) = self.parameterAsSink(parameters, self.OUTPUT, context, outputFilterFields, QgsWkbTypes.Polygon, inLayer.crs())      
        if sink:
            feedback.setProgressText(self.tr('Dissolving Delaunay triangles…'))
            dissolved_layer = processing.run("native:dissolve", {'INPUT': inLayer, 'OUTPUT': 'memory:'}, feedback=feedback, context=context)['OUTPUT']
            sink.addFeatures(dissolved_layer.getFeatures(), QgsFeatureSink.FastInsert) 
            result = {self.OUTPUT: dest_id}
        else:
            result = {}

        return result

    def name(self):
        return 'filter'

    def displayName(self):
        return '3.- Filter'

    def group(self):
        return 'First Pass Boundary Tools'

    def groupId(self):
        return 'fpboundarytools'

    def createInstance(self):
        return filter()

    #def icon(self):
    #    return QgsApplication.getThemeIcon("/algorithms/mAlgorithmExtractLayerExtent.svg")

    #def svgIconPath(self):
    #    return QgsApplication.iconPath("/algorithms/mAlgorithmExtractLayerExtent.svg")

    #def tags(self):
    #    return 'polygon,vector,raster,extent,envelope,bounds,bounding,boundary,layer,round,rounded'.split(',')    
