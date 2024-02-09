from qgis.core import   (QgsProcessing,
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
        self.addParameter(QgsProcessingParameterFolderDestination(self.INPUT, 'FolderPath',defaultValue=None))
        self.addParameter(QgsProcessingParameterString(self.LOT_ID, 'Lot ID', defaultValue='', multiLine=False))

    def processAlgorithm(self, parameters, context, model_feedback):
       
        feedback = QgsProcessingMultiStepFeedback(0, model_feedback)
        Input_Folder = self.parameterAsFile(parameters, self.INPUT, context)
        lot_id = self.parameterAsString(parameters, self.LOT_ID, context)

        try:
            connection = psycopg2.connect(user = "postgres",
                                          password = "Rk403FP!",
                                          host = "localhost",
                                          port = "5432",
                                          database ="launchpad")

            cursor = connection.cursor()
            QueryForLotID = ("SELECT  boundary_id, field_id, grower_id, farm_id,  field_name\
                                FROM public.boundaries_to_load\
                                where lot_id = '{0}'\
                                order by id;".format(lot_id))
            cursor.execute(QueryForLotID)
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
            #closing database connecion
            if (connection):
                cursor.close()
                connection.close()
                print("PostgresSQL connection is closed")


      
        #ListOfAttributes = pandas.read_csv(r'C:\Users\rida.khan\Documents\DBeaver\Backup\boundaries_to_load_20200707.csv')



       

        output_Filename_2 = os.path.join(Input_Folder, "2_Insert_Into_Fields.sql")
        
        with open(output_Filename_2,'w') as Insert_Into_Fields:
             Insert_Into_Fields.write("INSERT INTO public.fields\n" 
                            "(id, grower_id, farm_id, name, archived)\n" 
                            "values\n")
             for i, id_number in enumerate(range(len(boundary_id)), start=1):
                 if i == len(boundary_id):   
                    endchar = ';'
                 else:
                    endchar = ','
                 Insert_Into_Fields.write(" ('{0}', '{1}', '{2}', '{3}', false){4}\n".format(field_id[id_number], grower_id[id_number], farm_id[id_number], name[id_number], endchar))
             
        

        output_Filename_3 = os.path.join(Input_Folder, "3_Insert_Into_Boundaries.sql")

        with open(output_Filename_3,'w') as Insert_Into_Boundaries:
             Insert_Into_Boundaries.write("INSERT INTO public.boundaries\n" 
                            "(id, field_id, name, archived, irrigated)\n" 
                            "values\n")
             for i, id_number in enumerate(range(len(boundary_id)), start=1):
                 if i == len(boundary_id):   
                    endchar = ';'
                 else:
                    endchar = ','
                 Insert_Into_Boundaries.write(" ('{0}', '{1}', '{2}', false, false){3}\n".format(boundary_id[id_number], field_id[id_number], name[id_number], endchar))
            



        output_Filename_4 = os.path.join(Input_Folder, "4_Update_Boundaries_Shape_From_Boundaries_to_load_Table.sql")

        with open(output_Filename_4,'w') as Update_Boundaries_Table:
             Update_Boundaries_Table.write("UPDATE public.boundaries\n" 
                            "SET shape = boundaries_to_load.geom\n" 
                            "from boundaries_to_load\n"
                            "where (boundaries_to_load.boundary_id = boundaries.id) and (boundaries_to_load.lot_id = '{0}');".format(lot_id))



        output_Filename_5 = os.path.join(Input_Folder, "5_Update_Active_boundary_id_From_Boundaries_Table.sql")

        with open(output_Filename_5,'w') as Update_Active_Boundary:
             Update_Active_Boundary.write("UPDATE fields\n" 
                            "SET active_boundary_id = boundaries.id\n" 
                            "from boundaries\n"
                            "join boundaries_to_load on (boundaries_to_load.boundary_id = boundaries.id)\n"
                            "where (boundaries.field_id = fields.id) and (boundaries_to_load.lot_id = '{0}');".format(lot_id))

        # area is a generated column
        #output_Filename_6 = os.path.join(Input_Folder, "6_Update_Boundaries_Area_Field.sql")

        #with open(output_Filename_6,'w') as Update_Boundary_Area:
        #     Update_Boundary_Area.write("UPDATE public.boundaries\n" 
        #                    "SET area = ST_Area(shape)\n" 
        #                    "WHERE area = 0 or area is null;\n"
        #                    "DROP TABLE public.boundaries_to_load;\n")
                            


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
