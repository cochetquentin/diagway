# -*- coding: utf-8 -*-
"""
/***************************************************************************
 SuppresionRoute
                                 A QGIS plugin
 supprime les routes déjà scanné
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2021-07-16
        git sha              : $Format:%H$
        copyright            : (C) 2021 by Cochet Quentin / Diagway
        email                : quentin.cochet@outlook.com
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
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication, Qt
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QProgressBar
from qgis.core import QgsProject
# Initialize Qt resources from file resources.py
from .resources import *

# Import the code for the DockWidget
from .SuppresionRoute_dockwidget import SuppresionRouteDockWidget
from .Layer import QgsLayer
from .Tools import *
import os.path


class SuppresionRoute:
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
            'SuppresionRoute_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&SuppresionRoute')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'SuppresionRoute')
        self.toolbar.setObjectName(u'SuppresionRoute')

        #print "** INITIALIZING SuppresionRoute"

        self.pluginIsActive = False
        self.dockwidget = None


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
        return QCoreApplication.translate('SuppresionRoute', message)

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

        icon_path = ':/plugins/SuppresionRoute/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u''),
            callback=self.run,
            parent=self.iface.mainWindow())

    #--------------------------------------------------------------------------

    def onClosePlugin(self):
        """Cleanup necessary items here when plugin dockwidget is closed"""

        #print "** CLOSING SuppresionRoute"

        # disconnects
        self.dockwidget.closingPlugin.disconnect(self.onClosePlugin)

        # remove this statement if dockwidget is to remain
        # for reuse if plugin is reopened
        # Commented next statement since it causes QGIS crashe
        # when closing the docked window:
        # self.dockwidget = None

        self.pluginIsActive = False

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""

        #print "** UNLOAD SuppresionRoute"

        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&SuppresionRoute'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar

    #--------------------------------------------------------------------------

    #Create the progress bar
    def initProgressBar(self, max):
        progressMessageBar = self.iface.messageBar().createMessage("Running...")
        progress = QProgressBar()
        progress.setMaximum(max)
        progress.setAlignment(Qt.AlignLeft|Qt.AlignVCenter)
        progressMessageBar.layout().addWidget(progress)
        self.iface.messageBar().pushWidget(progressMessageBar)
        return progress


    def fillFields(self, comboBox):
        comboBox.clear()
        items = self.dockwidget.listWidget_layers.selectedItems()
        if (len(items) > 0):
            layer = QgsLayer.findLayerByName(items[0].text())
            fields = layer.getFields()
            for f in fields:
                comboBox.addItem(f)

    
    def checkAll(self):
        items = self.dockwidget.listWidget_layers.selectedItems()
        if (len(items) > 0):
            if (self.dockwidget.comboBox_layers.currentLayer() is None):
                self.dockwidget.push_ok.setEnabled(False)
                return
        
            self.dockwidget.push_ok.setEnabled(True)
        else:
            self.dockwidget.push_ok.setEnabled(False)


    #Add all layers in the list widget
    def addLayersListWidget(self):
        listWidget = self.dockwidget.listWidget_layers
        layers = QgsProject.instance().mapLayers().values()
        for l in layers:
            listWidget.addItem(l.name())

    #Merge selected layers
    def mergedSelectLayers(self, output):
        items = self.dockwidget.listWidget_layers.selectedItems()
        layers = []
        for i in items:
            layer = QgsLayer.findLayerByName(i.text())
            layers.append(layer.vector)
        mergeLayers(layers, output)

    #Create layer with all the road already recorded
    def getRoadsDone(self, destination_layer, output_path):
        source_layer = QgsLayer(vectorLayer=self.dockwidget.comboBox_layers.currentLayer())
        extract = []

        ids = getAllFeatures(destination_layer, "section_id")

        if (not destination_layer.isLT93()):
            destination_layer = destination_layer.projectionLT93("C:\\temp\\diagwayProjectionTmpLayer\\{}_LT93.shp".format(destination_layer.name))

        progress = self.initProgressBar(len(ids))
        k = 1

        for i in ids:
            buffer_path = "C:\\temp\\diagwayProjectionTmpLayer\\buffer_{}.shp".format(str(k))
            extract_path = "C:\\temp\\diagwayProjectionTmpLayer\\extract_{}.shp".format(str(k))

            destination_layer.filter("section_id = {}".format(i))

            buffer = destination_layer.buffer(50, buffer_path)

            extractByLocation(source_layer, buffer, extract_path)

            extract.append(QgsLayer(extract_path, str(k)).vector)

            progress.setValue(k)
            k += 1

        mergeLayers(extract, output_path)

        return QgsLayer(output_path, "RoadsDone")

    #Create layer with all the road not recorded yet
    def getRoadsUndone(self, destination_layer, output_path):
        source_layer = QgsLayer(vectorLayer = self.dockwidget.comboBox_layers.currentLayer())

        output_buffer = "C:\\temp\\diagwayProjectionTmpLayer\\{}_buffer.shp".format(destination_layer.name)
        if (not destination_layer.isLT93()):
            destination_layer = destination_layer.projectionLT93("C:\\temp\\diagwayProjectionTmpLayer\\{}_LT93.shp".format(destination_layer.name))
        destination_layer = destination_layer.buffer(1, output_buffer)

        difference(source_layer.vector, destination_layer.vector, output_path)
        return QgsLayer(output_path, "RoadsUndone")
    
    #Algorith
    def algo(self):
        dir_path = "C:\\temp\\diagwayProjectionTmpLayer"
        createDir(dir_path)

        output_path = "C:\\temp\\diagwayProjectionTmpLayer\\merged.shp"
        self.mergedSelectLayers(output_path)

        destination_layer = QgsLayer(output_path, "")
        output_path = "C:\\temp\\diagwayProjectionTmpLayer\\getRoadsDone.shp"
        destination_layer = self.getRoadsDone(destination_layer, output_path)

        output_path = "C:\\temp\\diagwayProjectionTmpLayer\\getRoadsUndone.shp"
        final = self.getRoadsUndone(destination_layer, output_path)

        final.add()

        removeDir(dir_path)

        self.iface.messageBar().clearWidgets()
        self.iface.messageBar().pushMessage("Done", "", level=3, duration=4)

    #--------------------------------------------------------------------------

    def run(self):
        """Run method that loads and starts the plugin"""

        if not self.pluginIsActive:
            self.pluginIsActive = True

            #print "** STARTING SuppresionRoute"

            # dockwidget may not exist if:
            #    first run of plugin
            #    removed on close (see self.onClosePlugin method)
            if self.dockwidget == None:
                # Create the dockwidget (after translation) and keep reference
                self.dockwidget = SuppresionRouteDockWidget()
                self.addLayersListWidget()

                #Reset index comboBox
                self.dockwidget.comboBox_layers.setCurrentIndex(-1)
                self.dockwidget.comboBox_fields.setCurrentIndex(-1)

                #Connect buttons
                self.dockwidget.push_ok.clicked.connect(self.algo)

                #Connect comboBox
                self.dockwidget.comboBox_layers.layerChanged.connect(self.checkAll)

                #Connect list widget
                self.dockwidget.listWidget_layers.itemSelectionChanged.connect(lambda : self.fillFields(self.dockwidget.comboBox_fields))
                self.dockwidget.listWidget_layers.itemSelectionChanged.connect(self.checkAll)

            # connect to provide cleanup on closing of dockwidget
            self.dockwidget.closingPlugin.connect(self.onClosePlugin)

            # show the dockwidget
            # TODO: fix to allow choice of dock location
            self.iface.addDockWidget(Qt.RightDockWidgetArea, self.dockwidget)
            self.dockwidget.show()