import os

from qgis.core import (QgsProcessingAlgorithm,
                       QgsProcessingMultiStepFeedback,
                       QgsProcessingParameterFile)


class RenameCsv(QgsProcessingAlgorithm):
    INPUT = 'INPUT'
    OUTPUT = 'OUTPUT'    
    
    def __init__(self):
        super().__init__()       
        
    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterFile(self.INPUT, 'Folder', behavior=QgsProcessingParameterFile.Folder, fileFilter='All files (*.*)', defaultValue=None))
        # self.addParameter(QgsProcessingParameterNumber(self.OUTPUT, 'No of files', type:QgsProcessingParameterNumber.Integer, defaultValue=None))
        
    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multistep feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(0, model_feedback)

        parent_folder = self.parameterAsFile(parameters, self.INPUT, context)
        input_folder = None
        file = None
        for name in os.listdir(parent_folder):
            if os.path.isdir(os.path.join(parent_folder, name)):
                input_folder = os.path.join(parent_folder, name)

            for file in os.listdir(input_folder):
                if '#' in file:
                    os.rename(os.path.join(input_folder, file),
                              os.path.join(input_folder, file.replace('#', ''))
                              )
        
                if '%' in file:
                    os.rename(os.path.join(input_folder, file),
                              os.path.join(input_folder, file.replace('%', ''))
                              )

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
