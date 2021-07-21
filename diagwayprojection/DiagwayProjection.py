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
from qgis.core import QgsMapLayerProxyModel

# Initialize Qt resources from file resources.py
from .resources import *

# Import the code for the DockWidget
from .DiagwayProjection_dockwidget import DiagwayProjectionDockWidget
from .Layer import QgsLayer
from .Worker import Worker
from .Tools import *


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
        return QCoreApplication.translate('DiagwayProjection', message)

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

        icon_path = ':/plugins/DiagwayProjection/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'DiagwayProjection'),
            callback=self.run,
            parent=self.iface.mainWindow())

    def onClosePlugin(self):
        """Cleanup necessary items here when plugin dockwidget is closed"""

        #print "** CLOSING DiagwayProjection"

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

        #print "** UNLOAD DiagwayProjection"

        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&DiagwayProjection'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar
    #--------------------------------------------------------------------------

    """Function for the algorithm"""
    #Create the path for the CSV file
    def saveFile(self):
        filename, _filter = QFileDialog.getSaveFileName(self.dockwidget, "Select output file ","", '*.csv')
        self.dockwidget.lineEdit_file.setText(filename)


    def selectFile(self):
        filename, _filter = QFileDialog.getOpenFileName(self.dockwidget, "Select output file ","", '*.csv')
        self.dockwidget.lineEdit_file_complete.setText(filename)


    def getSourceDestFile(self):
        if (self.dockwidget.radio_a.isChecked()):
            csv_path = self.dockwidget.lineEdit_file_complete.text()
            source_layer = self.dockwidget.source_comboBox_layers_complete.currentLayer()
            destination_layer = self.dockwidget.destination_comboBox_layers_complete.currentLayer()
        else:
            csv_path = self.dockwidget.lineEdit_file.text()
            source_layer = self.dockwidget.source_comboBox_layers.currentLayer()
            destination_layer = self.dockwidget.destination_comboBox_layers.currentLayer()

        source_layer = QgsLayer(vectorLayer=source_layer)
        destination_layer = QgsLayer(vectorLayer=destination_layer)
        
        return source_layer, destination_layer, csv_path

    #Filled the combo box fields
    def fillFields(self, comboBox):
        comboBox.clear()
        layer = self.dockwidget.sender().currentLayer()
        fields = layer.fields()
        for f in fields:
            comboBox.addItem(f.name())

    #Check if layer have lambert93 projection
    def isLayerLambert93(self):
        source_layer, destination_layer, csv_path = self.getSourceDestFile()

        if ((source_layer != None) and source_layer.isLT93()):
            self.dockwidget.source_img_warning.setHidden(False)
        if ((destination_layer != None) and destination_layer.isLT93()):
            self.dockwidget.destination_img_warning.setHidden(False)

    #Check if all box are correct
    def checkAll(self):
        source_layer, destination_layer, csv_path = self.getSourceDestFile()

        check = ((source_layer != destination_layer) and (source_layer != None) and (destination_layer != None) and (csv_path != "") and source_layer.isLT93() and destination_layer.isLT93())

        if (self.dockwidget.radio_w.isChecked()):
            self.dockwidget.push_next.setEnabled(check)
        else:
            self.dockwidget.push_next_complete.setEnabled(check)


    def filePreview(self):
        csv_path = self.dockwidget.lineEdit_file_complete.text()
        try:
            with open(csv_path, "r") as csv:
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
        source_layer, destination_layer, csv_path = self.getSourceDestFile()
        source_layer.filter("")
        destination_layer.filter("")

        if (self.dockwidget.radio_w.isChecked()):
            source_field = self.dockwidget.source_comboBox_fields.currentText()
            destination_field = self.dockwidget.destination_comboBox_fields.currentText()

            self.dockwidget.source_label_field.setText(source_field + " :")
            self.dockwidget.destination_label_field.setText(destination_field + " :")

            line = "{};{}\n".format(source_field, destination_field)
            with open(csv_path, "w") as csv:
                csv.write(line)
        else:
            with open(csv_path, "r") as csv:
                header = csv.readline()

            header = header.split(";")
            source_label = header[0] + " :"
            destination_label = header[1]
            destination_label = destination_label[:-1] + " :"

            self.dockwidget.source_label_field.setText(source_label)
            self.dockwidget.destination_label_field.setText(destination_label)

        name = getNameFromPath(csv_path)
        QgsLayer.removeLayersByName(name)
        self.iface.addVectorLayer(csv_path, "", "ogr")

        sourceStatement_layer = source_layer.clone()
        destinationStatement_layer = destination_layer.clone()

        sourceStatement_layer.setName("Statement_source")
        destinationStatement_layer.setName("Statement_destination")

        QgsLayer.removeLayersByName("Statement_source")
        QgsLayer.removeLayersByName("Statement_destination")

        sourceStatement_layer.add()
        destinationStatement_layer.add()

        source_layer.setVisibility(False)
        destination_layer.setVisibility(False)

        QgsLayer.styleByCSV(sourceStatement_layer, destinationStatement_layer, csv_path)
        source_layer.zoom(self)
            

    def checkAutoButton(self):
        txt = self.dockwidget.source_textEdit_fields.toPlainText()
        buffer_distance = self.dockwidget.buffer_lineEdit_distance.text()

        try:
            buffer_distance = int(buffer_distance)
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

        try:
            buffer_distance = int(buffer_distance)
        except ValueError:
            self.dockwidget.push_fullauto.setEnabled(False)
            print("Value have to be an integer")
        else:
            self.dockwidget.push_fullauto.setEnabled(True)


    def checkAddButton(self):
        source_textEdit = self.dockwidget.source_textEdit_fields.toPlainText()
        destination_textEdit = self.dockwidget.destination_textEdit_fields.toPlainText()

        if ((destination_textEdit == "") or (source_textEdit == "")):
            self.dockwidget.push_add.setEnabled(False)
        else:
            self.dockwidget.push_add.setEnabled(True)


    def getSelectedEntity(self):
        source_layer, destination_layer, csv_path = self.getSourceDestFile()

        source_fields = ""
        destination_fields = ""

        if (source_layer is not None):
            source_label = self.dockwidget.source_label_field.text()[:-2]
            source_feats = source_layer.selectedFeatures()
            for f in source_feats:
                source_fields += str(f[source_label]) + ";"

        if (destination_layer is not None):
            destination_label = self.dockwidget.destination_label_field.text()[:-2]
            destination_feats = destination_layer.selectedFeatures()
            for f in destination_feats:
                destination_fields += str(f[destination_label]) + ";"

        source_fields = source_fields[:-1]
        destination_fields = destination_fields[:-1]

        if (source_fields != ""):
            self.dockwidget.source_textEdit_fields.setText(source_fields)
        self.dockwidget.destination_textEdit_fields.setText(destination_fields)       


    def addFields(self):
        source_layer, destination_layer, csv_path = self.getSourceDestFile()

        source_text = self.dockwidget.source_textEdit_fields.toPlainText()
        destination_text = self.dockwidget.destination_textEdit_fields.toPlainText()

        addLineCSV(csv_path, source_text, destination_text)

        self.dockwidget.source_textEdit_fields.setText("")
        self.dockwidget.destination_textEdit_fields.setText("")

        source_layer.setVisibility(False)
        destination_layer.setVisibility(False)
        statementSource_layer, statementDestination_layer = createLayerStyleByCSV(csv_path)
        statementSource_layer.zoom(self)


    def getAutoDestinationFields(self):
        #Get data
        source_layer, destination_layer, csv_path = self.getSourceDestFile()

        source_field = self.dockwidget.source_label_field.text()[:-2]
        destination_field = self.dockwidget.destination_label_field.text()[:-2]

        source_value = self.dockwidget.source_textEdit_fields.toPlainText()
        buffer_distance = int(self.dockwidget.buffer_lineEdit_distance.text())

        destination_values = getDestBySource(source_layer, destination_layer, source_value, source_field, destination_field, buffer_distance)

        if (len(destination_values) == 0):
            isEmpty = True
        else:
            isEmpty = False

        #Create the line
        line = ""
        for value in destination_values:
            line += str(value) + ";"
        line = line[:-1]

        #Write line
        self.dockwidget.destination_textEdit_fields.setText(line)

        #Filter
        destination_expression = expressionFromFields(destination_field, line)
        source_expression = expressionFromFields(source_field, source_value)

        #Change style
        destination_rules = (
            ("Destinations", destination_expression, "blue"),
            ("Other", "ELSE", "brown")
        )
        source_rules = (
            ("source", source_expression, "magenta"),
            ("Other", "ELSE", "brown")
        )

        destination_layer.styleByRules(destination_rules)
        source_layer.styleByRules(source_rules)

        #Zoom
        destination_layer.filter(destination_expression)
        destination_layer.zoom(self)

        #Hide statement
        statementSource_layer = QgsLayer.findLayerByName("Statement_source")
        statementDestination_layer = QgsLayer.findLayerByName("Statement_destination")
        statementSource_layer.setVisibility(False)
        statementDestination_layer.setVisibility(False)

        source_layer.setVisibility(True)
        destination_layer.setVisibility(True)

        #Clear message
        if (isEmpty):
            source_layer.filter(source_expression)
            source_layer.zoom(self)
            self.iface.messageBar().pushMessage("Done", "No destination found", level=1, duration=4)
        else:
            destination_layer.filter(destination_expression)
            destination_layer.zoom(self)
            self.iface.messageBar().pushMessage("Done", "Destination found !", level=3, duration=4)

        #Clear filter 
        source_layer.filter("")
        destination_layer.filter("")


    def switch(self):
        source_layer, destination_layer, csv_path = self.getSourceDestFile()
        statementSource_layer = QgsLayer.findLayerByName("Statement_source")
        statementDestination_layer = QgsLayer.findLayerByName("Statement_destination")

        layers = [source_layer, destination_layer] 
        statements = [statementSource_layer, statementDestination_layer]

        if (source_layer.isVisible()):
            visibility = False
        else:
            visibility = True

        for l in layers:
            l.setVisibility(visibility)

        for l in statements:
            l.setVisibility(not visibility)
    #--------------------------------------------------------------------------

    """Full auto function"""
    def startAlgo(self):
        source_layer, destination_layer, csv_path = self.getSourceDestFile()
        source_field = self.dockwidget.source_label_field.text()[:-2]
        destination_field = self.dockwidget.destination_label_field.text()[:-2]
        worker = Worker(source_layer, destination_layer, csv_path, source_field, destination_field)

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
        QgsMessageLog.logMessage('Worker thread raised an exception:\n'.format(exception_string), level=Qgis.Critical)
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

                #Check the projection of layer
                self.dockwidget.source_comboBox_layers.layerChanged.connect(self.isLayerLambert93)
                self.dockwidget.destination_comboBox_layers.layerChanged.connect(self.isLayerLambert93)

                #Hide warning pic
                self.dockwidget.source_img_warning.setHidden(False)
                self.dockwidget.destination_img_warning.setHidden(False)

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

                #Connect textEdit
                self.dockwidget.source_textEdit_fields.textChanged.connect(self.checkAutoButton)
                self.dockwidget.source_textEdit_fields.textChanged.connect(self.checkAddButton)
                self.dockwidget.destination_textEdit_fields.textChanged.connect(self.checkAddButton)

                #Connect lineEdit
                self.dockwidget.lineEdit_file_complete.textChanged.connect(self.filePreview)
                self.dockwidget.buffer_lineEdit_distance.textChanged.connect(self.checkAutoButton)
                self.dockwidget.buffer_lineEdit_distance.textChanged.connect(self.checkFullAutoButton)

                self.iface.mapCanvas().selectionChanged.connect(self.getSelectedEntity)

            #Set up the first page
            self.dockwidget.stackedWidget.setCurrentIndex(0)

            # connect to provide cleanup on closing of dockwidget
            self.dockwidget.closingPlugin.connect(self.onClosePlugin)

            # show the dockwidget
            # TODO: fix to allow choice of dock location
            self.iface.addDockWidget(Qt.RightDockWidgetArea, self.dockwidget)
            self.dockwidget.show()
