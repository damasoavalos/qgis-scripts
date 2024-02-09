from qgis.core import QgsProcessing
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterVectorLayer
from qgis.core import QgsProcessingParameterNumber
from qgis.core import QgsProcessingParameterFeatureSink
from qgis.core import QgsCoordinateReferenceSystem
from qgis.core import QgsProperty
import processing


class Fp_simplify(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterVectorLayer('boundary', 'Boundary', types=[QgsProcessing.TypeVectorPolygon], defaultValue=None))
        self.addParameter(QgsProcessingParameterNumber('tolerance', 'Tolerance', type=QgsProcessingParameterNumber.Integer, minValue=1, maxValue=20, defaultValue=1))
        self.addParameter(QgsProcessingParameterFeatureSink('BoundarySimplified', 'Boundary Simplified', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, defaultValue=None))

    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(6, model_feedback)
        results = {}
        outputs = {}

        # Reproject layer to 3857
        alg_params = {
            'INPUT': parameters['boundary'],
            'TARGET_CRS': QgsCoordinateReferenceSystem('EPSG:3857'),
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ReprojectLayerTo3857'] = processing.run('native:reprojectlayer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        # Vertices Boundary
        alg_params = {
            'FIELD_LENGTH': 10,
            'FIELD_NAME': 'vertices_boundary',
            'FIELD_PRECISION': 3,
            'FIELD_TYPE': 1,
            'FORMULA': 'num_points($geometry)',
            'INPUT': outputs['ReprojectLayerTo3857']['OUTPUT'],
            'NEW_FIELD': True,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['VerticesBoundary'] = processing.run('qgis:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(2)
        if feedback.isCanceled():
            return {}

        # Simplify
        alg_params = {
            'INPUT': outputs['VerticesBoundary']['OUTPUT'],
            'METHOD': 0,
            'TOLERANCE': QgsProperty.fromExpression('@tolerance'),
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Simplify'] = processing.run('native:simplifygeometries', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(3)
        if feedback.isCanceled():
            return {}

        # Vertices Simplified
        alg_params = {
            'FIELD_LENGTH': 10,
            'FIELD_NAME': 'vertices_simplified',
            'FIELD_PRECISION': 3,
            'FIELD_TYPE': 1,
            'FORMULA': 'num_points($geometry)',
            'INPUT': outputs['Simplify']['OUTPUT'],
            'NEW_FIELD': True,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['VerticesSimplified'] = processing.run('qgis:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(4)
        if feedback.isCanceled():
            return {}

        # Reproject layer to 4326
        alg_params = {
            'INPUT': outputs['VerticesSimplified']['OUTPUT'],
            'TARGET_CRS': QgsCoordinateReferenceSystem('EPSG:4326'),
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ReprojectLayerTo4326'] = processing.run('native:reprojectlayer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(5)
        if feedback.isCanceled():
            return {}

        # Fix geometries
        alg_params = {
            'INPUT': outputs['ReprojectLayerTo4326']['OUTPUT'],
            'OUTPUT': parameters['BoundarySimplified']
        }
        outputs['FixGeometries'] = processing.run('native:fixgeometries', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['BoundarySimplified'] = outputs['FixGeometries']['OUTPUT']
        return results

    def name(self):
        return 'FP_Simplify'

    def displayName(self):
        return 'FP Simplify'

    def group(self):
        return 'First Pass Tools'

    def groupId(self):
        return 'firstpasstools'

    def createInstance(self):
        return Fp_simplify()
