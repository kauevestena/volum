# -*- coding: utf-8 -*-
"""
/***************************************************************************
 volum
                                 A QGIS plugin
 Plugin Para Calculo de volumes voltado para
  conjuntos esparsos de dados (malha de pontos XYZ)
                              -------------------
        begin                : 2017-11-23
        git sha              : $Format:%H$
        copyright            : (C) 2017 by Kaue de Moraes Vestena - UFPR
        email                : kauemv2@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from PyQt4.QtCore import QSettings, QTranslator, qVersion, QCoreApplication, QVariant, QLocale
# import QString
from PyQt4.QtGui import QAction, QIcon, QFileDialog
from qgis.core import QgsVectorLayer, QgsMapLayerRegistry, QgsVectorFileWriter, QgsFeatureRequest, QgsPoint
from qgis.core import QgsCoordinateReferenceSystem, QgsFeatureRequest, QgsVectorLayerEditUtils
from qgis.core import QgsField, QgsGeometry
from qgis.gui import QgsMapCanvas, QgsProjectionSelectionWidget
from qgis.utils import iface
# Initialize Qt resources from file resources.py
import resources

############
import processing
import time
import math
############

# Import the code for the dialog
from volumator_dialog import volumDialog
import os.path

###################################################################### GLOBAL

# # # #if shapely works, this will work:
# # # print Point(0, 0).geom_type


def euclidean_distance(point1,point2):
# thx: https://gis.stackexchange.com/a/94215
    return math.sqrt((point2.x()-point1.x())**2 + (point2.y()-point1.y())**2)

def retrieve_att(layer,att_id,row_id):
    iterr = layer.getFeatures()
    attrs = []
    for feature in iterr:
        attrs.append(feature.attributes())
    return attrs[row_id][att_id]

def retrieve_atts(layer):
    iterr = layer.getFeatures()
    attrs = []
    for feature in iterr:
        attrs.append(feature.attributes())
    return attrs

def column(matrixList, i):
    return [row[i] for row in matrixList]

def sum(lst):
    sum = 0.0
    for val in lst:
        sum += val
    return sum


def get_areas(layer):
    # # # # #FUTURE : check if layer is a layer of polygons, 
    # # # # # if not return empty list and a warning
    iter = layer.getFeatures()
    areas = []
    for feature in iter:
        areas.append(feature.geometry().area())
        return areas

def get_triangles(layer,H1,H2,H3,op,hCalc):
    iterr = layer.getFeatures()
    triangles = []
    i = 0
    for feature in iterr:
        # triang = feature.geometry().exportToWkt()
        # print triang
        triangles.append(kTriangle(feature,H1[i],H2[i],H3[i],op,hCalc))
        i += 1
    return triangles


def get_datetime():
    return time.strftime("%d-%m-%Y_%H-%M-%S")

def define_op(MIN,MAX,hcal):
    onlyC = True
    onlyA = False
    BOTH  = False

    if hcal > MAX:
        onlyC = False
        onlyA = True

    if hcal > MIN and hcal < MAX:
        onlyC = onlyA = False
        BOTH = True

    op = 1

    if onlyA:
        op = 2
    elif BOTH:
        op = 3

    # print op
    return op



# computername = "kaue2"
computername = "kauevestena"
#HITF = Handle In The Future

print "teste "+get_datetime() #COMMENT

# class kPoint:
#     def __init__(self,x,y,z):
#         self.x = x
#         self.y = y
#         self.z = z 


def med3(v1,v2,v3):
    return (v1+v2+v3)/3

def r3(X1,Y1,X2):
    return (Y1*X2)/X1

def sameSignal(v1,v2):
    if   v1 > 0.0 and v2 > 0.0 :
        return True
    elif v1 < 0.0 and v2 < 0.0 :
        return True
    else:
        return False

def triangleType(diffs):
    #to define in wich segments the point will
    # need to be interpolated
    #case 1: 1 2,2 3
    #case 2: 1 2,3 1
    #case 3: 2 3,3 1
    c12 = not sameSignal(diffs[0],diffs[1])
    c23 = not sameSignal(diffs[1],diffs[2])
    c31 = not sameSignal(diffs[2],diffs[0])
    # print [c12,c23,c31,diffs]
    if c12 and c23:
        return 1
    elif c12 and c31:
        return 2
    elif c31 and c23:
        return 3
    else:
        return 4

def sum2abs(v1,v2):
    return abs(v1)+abs(v2)

class kTriangle:
    triangWKT = ""
    poly = None
    area = 0.0
    # vH1 = 0.0
    # vH2 = 0.0
    # vH3 = 0.0
    vH = 0.0
    vhs = []
    volCt = 0.0
    volAt = 0.0
    hmed = 0.0
    p = [] #
    interPT1 = None
    interPT2 = None
    def __init__(self,feature,h1,h2,h3,op,hCalc):
        self.poly = feature.geometry().asPolygon()
        self.triangWKT = feature.geometry().exportToWkt()
        self.area = feature.geometry().area()
        self.h1 = h1
        self.h2 = h2
        self.h3 = h3
        self.hmed = med3(self.h1,self.h2,self.h3)
        self.interPT1 = feature.geometry().interpolate(210).asPoint() #NEXT
        if op == 1:
            self.vH = self.hmed - hCalc
            self.volCt = self.area * self.vH 
        elif op == 2:
            self.vH = hCalc - self.hmed
            self.volAt = self.area *  self.vH
        else:
            # self.vH1 = self.h1 - hCalc
            # self.vH2 = self.h2 - hCalc
            # self.vH3 = self.h3 - hCalc
            vhs = [self.h1 - hCalc,self.h2 - hCalc,self.h3 - hCalc]
            dist1 = euclidean_distance(self.poly[0][0],self.poly[0][1])
            dist1 = euclidean_distance(self.poly[0][1],self.poly[0][2])
            dist1 = euclidean_distance(self.poly[0][2],self.poly[0][0])
            case = triangleType(vhs)
            if case == 4:
                self.vH = med3(vhs[0],vhs[1],vhs[2])
                if self.vH > 0:
                    self.volCt = self.area * self.vH
                else :
                    self.volAt = self.area * abs(self.vH)
            elif case == 1:
                v12 = sum2abs(vhs[0],vhs[1])
                v23 = sum2abs(vhs[1],vhs[2])
            elif case == 2:
                v12 = sum2abs(vhs[0],vhs[1])
                v13 = sum2abs(vhs[0],vhs[2])
            elif case == 3:
                v23 = sum2abs(vhs[1],vhs[2])
                v13 = sum2abs(vhs[0],vhs[2])

    # def convToListOfQstring(list):
    #     out = []
    #     for val in list:
    #         out.append(QString(val))



#########################################################################


class volum:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'volum_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        ## Create the dialog (after translation) and keep reference
        self.dlg = volumDialog()


        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Volumator')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'volum')
        self.toolbar.setObjectName(u'volum')
       
       #####################################################################

        self.dlg.hCalc.setMaximum(100000.0)


        # self.dlg.lineEdit.clear()
        # self.dlg.pushButton.clicked.connect(self.select_output_file)

        ##botao input
        self.dlg.input2.clear()
        self.dlg.botaoinput.clicked.connect(self.select_input_file)

        ##botao output
        self.dlg.outputTxt.clear()
        self.dlg.botaoOutput.clicked.connect(self.select_output_file)

        #botao minmax
        self.dlg.obMaxMin.clicked.connect(self.obtain_max_min)

        #botao ids
        self.dlg.obIDs.clicked.connect(self.obtain_ids)

        ###botao de seleciona CRS #31982
        temp = QgsCoordinateReferenceSystem()
        temp.createFromId(31982)
        self.dlg.crsSel.setCrs(temp)


        #muda seletor de CRS caso seja selecionado o orto
        self.dlg.defProjButton.clicked.connect(self.set_orto_crs)   

        ## definição do "sobre" 
        self.dlg.aboutDefProj.setOpenExternalLinks(True)

        #trocando virgula (argh) por ponto
        self.dlg.hCalc.setLocale(QLocale("UnitedStates")) #LANGUAGE
        self.dlg.hEquip.setLocale(QLocale("UnitedStates")) #LANGUAGE
        self.dlg.hEquip.setValue(1.5)

        #hiding everithing that is not useful at the beggining #DO
        # self.dlg.hEquip.hide()




        ##################################################################


        # ####################### LINHAS A VIRAR COMENTARIO
        self.dlg.input2.setText("/home/"+computername+"/Documents/ex.csv") #COMMENT
        self.dlg.outputTxt.setText("/home/"+computername+"/report.txt") #COMMENT



        ######################



    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('volum', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        # Create the dialog (after translation) and keep reference
        #self.dlg = volumDialog() ### isso causava o bug da janela de dialogo nao abrir...

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/volum/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Volume para pontos esparsos'),
            callback=self.run,
            parent=self.iface.mainWindow())


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&Volumator'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar

    ################################################################ FUNÇOES-MEMBRO 

    def select_input_file(self):
        filename = QFileDialog.getOpenFileName(self.dlg, "Selecione o Arquivo de entrada ","", '*.csv')
        self.dlg.input2.setText(filename)

    def select_output_file(self):
        filename = QFileDialog.getSaveFileName(self.dlg, "Selecione o Arquivo de saida ","", '*.txt')
        self.dlg.outputTxt.setText(filename)


    def add_layer_canvas(self,layer):
        # canvas = QgsMapCanvas()
        QgsMapLayerRegistry.instance().addMapLayer(layer)
        QgsMapCanvas().setExtent(layer.extent())
        # canvas.setLayerSet([QgsMapCanvasLayer(layer)])
        
    def set_orto_crs(self):
        # if self.dlg.defProjButton.clicked:
        temp = QgsCoordinateReferenceSystem()
        temp.createFromProj4("+proj=ortho +lat_0=0.0 +lon_0=0.0 +x_0=0 +y_0=0")
        self.dlg.crsSel.setCrs(temp)

    def obtain_max_min(self):
        if self.dlg.input2.text() != "":
            path = self.dlg.input2.text()+"?delimiter=%s&xField=%s&yField=%s" % (",", "X", "Y")
            layer = QgsVectorLayer(path, "pontosTemp", "delimitedtext")
            self.dlg.lMAX.setText(str(max(column(retrieve_atts(layer),3))))
            self.dlg.lMIN.setText(str(min(column(retrieve_atts(layer),3))))
            layer = None

    def obtain_ids(self):
        if self.dlg.input2.text() != "":
            path = self.dlg.input2.text()+"?delimiter=%s&xField=%s&yField=%s" % (",", "X", "Y")
            layer = QgsVectorLayer(path, "pontosTemp", "delimitedtext")
            idList = column(retrieve_atts(layer),0)
            idList2 = []
            for val in idList:
                idList2.append(str(val))
            self.dlg.oriSelec.addItems(idList2)
            self.dlg.stationSelec.addItems(idList2)
            layer = None




    ######################################################################

    def run(self):
        
        #
        crsOrt = QgsCoordinateReferenceSystem()
        crsOrt.createFromProj4("+proj=ortho +lat_0=0.0 +lon_0=0.0 +x_0=0 +y_0=0")

        """Run method that performs all the real work"""
        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()

        # See if OK was pressed






        if result:
            # Do something useful here - delete the line containing pass and
            # substitute with your code.


            ##################################################################################### CODIGO

            ###PATHS
            delaupath = "/home/"+computername+"/.qgis2/processing/outputs/delau.shp"  #HITF
            xymeanpath  = "/home/"+computername+"/.qgis2/processing/outputs/XYmean.shp" #HITF
            point2spath = "/home/"+computername+"/.qgis2/processing/outputs/datapoints2.shp" #HITF
            # outpath = "/home/"+computername+"/report.txt" #HITF
            
            ###PATHS

            self.dlg.botaoinput.clicked.connect

            filename = self.dlg.input2.text()
            
            # print filename
            
            path2 = filename+"?delimiter=%s&xField=%s&yField=%s" % (",", "X", "Y")

            datapoints = QgsVectorLayer(path2, "pontos", "delimitedtext")


                
            datapoints.setCrs(self.dlg.crsSel.crs())


            

            processing.runalg("qgis:delaunaytriangulation",datapoints,delaupath)

            triangles = QgsVectorLayer(delaupath,"triangles","ogr")

            

            processing.runalg("qgis:meancoordinates",datapoints,None,None,xymeanpath)

            xymean = QgsVectorLayer(xymeanpath,"pmed","ogr")


            ##passando todos para o CRS selecionado
            triangles.setCrs(self.dlg.crsSel.crs())
            xymean.setCrs(self.dlg.crsSel.crs())





            # # # # # # # # # # # # #FUTURE FEATURE: IF CRS IS ORTHO, TRANSLADE ALL POINTS TO THE TOPOCENTER
            # # # # # # # # if self.dlg.crsSel.crs() == crsOrt:
            # # # # # # # #     pass

            # # # # # # # # vlayer = datapoints
            # # # # # # # # # u = QgsVectorLayerEditUtils( vlayer )
            # # # # # # # # vlayer.beginEditCommand("Translate")
            # # # # # # # # for feat in vlayer.getFeatures():
            # # # # # # # #     ff = feat.id()
            # # # # # # # #     # vlayer.translateFeature(ff,1000,1000)
            # # # # # # # #     ox = feat.geometry().asPoint().x()
            # # # # # # # #     oy = feat.geometry().asPoint().y()
            # # # # # # # #     tx = 10000
            # # # # # # # #     ty = 1000
            # # # # # # # #     geom = QgsGeometry.fromPoint(QgsPoint(ox+tx,oy+ty))

            # # # # # # # #     vlayer.dataProvider().changeGeometryValues({ ff : geom })

            # # # # # # # #     vlayer.updateFeature(feat)
            # # # # # # # #     # vlayer.updateExtents()

            # # # # # # # #     ox2 = feat.geometry().asPoint().x()

            # # # # # # # #     # print ox-ox2
            # # # # # # # # # vlayer.beginEditCommand("Translate")
            # # # # # # # # vlayer.commitChanges()
            # # # # # # # # vlayer.endEditCommand()

            # vlayer.updateExtents()

            # # # # # # ok

            # x = retrieve_att(datapoints,1,0)



            #definindo a maior e a menor altitude
            MIN = min(column(retrieve_atts(datapoints),3))
            MAX = max(column(retrieve_atts(datapoints),3))

            ## DEFINIÇÃO DA ALTITUDE DE CALCULO
            hcal = float(self.dlg.hCalc.text())

            ## booleanos para apenas corte ou aterro


            #vector with heights, indexes of points and finally height of each point
            heigths = column(retrieve_atts(datapoints),3)
            
            iP1 = column(retrieve_atts(triangles),0)
            iP2 = column(retrieve_atts(triangles),1)
            iP3 = column(retrieve_atts(triangles),2)

            Hp1 = []
            Hp2 = []
            Hp3 = []

            for ind in iP1:
                Hp1.append(heigths[int(ind)])

            for ind in iP2:
                Hp2.append(heigths[int(ind)])

            for ind in iP3:
                Hp3.append(heigths[int(ind)])

            op = define_op(MIN,MAX,hcal)
            
            # print [len(Hp1),len(Hp2),len(Hp3),len(iP1),len(heigths)] #COMMENT

            # areas = get_areas(triangles)

            # print areas

            # print [Hp1,Hp2,Hp3]
            
            vec_triangles = get_triangles(triangles,Hp1,Hp2,Hp3,op,hcal)

            print vec_triangles[0].poly[0]
            print [vec_triangles[0].interPT1[0],vec_triangles[0].interPT1[1]]



            
            # Adicionando as altitudes aos triangulos, area e demais calculos

            # # # # # # # triangles.beginEditCommand("Attribute")
            # # # # # # # # triangles.addAttribute(QgsField("hP1",QVariant.Double))
            # # # # # # # triangles.dataProvider().addAttributes([QgsField("hP1",QVariant.Double),QgsField("hP2",QVariant.Double),QgsField("hP3",QVariant.Double)])

            # # # # # # # provider = triangles.dataProvider()

            # # # # # # # areas = [ feat.geometry().area() 
            # # # # # # #         for feat in triangles.getFeatures() ]

            # # # # # # # field = QgsField("area", QVariant.Double)
            # # # # # # # provider.addAttributes([field])
            # # # # # # # triangles.updateFields()

            # # # # # # # idx = triangles.fieldNameIndex('area')

            # # # # # # # for area in areas:
            # # # # # # #     new_values = {idx : float(area)}
            # # # # # # #     provider.changeAttributeValues({areas.index(area):new_values})

            # # # # # # # idx2 = triangles.fieldNameIndex('hP1')
            

            # # # # # # # triangles.endEditCommand()

            # # # # # # # triangles.updateFields()
            

            


                    



            ######################################################DEVEM ESTAR NO FINAL DO CODIGO

            # # #Relatorio de saida
            if self.dlg.outputTxt.text()  != "":
                file = open(self.dlg.outputTxt.text(),"w")
                file.write("############## ~~VOLUMATOR 0.1 ~~ ##############\n")
                file.write("        Relatorio de Saida do Processamento\n\n")

                sumCt = 0.0
                sumAt = 0.0
                sumArea = 0.0

                for tri in vec_triangles:
                    sumCt   += tri.volCt
                    sumAt   += tri.volAt
                    sumArea += tri.area

                nl = "\n"

                file.write("Volume de Corte: " +str(sumCt)+" m3 (metros cubicos)"+nl)
                file.write("Volume de Aterro: "+str(sumAt)+" m3 (metros cubicos)"+nl+nl)

                file.write("Dados de Entrada: "+nl)
                file.write("Arquivo de Entrada: "+self.dlg.input2.text()+nl)
                file.write("Altura (ou \"cota\") utilizada para calculo: "+str(hcal)+nl)
                file.write("Altura Max. "+str(MAX)+nl)
                file.write("Altura Min. "+str(MIN)+nl)
                if hcal < MIN:
                    file.write("Altura de passagem (mesmo volume de Corte e Aterro): "+str(hcal+(sumCt/sumArea))+nl)


                file.close()

                


            # # ####



            ### projeto com o CRS escolhido
            iface.mapCanvas().mapRenderer().setDestinationCrs(self.dlg.crsSel.crs())

            #### adicionando na visualização
            self.add_layer_canvas(triangles)
            self.add_layer_canvas(datapoints)
            # self.add_layer_canvas(xymean)  #COMMENT


            #####################################################################################
            # pass

            print "end" #COMMENT
            