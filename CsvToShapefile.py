from qgis.core import (QgsProcessing,
                        QgsProcessingAlgorithm,
                        QgsProcessingMultiStepFeedback,
                        QgsProcessingParameterFile,
                        QgsCoordinateReferenceSystem,
                        QgsVectorLayer,
                        QgsPointXY,
                        QgsFeature,
                        QgsGeometry,
                        QgsVectorFileWriter,
                        QgsWkbTypes)

from qgis.utils import Qgis
import os
import shutil
import processing


class CsvToShapefile(QgsProcessingAlgorithm):
    INPUT = 'INPUT'
    OUTPUT = 'OUTPUT'    
    
    def __init__(self):
        super().__init__()
        self.lon_field = 'longitude' # set the name for the field containing the longitude
        self.lat_field = 'latitude' # set the name for the field containing the latitude
        self.stringCrs = 'epsg:4326'      
        self.crs = 4326  # set the crs as needed
        self.spatRef = QgsCoordinateReferenceSystem(self.crs, QgsCoordinateReferenceSystem.EpsgCrsId)
    
    def processFolder(self, _csvFile, _outputShp):

        uri = "file:///{0}?encoding=UTF-8&delimiter={1}&xField={2}&yField={3}&crs={4}".format(_csvFile, ',', self.lon_field, self.lat_field, self.stringCrs)  
        layerPoints = QgsVectorLayer(uri, 'points', 'delimitedtext')       
        if (layerPoints.featureCount() > 0) and  (layerPoints.isValid()):

            outLayer = QgsVectorFileWriter.writeAsVectorFormat(layerPoints, _outputShp, 'UTF-8', layerPoints.crs(), "ESRI Shapefile")            
            del outLayer    

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterFile(self.INPUT, 'Folder', behavior=QgsProcessingParameterFile.Folder, fileFilter='All files (*.*)', defaultValue=None))
        # self.addParameter(QgsProcessingParameterNumber(self.OUTPUT, 'No of files', type:QgsProcessingParameterNumber.Integer, defaultValue=None))
        
    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(0, model_feedback)
        Input_Folder = self.parameterAsFile(parameters, self.INPUT, context)
        output_Folder = os.path.join(Input_Folder, 'Shapefile')
        
        if os.path.exists(output_Folder):
            shutil.rmtree(output_Folder, ignore_errors=True)            
        os.mkdir(output_Folder)        
         
        for file in os.listdir(Input_Folder):
            if file.endswith('.csv'):                
                self.processFolder(os.path.join(Input_Folder, file), os.path.join(output_Folder, os.path.splitext(file)[0]))                    
        
        results = {}       
        outputs = {}

        return results

    def name(self):
        return 'CsvToShapefile'

    def displayName(self):
        return 'CsvToShapefile'

    def group(self):
        return 'First Pass Tools'

    def groupId(self):
        return 'firstpasstools'

    def createInstance(self):
        return CsvToShapefile()
