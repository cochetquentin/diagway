# -*- coding: utf-8 -*-
"""
/***************************************************************************
 DiagwayProjection
                                 A QGIS plugin
 Projection de route
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2021-06-29
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
from qgis.PyQt.QtWidgets import QAction, QFileDialog, QProgressBar, QPushButton
from qgis.core import QgsMapLayerProxyModel, QgsMessageLog, Qgis

# Initialize Qt resources from file resources.py
from .resources import *

# Import the code for the DockWidget
from .DiagwayProjection_dockwidget import DiagwayProjectionDockWidget
from .Layer import QgsLayer
from .Worker import Worker
from .Tools import *
import os.path


class DiagwayProjection(QtCore.QObject):
    """Constructor & Variables"""
    def __init__(self, iface):
        #Multi-threading
        QtCore.QObject.__init__(self)

        # Save reference to the QGIS interface
        self.iface = iface

        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)

        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'DiagwayProjection_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&DiagwayProjection')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'DiagwayProjection')
        self.toolbar.setObjectName(u'DiagwayProjection')

        #print "** INITIALIZING DiagwayProjection"
        self.pluginIsActive = False
        self.dockwidget = None
    #--------------------------------------------------------------------------

    """Function for the plugins"""
    #Get the translation for a string using Qt translation API
    def tr(self, message):
        """
        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('DiagwayProjection', message)

    #Add a toolbar icon to the toolbar
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
        """
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

    #Create the menu entries and toolbar icons inside the QGIS GUI
    def initGui(self):
        icon_path = ':/plugins/DiagwayProjection/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'DiagwayProjection'),
            callback=self.run,
            parent=self.iface.mainWindow())

    #Cleanup necessary items here when plugin dockwidget is closed
    def onClosePlugin(self):
        print("** CLOSING DiagwayProjection")

        # disconnects
        self.dockwidget.closingPlugin.disconnect(self.onClosePlugin)

        # remove this statement if dockwidget is to remain
        # for reuse if plugin is reopened
        # Commented next statement since it causes QGIS crashe
        # when closing the docked window:
        # self.dockwidget = None

        self.pluginIsActive = False

    #Removes the plugin menu item and icon from QGIS GUI
    def unload(self):
        print("** UNLOAD DiagwayProjection")

        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&DiagwayProjection'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar
    #--------------------------------------------------------------------------

    """Function for the algorithm"""
    #Create the path for the CSV file (Replace file)
    def saveFile(self):
        filename, _filter = QFileDialog.getSaveFileName(self.dockwidget, "Select output file ","", '*.csv')
        self.dockwidget.lineEdit_file.setText(filename)

    #Create the path for the CSV file (Complete file)
    def selectFile(self):
        filename, _filter = QFileDialog.getOpenFileName(self.dockwidget, "Select output file ","", '*.csv')
        self.dockwidget.lineEdit_file_complete.setText(filename)

    #Get source, destination layer and the CSV path
    def getSourceDestFile(self):
        if (self.dockwidget.radio_a.isChecked()):
            path_csv = self.dockwidget.lineEdit_file_complete.text()
            layer_source = self.dockwidget.source_comboBox_layers_complete.currentLayer()
            layer_dest = self.dockwidget.destination_comboBox_layers_complete.currentLayer()
        else:
            path_csv = self.dockwidget.lineEdit_file.text()
            layer_source = self.dockwidget.source_comboBox_layers.currentLayer()
            layer_dest = self.dockwidget.destination_comboBox_layers.currentLayer()

        layer_source = QgsLayer(vectorLayer=layer_source)
        layer_dest = QgsLayer(vectorLayer=layer_dest)
        
        return layer_source, layer_dest, path_csv

    #Filled the combo box fields
    def fillFields(self, comboBox):
        comboBox.clear()
        layer = self.dockwidget.sender().currentLayer()
        if layer is not None:
            fields = layer.fields()
            for f in fields:
                comboBox.addItem(f.name())

    #Check if all box are correct
    def checkAll(self):
        layer_source, layer_dest, path_csv = self.getSourceDestFile()

        check = ((layer_source != layer_dest) and (layer_source != None) and (layer_dest != None) and (path_csv != "") and layer_source.isLT93() and layer_dest.isLT93())

        if (self.dockwidget.radio_w.isChecked()):
            self.dockwidget.push_next.setEnabled(check)
        else:
            self.dockwidget.push_next_complete.setEnabled(check)


    def filePreview(self):
        path_csv = self.dockwidget.lineEdit_file_complete.text()
        try:
            with open(path_csv, "r") as csv:
                text = csv.read()
        except (FileNotFoundError, OSError):
            text = "File doesn't exist"
            self.dockwidget.push_next_complete.setEnabled(False)
        except UnicodeDecodeError :
            text = "Unicode error"
            self.dockwidget.push_next_complete.setEnabled(False)
        finally:
            self.dockwidget.textEdit_preview.setText(text)


    def setupPage3(self):
        layer_source, layer_dest, path_csv = self.getSourceDestFile()
        layer_source.filter("")
        layer_dest.filter("")

        if (self.dockwidget.radio_w.isChecked()):
            field_source = self.dockwidget.source_comboBox_fields.currentText()
            field_dest = self.dockwidget.destination_comboBox_fields.currentText()

            self.dockwidget.source_label_field.setText(field_source + " :")
            self.dockwidget.destination_label_field.setText(field_dest + " :")

            line = "{};{}\n".format(field_source, field_dest)
            with open(path_csv, "w") as csv:
                csv.write(line)
        else:
            with open(path_csv, "r") as csv:
                header = csv.readline()

            header = header.split(";")
            label_source = header[0] + " :"
            label_dest = header[1]
            label_dest = label_dest[:-1] + " :"

            self.dockwidget.source_label_field.setText(label_source)
            self.dockwidget.destination_label_field.setText(label_dest)

        name = getNameFromPath(path_csv)
        QgsLayer.removeLayersByName(name)
        self.iface.addVectorLayer(path_csv, "", "ogr")

        layer_statement = layer_source.clone()

        layer_statement.setName("Statement_source")

        QgsLayer.removeLayersByName("Statement_source")

        layer_statement.add()

        layer_source.setVisibility(False)
        layer_dest.setVisibility(False)

        QgsLayer.styleByCSV(layer_statement, path_csv)
            

    def checkAutoButton(self):
        txt = self.dockwidget.source_lineEdit_fields.text()
        buffer_distance = self.dockwidget.buffer_lineEdit_distance.text()
        precision = self.dockwidget.precision_lineEdit.text()

        try:
            buffer_distance = int(buffer_distance)
            precision = int(precision)
        except ValueError:
            self.dockwidget.push_auto.setEnabled(False)
            print("Value have to be an integer")
        else:
            if (txt == ""):
                self.dockwidget.push_auto.setEnabled(False)
            else :
                self.dockwidget.push_auto.setEnabled(True)


    def checkFullAutoButton(self):
        buffer_distance = self.dockwidget.buffer_lineEdit_distance.text()
        precision = self.dockwidget.precision_lineEdit.text()

        try:
            buffer_distance = int(buffer_distance)
            precision = int(precision)
        except ValueError:
            self.dockwidget.push_fullauto.setEnabled(False)
            print("Value have to be an integer")
        else:
            self.dockwidget.push_fullauto.setEnabled(True)


    def checkAddButton(self):
        textEdit_source = self.dockwidget.source_lineEdit_fields.text()
        textEdit_dest = self.dockwidget.destination_lineEdit_fields.text()

        if ((textEdit_dest == "") or (textEdit_source == "")):
            self.dockwidget.push_add.setEnabled(False)
        else:
            self.dockwidget.push_add.setEnabled(True)


    def getSelectedEntity(self):
        layer_source, layer_dest, path_csv = self.getSourceDestFile()

        fields_source = ""
        fields_dest = ""

        if (layer_source is not None):
            label_source = self.dockwidget.source_label_field.text()[:-2]
            feats_source = layer_source.selectedFeatures()
            for f in feats_source:
                fields_source += str(f[label_source]) + ";"

        if (layer_dest is not None):
            label_dest = self.dockwidget.destination_label_field.text()[:-2]
            destination_feats = layer_dest.selectedFeatures()
            for f in destination_feats:
                fields_dest += str(f[label_dest]) + ";"

        fields_source = fields_source[:-1]
        fields_dest = fields_dest[:-1]

        if (fields_source != ""):
            self.dockwidget.source_lineEdit_fields.setText(fields_source)
        self.dockwidget.destination_lineEdit_fields.setText(fields_dest)       


    def addFields(self):
        layer_source, layer_dest, path_csv = self.getSourceDestFile()

        text_source = self.dockwidget.source_lineEdit_fields.text()
        text_dest = self.dockwidget.destination_lineEdit_fields.text()

        addLineCSV(path_csv, text_source, text_dest)

        self.dockwidget.source_lineEdit_fields.setText("")
        self.dockwidget.destination_lineEdit_fields.setText("")

        layer_source.setVisibility(False)
        layer_dest.setVisibility(False)
        createLayerStyleByCSV(path_csv)
        self.iface.mapCanvas().refreshAllLayers() 


    def getAutoDestinationFields(self):
        #Get data
        layer_source, layer_dest, path_csv = self.getSourceDestFile()

        field_source = self.dockwidget.source_label_field.text()[:-2]
        field_dest = self.dockwidget.destination_label_field.text()[:-2]

        source_value = self.dockwidget.source_lineEdit_fields.text()
        buffer_distance = int(self.dockwidget.buffer_lineEdit_distance.text())
        precision = float(self.dockwidget.precision_lineEdit.text())/100

        dest_value = getDestBySource(layer_source, layer_dest, source_value, field_source, field_dest, buffer_distance, precision)

        if (len(dest_value) == 0):
            isEmpty = True
        else:
            isEmpty = False

        #Create the line
        line = ""
        for value in dest_value:
            line += str(value) + ";"
        line = line[:-1]

        #Write line
        self.dockwidget.destination_lineEdit_fields.setText(line)

        #Filter
        expression_source = expressionFromFields(field_dest, line)
        expression_dest = expressionFromFields(field_source, source_value)

        #Change style
        destination_rules = (
            ("Destinations", expression_source, "blue"),
            ("Other", "ELSE", "darkBrown")
        )
        source_rules = (
            ("source", expression_dest, "magenta"),
            ("Other", "ELSE", "brown")
        )

        layer_dest.styleByRules(destination_rules)
        layer_source.styleByRules(source_rules)

        #Zoom
        layer_dest.filter(expression_source)
        layer_dest.zoom(self)

        #Hide statement
        layer_statement = QgsLayer.findLayerByName("Statement_source")
        layer_statement.setVisibility(False)

        layer_source.setVisibility(True)
        layer_dest.setVisibility(True)

        #Clear message
        if (isEmpty):
            layer_source.filter(expression_dest)
            layer_source.zoom(self)
            self.iface.messageBar().pushMessage("Done", "No destination found", level=1, duration=4)
        else:
            layer_dest.filter(expression_source)
            layer_dest.zoom(self)
            self.iface.messageBar().pushMessage("Done", "Destination found !", level=3, duration=4)

        #Clear filter 
        layer_source.filter("")
        layer_dest.filter("")


    def switch(self):
        layer_source, layer_dest, path_csv = self.getSourceDestFile()
        layer_statement = QgsLayer.findLayerByName("Statement_source")

        layers = [layer_source, layer_dest] 

        if (layer_source.isVisible()):
            visibility = False
        else:
            visibility = True

        for l in layers:
            l.setVisibility(visibility)

        layer_statement.setVisibility(not visibility)
        
        
    def showField(self):
        textEdit_dest = self.dockwidget.destination_lineEdit_fields
        field_source = self.dockwidget.source_label_field.text()[:-2]
        field_dest = self.dockwidget.destination_label_field.text()[:-2]
        field_source_value = self.sender().text()
        layer_source, layer_dest, path_csv = self.getSourceDestFile()

        with open(path_csv, "r") as csv:
            lines = csv.readlines()

        for line in lines:
            id = line.split("\"")[0]
            id = id[:-1]
            if (field_source_value == id):
                field_dest_value = line.split("\"")[1]
                textEdit_dest.setText(field_dest_value)

                expression_dest = "\"{}\" = {}".format(field_source, field_source_value)
                expression_source = "\"{}\" in ('{}')".format(field_dest, field_dest_value.replace(";", "','"))

                source_statement = QgsLayer.findLayerByName("Statement_source")

                source_statement.setVisibility(False)
                layer_source.setVisibility(True)
                layer_dest.setVisibility(True)

                layer_dest.filter(expression_source)
                layer_dest.zoom(self)
                layer_dest.filter("")

                layer_source.vector.selectByExpression(expression_dest)
                layer_dest.vector.selectByExpression(expression_source)
                return

        textEdit_dest.setText("")
    
    #--------------------------------------------------------------------------

    """Full auto function"""
    def startAlgo(self):
        layer_source, layer_dest, path_csv = self.getSourceDestFile()
        field_source = self.dockwidget.source_label_field.text()[:-2]
        field_dest = self.dockwidget.destination_label_field.text()[:-2]
        buffer_distance = int(self.dockwidget.buffer_lineEdit_distance.text())
        precision = float(self.dockwidget.precision_lineEdit.text())/100
        worker = Worker(layer_source, layer_dest, path_csv, field_source, field_dest, buffer_distance, precision)

        # configure the QgsMessageBar
        messageBar = self.iface.messageBar().createMessage('Running...', )
        progressBar = QProgressBar()
        progressBar.setAlignment(QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        cancelButton = QPushButton()
        cancelButton.setText('Cancel')
        cancelButton.clicked.connect(worker.kill)
        messageBar.layout().addWidget(progressBar)
        messageBar.layout().addWidget(cancelButton)
        self.iface.messageBar().pushWidget(messageBar)
        self.messageBar = messageBar

        # start the worker in a new thread
        thread = QtCore.QThread(self)
        worker.moveToThread(thread)
        worker.finished.connect(self.algoFinished)
        worker.error.connect(self.algoError)
        worker.progress.connect(progressBar.setValue)
        thread.started.connect(worker.run)
        thread.start()
        self.thread = thread
        self.worker = worker

    def algoFinished(self, layer):
        # clean up the worker and thread
        self.worker.deleteLater()
        self.thread.quit()
        self.thread.wait()
        self.thread.deleteLater()
        # remove widget from message bar
        self.iface.messageBar().popWidget(self.messageBar)
        if layer is not None:
            # report the result
            layer.zoom(self)
            self.iface.messageBar().pushMessage("Done", "Algorith is finished", level=3, duration=4)
        else:
            # notify the user that something went wrong
            self.iface.messageBar().pushMessage("Error", "Something went wrong... Check out the logs message for further informations", level=4, duration=4)

    def algoError(self, e, exception_string):
        QgsMessageLog.logMessage('Worker thread raised an exception: {} -- {}'.format(exception_string, e), level=Qgis.Critical)
    #--------------------------------------------------------------------------

    """Run"""
    def run(self):
        if not self.pluginIsActive:
            self.pluginIsActive = True

            #print "** STARTING DiagwayProjection"

            # dockwidget may not exist if:
            #    first run of plugin
            #    removed on close (see self.onClosePlugin method)
            if self.dockwidget == None:
                # Create the dockwidget (after translation) and keep reference
                self.dockwidget = DiagwayProjectionDockWidget()

                #Reset index layer
                self.dockwidget.source_comboBox_layers.setCurrentIndex(-1)
                self.dockwidget.destination_comboBox_layers.setCurrentIndex(-1)
                self.dockwidget.source_comboBox_layers_complete.setCurrentIndex(-1)
                self.dockwidget.destination_comboBox_layers_complete.setCurrentIndex(-1)

                #Filter for vector layer
                self.dockwidget.source_comboBox_layers.setFilters(QgsMapLayerProxyModel.VectorLayer)
                self.dockwidget.destination_comboBox_layers.setFilters(QgsMapLayerProxyModel.VectorLayer)
                self.dockwidget.source_comboBox_layers_complete.setFilters(QgsMapLayerProxyModel.VectorLayer)
                self.dockwidget.destination_comboBox_layers_complete.setFilters(QgsMapLayerProxyModel.VectorLayer)

                #Display fields of selected layers
                self.dockwidget.source_comboBox_layers.layerChanged.connect(lambda : self.fillFields(self.dockwidget.source_comboBox_fields))
                self.dockwidget.destination_comboBox_layers.layerChanged.connect(lambda : self.fillFields(self.dockwidget.destination_comboBox_fields))

                #Check before go to next step
                self.dockwidget.source_comboBox_layers.layerChanged.connect(self.checkAll)
                self.dockwidget.destination_comboBox_layers.layerChanged.connect(self.checkAll)
                self.dockwidget.lineEdit_file.textChanged.connect(self.checkAll)
                self.dockwidget.source_comboBox_layers_complete.layerChanged.connect(self.checkAll)
                self.dockwidget.destination_comboBox_layers_complete.layerChanged.connect(self.checkAll)
                self.dockwidget.lineEdit_file_complete.textChanged.connect(self.checkAll)

                #Connect buttons
                self.dockwidget.push_create.clicked.connect(lambda : self.dockwidget.stackedWidget.setCurrentIndex(1))
                self.dockwidget.push_complete.clicked.connect(lambda : self.dockwidget.stackedWidget.setCurrentIndex(2))
                self.dockwidget.push_create.clicked.connect(lambda : self.dockwidget.radio_w.setChecked(True))
                self.dockwidget.push_complete.clicked.connect(lambda : self.dockwidget.radio_a.setChecked(True))
                self.dockwidget.push_next.clicked.connect(lambda : self.dockwidget.stackedWidget.setCurrentIndex(3))
                self.dockwidget.push_next_complete.clicked.connect(lambda : self.dockwidget.stackedWidget.setCurrentIndex(3))
                self.dockwidget.push_cancel_create.clicked.connect(lambda : self.dockwidget.stackedWidget.setCurrentIndex(0))
                self.dockwidget.push_cancel_complete.clicked.connect(lambda : self.dockwidget.stackedWidget.setCurrentIndex(0))
                self.dockwidget.push_cancel_3.clicked.connect(lambda : self.dockwidget.stackedWidget.setCurrentIndex(0))
                self.dockwidget.push_file.clicked.connect(self.saveFile)
                self.dockwidget.push_file_complete.clicked.connect(self.selectFile)
                self.dockwidget.push_next.clicked.connect(self.setupPage3)
                self.dockwidget.push_next_complete.clicked.connect(self.setupPage3)
                self.dockwidget.push_add.clicked.connect(self.addFields)
                self.dockwidget.push_auto.clicked.connect(self.getAutoDestinationFields)
                self.dockwidget.push_fullauto.clicked.connect(self.startAlgo)
                self.dockwidget.push_switch.clicked.connect(self.switch)

                #Connect lineEdit
                self.dockwidget.lineEdit_file_complete.textChanged.connect(self.filePreview)
                self.dockwidget.buffer_lineEdit_distance.textChanged.connect(self.checkAutoButton)
                self.dockwidget.source_lineEdit_fields.textChanged.connect(self.checkAutoButton)
                self.dockwidget.precision_lineEdit.textChanged.connect(self.checkAutoButton)
                self.dockwidget.buffer_lineEdit_distance.textChanged.connect(self.checkFullAutoButton)
                self.dockwidget.precision_lineEdit.textChanged.connect(self.checkFullAutoButton)
                self.dockwidget.source_lineEdit_fields.textChanged.connect(self.checkAddButton)
                self.dockwidget.destination_lineEdit_fields.textChanged.connect(self.checkAddButton)
                self.dockwidget.source_lineEdit_fields.editingFinished.connect(self.showField)

                self.iface.mapCanvas().selectionChanged.connect(self.getSelectedEntity)

            #Set up the first page
            self.dockwidget.stackedWidget.setCurrentIndex(0)

            # connect to provide cleanup on closing of dockwidget
            self.dockwidget.closingPlugin.connect(self.onClosePlugin)

            # show the dockwidget
            # TODO: fix to allow choice of dock location
            self.iface.addDockWidget(Qt.RightDockWidgetArea, self.dockwidget)
            self.dockwidget.show()
