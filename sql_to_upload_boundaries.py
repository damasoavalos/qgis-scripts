from qgis.core import (QgsProcessing,
                       QgsProcessingAlgorithm,
                       QgsProcessingMultiStepFeedback,
                       QgsProcessingParameterFolderDestination,
                       QgsProcessingParameterString,
                       QgsCoordinateReferenceSystem,
                       QgsVectorLayer,
                       QgsPointXY,
                       QgsFeature,
                       QgsGeometry,
                       QgsVectorFileWriter,
                       QgsWkbTypes,
                       QgsExpression,
                       QgsProcessingParameterFile)

from qgis.utils import Qgis
import os
import shutil
import processing
import pandas
import psycopg2


class SQLToUploadBoundaries (QgsProcessingAlgorithm):
    INPUT = 'INPUT'
    OUTPUT = 'OUTPUT'    
    LOT_ID = 'lotid'

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterFolderDestination(self.INPUT, 'FolderPath', defaultValue=None))
        self.addParameter(QgsProcessingParameterString(self.LOT_ID, 'Lot ID', defaultValue='', multiLine=False))

    def processAlgorithm(self, parameters, context, model_feedback):
       
        feedback = QgsProcessingMultiStepFeedback(0, model_feedback)
        input_folder = self.parameterAsFile(parameters, self.INPUT, context)
        lot_id = self.parameterAsString(parameters, self.LOT_ID, context)

        try:
            connection = psycopg2.connect(user="postgres",
                                          password="Rk403FP!",
                                          host="localhost",
                                          port="5432",
                                          database="launchpad")

            cursor = connection.cursor()
            query_for_lot_id = ('SELECT boundary_id, field_id, grower_id, farm_id, field_name '
                                'FROM public.boundaries_to_load '
                                'WHERE lot_id = \'{0}\' order by id;'.format(lot_id))
            cursor.execute(query_for_lot_id)
            boundary_records = cursor.fetchall()
             
            boundary_id = []
            field_id = []
            grower_id = []
            farm_id = []
            name = []

            for row in boundary_records:
                boundary_id.append(row[0])
                field_id.append(row[1])
                grower_id.append(row[2])
                farm_id.append(row[3])
                name.append(row[4])

        finally:
            # closing database connecion
            if connection:
                cursor.close()
                connection.close()
                print("PostgresSQL connection is closed")

        # ListOfAttributes = pandas.read_csv(r'C:\Users\rida.khan\Documents\DBeaver\Backup\boundaries_to_load_20200707.csv')

        output_filename_2 = os.path.join(input_folder, "2_Insert_Into_Fields.sql")
        
        with open(output_filename_2, 'w') as insert_into_fields:
            insert_into_fields.write("INSERT INTO public.fields("
                                     "id, "
                                     "grower_id, "
                                     "farm_id, "
                                     "name, "
                                     "archived) "
                                     "values")
            for i, id_number in enumerate(range(len(boundary_id)), start=1):
                if i == len(boundary_id):
                    endchar = ';'
                else:
                    endchar = ','
                insert_into_fields.write(" ('{0}', '{1}', '{2}', '{3}', false){4}\n".format(field_id[id_number],
                                                                                            grower_id[id_number],
                                                                                            farm_id[id_number],
                                                                                            name[id_number],
                                                                                            endchar)
                                         )

        output_filename_3 = os.path.join(input_folder, "3_Insert_Into_Boundaries.sql")

        with open(output_filename_3, 'w') as Insert_Into_Boundaries:
            Insert_Into_Boundaries.write("INSERT INTO public.boundaries("
                                         "id, "
                                         "field_id, "
                                         "name, "
                                         "archived, "
                                         "irrigated) "
                                         "values")
            for i, id_number in enumerate(range(len(boundary_id)), start=1):
                if i == len(boundary_id):
                    endchar = ';'
                else:
                    endchar = ','
                Insert_Into_Boundaries.write(" ('{0}', '{1}', '{2}', false, false){3}\n".format(boundary_id[id_number],
                                                                                                field_id[id_number],
                                                                                                name[id_number],
                                                                                                endchar)
                                             )

        output_filename_4 = os.path.join(input_folder, "4_Update_Boundaries_Shape_From_Boundaries_to_load_Table.sql")

        with open(output_filename_4, 'w') as Update_Boundaries_Table:
            Update_Boundaries_Table.write("UPDATE public.boundaries "
                                          "SET shape = boundaries_to_load.geom "
                                          "FROM boundaries_to_load "
                                          "WHERE (boundaries_to_load.boundary_id = boundaries.id) "
                                          "AND (boundaries_to_load.lot_id = '{0}');".format(lot_id))

        output_filename_5 = os.path.join(input_folder, "5_Update_Active_boundary_id_From_Boundaries_Table.sql")

        with open(output_filename_5, 'w') as Update_Active_Boundary:
            Update_Active_Boundary.write("UPDATE fields "
                                         "SET active_boundary_id = boundaries.id "
                                         "FROM boundaries "
                                         "JOIN boundaries_to_load "
                                         "ON (boundaries_to_load.boundary_id = boundaries.id) "
                                         "WHERE (boundaries.field_id = fields.id) "
                                         "AND (boundaries_to_load.lot_id = '{0}');".format(lot_id))

        # area is a generated column
        # output_filename_6 = os.path.join(input_folder, "6_Update_Boundaries_Area_Field.sql")

        # with open(output_filename_6,'w') as Update_Boundary_Area:
        #     Update_Boundary_Area.write("UPDATE public.boundaries "
        #                                "SET area = ST_Area(shape) "
        #                                "WHERE area = 0 OR area is null; "
        #                                "DROP TABLE public.boundaries_to_load;")

        results = {}       
        outputs = {}

        return results

    def name(self):
        return 'SQLToUploadBoundaries'

    def displayName(self):
        return 'SQLToUploadBoundaries'

    def group(self):
        return 'First Pass Tools'

    def groupId(self):
        return 'firstpasstools'

    def createInstance(self):
        return SQLToUploadBoundaries()
