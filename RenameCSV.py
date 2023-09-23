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
                        QgsWkbTypes,
                        QgsField)

from qgis.PyQt.QtCore import QVariant
from qgis.utils import Qgis
import os
import shutil
import processing
import datetime


class RenameCsv(QgsProcessingAlgorithm):
    INPUT = 'INPUT'
    OUTPUT = 'OUTPUT'    
    
    def __init__(self):
        super().__init__()       
        
    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterFile(self.INPUT, 'Folder', behavior=QgsProcessingParameterFile.Folder, fileFilter='All files (*.*)', defaultValue=None))
        # self.addParameter(QgsProcessingParameterNumber(self.OUTPUT, 'No of files', type:QgsProcessingParameterNumber.Integer, defaultValue=None))
        
    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(0, model_feedback)

        parent_folder = self.parameterAsFile(parameters, self.INPUT, context)
        for name in os.listdir(parent_folder):
           if os.path.isdir(os.path.join(parent_folder, name)):
               Input_Folder = os.path.join(parent_folder, name)               
                            
           for file in os.listdir(Input_Folder):
               if '#' in file:
                   os.rename(os.path.join(Input_Folder, file), os.path.join(Input_Folder, file.replace('#', '') ))
        
               if '%' in file:
                   os.rename(os.path.join(Input_Folder, file), os.path.join(Input_Folder, file.replace('%', '') ) )    
               
                
        results = {}       
        outputs = {}

        return results

    def name(self):
        return 'RenameCsv'

    def displayName(self):
        return 'RenameCsv'

    def group(self):
        return 'First Pass Tools'

    def groupId(self):
        return 'firstpasstools'

    def createInstance(self):
        return RenameCsv()
