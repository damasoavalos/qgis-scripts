import os
import shutil
import processing
import datetime

from qgis.core import (QgsProcessing,
                       QgsProcessingAlgorithm,
                       QgsProcessingMultiStepFeedback,
                       QgsProcessingParameterFile,
                       QgsCoordinateReferenceSystem,
                       QgsProcessingParameterFeatureSink,
                       QgsVectorLayer,
                       QgsFeatureSink,
                       QgsFields,
                       QgsPointXY,
                       QgsFeature,
                       QgsGeometry,
                       QgsVectorFileWriter,
                       QgsWkbTypes,
                       QgsField)

from qgis.PyQt.QtCore import QCoreApplication, QVariant
from qgis.utils import Qgis


class combinecsv(QgsProcessingAlgorithm):
    INPUT = 'INPUT'
    OUTPUT = 'OUTPUT'

    def tr(self, string):
        # Returns a translatable string with the self.tr() function.
        return QCoreApplication.translate('Processing', string)

    def __init__ ( self ):
        super().__init__()
        self.lon_field = 'longitude'  # set the name for the field containing the longitude
        self.lat_field = 'latitude'  # set the name for the field containing the latitude
        self.stringCrs = 'epsg:4326'
        self.fieldsToAdd = []
        self.namesFieldsToAdd = []
        self.AddFields()

    # add fields
    def AddFields ( self ):

        # TODO Add fields for Seeding and application
        # Harvesting fields
        # 'Latitude'
        self.fieldsToAdd.append(QgsField('Latitude', QVariant.Double))
        self.namesFieldsToAdd.append('Latitude')
        # 'Longitude'
        self.fieldsToAdd.append(QgsField('Longitude', QVariant.Double))
        self.namesFieldsToAdd.append('Longitude')
        # 'Distance'
        self.fieldsToAdd.append(QgsField('Distance', QVariant.Double))
        self.namesFieldsToAdd.append('Distance')
        # 'Width'
        self.fieldsToAdd.append(QgsField('Width', QVariant.Double))
        self.namesFieldsToAdd.append('Width')
        # 'GrowYear'
        self.fieldsToAdd.append(QgsField('GrowYear', QVariant.Int))
        self.namesFieldsToAdd.append('GrowYear')
        # 'OriginalFieldName'
        self.fieldsToAdd.append(QgsField('OriginalFieldName', QVariant.String))
        self.namesFieldsToAdd.append('OriginalFieldName')
        # 'OriginalCropType'
        self.fieldsToAdd.append(QgsField('OriginalCropType', QVariant.String))
        self.namesFieldsToAdd.append('OriginalCropType')
        # 'VehicleID'
        self.fieldsToAdd.append(QgsField('VehicleID', QVariant.String))
        self.namesFieldsToAdd.append('VehicleID')
        # 'Timestamp'
        self.fieldsToAdd.append(QgsField('Timestamp', QVariant.Int))
        self.namesFieldsToAdd.append('Timestamp')
        # 'Heading'
        self.fieldsToAdd.append(QgsField('Heading', QVariant.Int))
        self.namesFieldsToAdd.append('Heading')
        # 'Duration'
        self.fieldsToAdd.append(QgsField('Duration', QVariant.Double))
        self.namesFieldsToAdd.append('Duration')
        # 'datetime'
        self.fieldsToAdd.append(QgsField('datetime', QVariant.DateTime))
        # fieldsToAddName.append('datetime')

    def ProcessCsv ( self, _csvFile, _sink, _feedback ):

        uri = "file:///{0}?encoding=UTF-8&delimiter={1}&xField={2}&yField={3}&crs={4}".format(_csvFile, ',', self.lon_field, self.lat_field, self.stringCrs)
        csvLayer = QgsVectorLayer(uri, 'points', 'delimitedtext')
        if (csvLayer.featureCount() > 0) and (csvLayer.isValid()):

            # Populate sink layer
            pt = QgsPointXY()
            outFeature = QgsFeature()
            attrs = []
            for feat in csvLayer.getFeatures():
                if _feedback.isCanceled():
                    return {}

                for nameField in self.namesFieldsToAdd:
                    attrs.append(feat[nameField])
                attrs.append(datetime.datetime.fromtimestamp(feat['Timestamp']).strftime('%Y-%m-%d %H:%M:%S'))
                pt.setX(float(feat[self.lon_field]))
                pt.setY(float(feat[self.lat_field]))
                outFeature.setAttributes(attrs)
                outFeature.setGeometry(QgsGeometry.fromPointXY(pt))
                _sink.addFeature(outFeature, QgsFeatureSink.FastInsert)
                attrs.clear()
            del csvLayer

    def initAlgorithm ( self, config=None ):
        self.addParameter(QgsProcessingParameterFile(self.INPUT, 'Folder', behavior=QgsProcessingParameterFile.Folder, fileFilter='All files (*.*)', defaultValue=None))
        self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT, 'As-Applied Points', type=QgsProcessing.TypeVectorPoint))

    def processAlgorithm ( self, parameters, context, feedback ):

        fields = QgsFields()
        for field in self.fieldsToAdd:
            fields.append(field)

        (sink, dest_id) = self.parameterAsSink(parameters, self.OUTPUT, context, fields, QgsWkbTypes.Point, QgsCoordinateReferenceSystem(self.stringCrs))

        parent_folder = self.parameterAsFile(parameters, self.INPUT, context)

        _Folders = sum(os.path.isdir(os.path.join(parent_folder, i)) for i in os.listdir(parent_folder))        
        totalFolders = _Folders if _Folders > 0 else 1
        feedback.setProgressText('Processing {0} {1}'.format(totalFolders, 'folder' if totalFolders == 1 else 'folders'))

        
        if totalFolders == 1:
            entries = [os.path.basename(os.path.normpath(parent_folder))]
        else:
            entries = os.listdir(parent_folder)

        for currentFolderNumber, name in enumerate(entries, start=1):
            if feedback.isCanceled():
                return {}

            if os.path.isdir(os.path.join(parent_folder, name)):
                Input_Folder = os.path.join(parent_folder, name)
            else:
                Input_Folder = self.parameterAsFile(parameters, self.INPUT, context)

            csvFiles = os.listdir(Input_Folder)
            total = 100.0 / len(csvFiles)
            feedback.setProgressText('Processing {0} {1} in folder {2}  ({3}/{4})'.format(len(csvFiles), 'file' if len(csvFiles) == 1 else 'files', name, currentFolderNumber, totalFolders))
            for currentFileNumber, file in enumerate(csvFiles, start=1):
                feedback.setProgress(int(currentFileNumber * total))
                if file.endswith('.csv'):
                    if feedback.isCanceled():
                        return {}
                    self.ProcessCsv(os.path.join(Input_Folder, file), sink, feedback)

        results = {self.OUTPUT: dest_id}
        outputs = {}
        return results

    def name ( self ):
        return 'combinecsv'

    def displayName ( self ):
        return '1.- Combine CSV'

    def group ( self ):
        return 'First Pass Boundary Tools'

    def groupId ( self ):
        return 'fpboundarytools'

    def createInstance ( self ):
        return combinecsv()
