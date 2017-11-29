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
from PyQt4.QtCore import QSettings, QTranslator, qVersion, QCoreApplication
from PyQt4.QtGui import QAction, QIcon, QFileDialog
from qgis.core import QgsVectorLayer, QgsMapLayerRegistry, QgsVectorFileWriter, QgsCoordinateReferenceSystem
from qgis.gui import QgsMapCanvas, QgsProjectionSelectionWidget
from qgis.utils import iface
# Initialize Qt resources from file resources.py
import resources

############
import processing
############

# Import the code for the dialog
from volumator_dialog import volumDialog
import os.path

print "teste"


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


        # self.dlg.lineEdit.clear()
        # self.dlg.pushButton.clicked.connect(self.select_output_file)

        ##botao input
        self.dlg.input2.clear()
        self.dlg.botaoinput.clicked.connect(self.select_input_file)

        ###botao de seleciona CRS #31982
        temp = QgsCoordinateReferenceSystem()
        temp.createFromId(31982)
        self.dlg.crsSel.setCrs(temp)


        #muda seletor de CRS caso seja selecionado o orto
        self.dlg.defProjButton.clicked.connect(self.set_orto_crs)   


        


        ## definição do "sobre"
        self.dlg.aboutDefProj.setOpenExternalLinks(True)

        self.dlg.aboutDefProj.setText('''<a href='http://stackoverflow.com'>sobre</a>''')

        ##################################################################

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

    ################################################################ FUNÇOES

    def select_input_file(self):
        filename = QFileDialog.getOpenFileName(self.dlg, "Selecione o Arquivo de entrada ","", '*.csv')
        self.dlg.input2.setText(filename)


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


    ######################################################################

    def run(self):
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
            delaupath = "/home/kauevestena/.qgis2/processing/outputs/delau.shp"
            xymeanpath  = "/home/kauevestena/.qgis2/processing/outputs/XYmean.shp"
            point2spath = "/home/kauevestena/.qgis2/processing/outputs/datapoints2.shp"
            
            ###PATHS

            self.dlg.botaoinput.clicked.connect

            filename = self.dlg.input2.text()
            
            print filename
            
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

            ### projeto com o CRS escolhido
            iface.mapCanvas().mapRenderer().setDestinationCrs(self.dlg.crsSel.crs())

            #### adicionando na visualização
            self.add_layer_canvas(triangles)
            self.add_layer_canvas(datapoints)
            # # self.add_layer_canvas(xymean)




            #####################################################################################
            # pass
            