# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Limes
                                 A QGIS plugin
 This plugin download and show Roman military installations alongside the frontiers of the Roman Empire (Limes)
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2022-02-14
        git sha              : $Format:%H$
        copyright            : (C) 2022 by Václav FRÖHLICH / ENVIPARTNER, s.r.o. / Michal Dyčka
        email                : frohlich@envipartner.cz
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
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction

# Initialize Qt resources from file resources.py
from .resources import *
# Import the code for the dialog
from .Limes_dialog import LimesDialog
import os.path

from qgis.core import QgsProject, QgsVectorLayerCache, QgsMessageLog, QgsVectorLayer, QgsProcessingFeatureSourceDefinition, QgsFeatureRequest, QgsVectorFileWriter
from qgis.gui import QgsAttributeTableModel, QgsAttributeTableView, QgsAttributeTableFilterModel, QgsAttributeTableFilterModel

import processing
from processing.core.Processing import Processing
from qgis.core import Qgis

import sys
import os
import re

class Limes:
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
            'Limes_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&LIMES')

        # Check if plugin was started the first time in current QGIS session
        # Must be set in initGui() to survive plugin reloads
        self.first_start = None

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
        return QCoreApplication.translate('Limes', message)


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
            # Adds plugin icon to Plugins toolbar
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/Limes/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'LIMES'),
            callback=self.run,
            parent=self.iface.mainWindow())

        # will be set False in run()
        self.first_start = True


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&LIMES'),
                action)
            self.iface.removeToolBarIcon(action)

    def download_layer(self):
        try:
            self.downloaded_layer = processing.run("native:filedownloader", {'URL':'https://raw.githubusercontent.com/WencelFrohlich/limes/main/archeological_sites.geojson','OUTPUT':'TEMPORARY_OUTPUT'})['OUTPUT']
            self.iface.messageBar().pushMessage("LIMES plugin", "The layer of archeological sites was succesfully loaded in memory!", level=Qgis.Info, duration=3)
        except:
            sys.exit()

    def create_layer(self):
        self.layer = QgsVectorLayer(self.downloaded_layer, "source_layer","ogr")
        #QgsProject.instance().addMapLayer(self.layer)

    def filter_features(self):
        #QgsMessageLog.logMessage(str(self.dlg.expressionField.isValidExpression()))
        if self.dlg.expressionField.isValidExpression():
            self.layer.selectByExpression(self.dlg.expressionField.asExpression()) 
            self.dlg.textBrowser.setText(str(len(self.layer.selectedFeatures())) + ' sites')
            if len(self.layer.selectedFeatures()) > 0:
                self.dlg.button_box.buttons()[0].setEnabled(True)

    def save_result(self):
        QgsProject.instance().addMapLayer(self.layer)
        self.result = processing.run("native:savefeatures", 
        {'INPUT': QgsProcessingFeatureSourceDefinition(self.layer.id(), selectedFeaturesOnly=True, featureLimit=-1, geometryCheck=QgsFeatureRequest.GeometryAbortOnInvalid),
        'OUTPUT':'TEMPORARY_OUTPUT',
        'LAYER_NAME':'vysledek',
        'DATASOURCE_OPTIONS':'',
        'LAYER_OPTIONS':''}
        )
        result_layer = QgsVectorLayer(self.result['OUTPUT'], "filtered_sites","ogr")
        self.delete_attributes(result_layer)
        QgsProject.instance().addMapLayer(result_layer)
        QgsMessageLog.logMessage('LIMES plugin: {0}'.format(str("Data was added successfully")), level=Qgis.Info)

    def get_unique_values(self, attribute_name):
        unique_values = []
        #unique_values.append(None)
        index = self.layer.fields().indexOf(attribute_name)
        for value in self.layer.uniqueValues(index):
            if value:
                unique_values.append(value)
        return unique_values

    def get_splited_unique_values(self, attribute_name):
        unique_values = []
        index = self.layer.fields().indexOf(attribute_name)
        for value in self.layer.uniqueValues(index):
            if value:
                if ', ' not in value:
                    if value not in unique_values:
                        unique_values.append(value)
                else:
                    for splited in value.split(', '):
                        if splited not in unique_values:
                            unique_values.append(splited)
        return unique_values
    
    def check_coordinates(self, coordnatesString):
        if coordnatesString and coordnatesString != '' and re.match(r"^((\-?|\+?)?\d+(\.\d+)?),\s*((\-?|\+?)?\d+(\.\d+)?)$", coordnatesString):
            if float(coordnatesString.split(',')[0]) > -180 and float(coordnatesString.split(',')[0]) < 180 and float(coordnatesString.split(',')[1]) > -180 and float(coordnatesString.split(',')[1]) < 180:
                return True
            else:
                self.iface.messageBar().pushMessage("LIMES plugin", "The copied coordinates are not in CRS: 'EPSG:4326'.", level=Qgis.Info, duration=5)
        else:
            self.iface.messageBar().pushMessage("LIMES plugin", "The copied coordinates are not in the correct format. An example of the correct form is: -3.732708,52.413018 'EPSG:4326'.", level=Qgis.Critical, duration=8)
            return False
            

    def get_array_expression(self, array, attribute_name):
        if len(array) > 0:
            result = '"' + attribute_name + '"' + ' in ' + str(tuple(i for i in array))
            result = result.replace("',)", "')")
            return result
        else:
            return '"' + attribute_name + '" is not null'

    def get_splited_array_expression(self, array, attribute_name):
        if len(array) > 0:
            result = []
            for value in array:
                result.append('"' + attribute_name + '" ilike ' + "'%" + value + "%'")
            return " OR ".join(result)
        else:
            return '"' + attribute_name + '" is not null'
    
    def get_text_expression(self, text, attribute_name):
        if text != '':
            return '"' + attribute_name + '" ilike ' + "'%" +  str(text).lower() + "%'"
        else:
            return '"' + attribute_name + '" is not null' 

    def get_number_expression(self, number, attribute_name):
        if number == 0 or number == 0.001 or str(number) == '0':
            return '"' + attribute_name + '" is not null' 
        else:
            return '"' + attribute_name + '" ' + str(self.get_operator(attribute_name)) + ' ' +  str(round(number, 3))
        
    def get_coordinates(self, coordinatesString):
        QgsMessageLog.logMessage('LIMES plugin: {0}'.format(str("number: {0}".format(self.dlg.spinBoxBufferSize.value()))), level=Qgis.Info)
        if self.check_coordinates(coordinatesString) and self.dlg.spinBoxBufferSize.value() * 1000 != 0:
            return "intersects(buffer(transform(make_point($x, $y), 'EPSG:4326', 'EPSG:3857'), {1}),transform(make_point({0}), 'EPSG:4326', 'EPSG:3857'))".format(
                coordinatesString, 
                self.dlg.spinBoxBufferSize.value() * 1000
            )
        else:
            return '"$geometry" is not null' 

    def get_general_search(self, text):
        attributes = ['Ort', 'Antiker Name', 'Klassifikation', 'Besatzung_Einheit']
        expressions = []
        if text != '':
            for attribute in attributes:
                expressions.append('"' + attribute + '" ilike ' + "'%" +  str(text).lower() + "%'")
            return " OR ".join(expressions)
        else:
            return ''

    def get_operator(self, attribute_name):
        if attribute_name == 'Anfang_Min':
            if self.dlg.radioButtonAnfangMinLessOrEqual.isChecked():
                return '<='
            elif self.dlg.radioButtonAnfangMinMoreOrEqual.isChecked():
                return '>='
            elif self.dlg.radioButtonAnfangMinNotEqual.isChecked():
                return '!='
            elif self.dlg.radioButtonAnfangMinEqual.isChecked():
                return '='
        elif attribute_name == 'Anfang_Max':
            if self.dlg.radioButtonAnfangMaxLessOrEqual.isChecked():
                return '<='
            elif self.dlg.radioButtonAnfangMaxMoreOrEqual.isChecked():
                return '>='
            elif self.dlg.radioButtonAnfangMaxNotEqual.isChecked():
                return '!='
            elif self.dlg.radioButtonAnfangMaxEqual.isChecked():
                return '='
        elif attribute_name == 'Ende_Min':
            if self.dlg.radioButtonEndeMinLessOrEqual.isChecked():
                return '<='
            elif self.dlg.radioButtonEndeMinMoreOrEqual.isChecked():
                return '>='
            elif self.dlg.radioButtonEndeMinNotEqual.isChecked():
                return '!='
            elif self.dlg.radioButtonEndeMinEqual.isChecked():
                return '='
        elif attribute_name == 'Ende_Max':
            if self.dlg.radioButtonEndeMaxLessOrEqual.isChecked():
                return '<='
            elif self.dlg.radioButtonEndeMaxMoreOrEqual.isChecked():
                return '>='
            elif self.dlg.radioButtonEndeMaxNotEqual.isChecked():
                return '!='
            elif self.dlg.radioButtonEndeMaxEqual.isChecked():
                return '='
        elif attribute_name == 'Grosse_in_Hektar':
            if self.dlg.radioButtonGrosseLessOrEqual.isChecked():
                return '<='
            elif self.dlg.radioButtonGrosseMoreOrEqual.isChecked():
                return '>='
            elif self.dlg.radioButtonGrosseNotEqual.isChecked():
                return '!='
            elif self.dlg.radioButtonGrosseEqual.isChecked():
                return '='
        elif attribute_name == 'Annex_in_Hektar':
            if self.dlg.radioButtonAnnexLessOrEqual.isChecked():
                return '<='
            elif self.dlg.radioButtonAnnexMoreOrEqual.isChecked():
                return '>='
            elif self.dlg.radioButtonAnnexNotEqual.isChecked():
                return '!='
            elif self.dlg.radioButtonAnnexEqual.isChecked():
                return '='                
        else:
            return '='

    
    def clean_expression(self):
        result = []
        conditions = str(self.expression).split('AND')
        for condition in conditions:
            if 'is not null' not in condition:
                result.append(condition) 
        return ' AND '.join(result)   

    def create_general_search_expression(self):
        self.expression = self.get_general_search(self.dlg.mLineGenaralSearch.value())
        self.dlg.expressionField.setExpression(self.clean_expression())

    def create_expression(self):
        self.expression = ''        
        #self.expression = "{0} AND {1} AND {2} AND {3} AND {4} AND {5} AND {6} AND {7} AND {8} AND {9} AND {10} AND {11} AND {12} AND {13} AND {14} AND {15} AND {16} AND {17} AND {18} AND {19}".format(
        self.expression = "{0} AND {1} AND {2} AND {3} AND {4} AND {5} AND {6} AND {7} AND {8} AND {9} AND {10} AND {11} AND {12} AND {13} AND {14} AND {15} AND {16} AND {17} AND {18}".format(
            self.get_text_expression(self.dlg.mLineEditOrt.value(), 'Ort'),
            self.get_array_expression(self.dlg.comboxBoxProvinz.checkedItems(), 'Provinz'),
            self.get_text_expression(self.dlg.mLineEditAntiker_Name.value(), 'Antiker_Name'),
            self.get_number_expression(self.dlg.spinBoxGrosseInHektar.value(), 'Grosse_in_Hektar'),
            self.get_array_expression(self.dlg.comboxBoxUmwehrung.checkedItems(), 'Umwehrung'),
            self.get_array_expression(self.dlg.comboBoxAnnex.checkedItems(), 'Annex'),
            self.get_number_expression(self.dlg.spinBoxAnnexInHektar.value(), 'Annex_in_Hektar'),
            self.get_array_expression(self.dlg.comboBoxLimes.checkedItems(), 'Limes'),
            self.get_text_expression(self.dlg.mLineEditKlassifikation.value(), 'Klassifikation'),
            self.get_array_expression(self.dlg.comboBoxObjekt.checkedItems(), 'Objekt'),
            self.get_array_expression(self.dlg.comboBoxAnfang_Genauigkeit.checkedItems(), 'Anfang_Genauigkeit_text'),
            self.get_number_expression(self.dlg.spinBoxAnfang_Min.value(), 'Anfang_Min'),
            self.get_number_expression(self.dlg.spinBoxAnfang_Max.value(), 'Anfang_Max'),
            self.get_array_expression(self.dlg.comboBoxEnde_Genauigkeit.checkedItems(), 'Ende_Genauigkeit_text'),
            self.get_number_expression(self.dlg.spinBoxEndeMin.value(), 'Ende_Min'),
            self.get_number_expression(self.dlg.spinBoxEndeMax.value(), 'Ende_Max'),
            self.get_splited_array_expression(self.dlg.comboBoxBesatzung.checkedItems(), 'Besatzung'),
            self.get_text_expression(self.dlg.mLineEditBesatzung_Einheit.value(), 'Besatzung_Einheit'),
            self.get_coordinates(self.dlg.mLineEditCoordinates.value())
            
        )
        #QgsMessageLog.logMessage(str(self.expression))
        self.dlg.expressionField.setExpression(self.clean_expression())

    def init_inputs(self, dialog):
        self.dlg.mLineEditCoordinates.valueChanged.connect(lambda: self.create_expression())
        self.dlg.spinBoxBufferSize.valueChanged.connect(lambda: self.create_expression())
        
        self.dlg.comboxBoxProvinz.addItems(self.get_unique_values('Provinz'))
        self.dlg.comboxBoxProvinz.checkedItemsChanged.connect(lambda: self.create_expression())
        self.dlg.mLineGenaralSearch.valueChanged.connect(lambda: self.create_general_search_expression())
        self.dlg.mLineEditOrt.valueChanged.connect(lambda: self.create_expression())
        self.dlg.mLineEditAntiker_Name.valueChanged.connect(lambda: self.create_expression())
        self.dlg.spinBoxGrosseInHektar.valueChanged.connect(lambda: self.create_expression())
        self.dlg.comboxBoxUmwehrung.addItems(self.get_unique_values('Umwehrung'))
        self.dlg.comboxBoxUmwehrung.checkedItemsChanged.connect(lambda: self.create_expression())
        self.dlg.comboBoxAnnex.addItems(self.get_unique_values('Annex'))
        self.dlg.comboBoxAnnex.checkedItemsChanged.connect(lambda: self.create_expression())
        self.dlg.spinBoxAnnexInHektar.valueChanged.connect(lambda: self.create_expression())
        self.dlg.comboBoxLimes.addItems(self.get_unique_values('Limes'))
        self.dlg.comboBoxLimes.checkedItemsChanged.connect(lambda: self.create_expression())
        self.dlg.mLineEditKlassifikation.valueChanged.connect(lambda: self.create_expression())
        self.dlg.comboBoxObjekt.addItems(self.get_unique_values('Objekt'))
        self.dlg.comboBoxObjekt.checkedItemsChanged.connect(lambda: self.create_expression())
        self.dlg.comboBoxAnfang_Genauigkeit.addItems(self.get_unique_values('Anfang_Genauigkeit_text'))
        self.dlg.comboBoxAnfang_Genauigkeit.checkedItemsChanged.connect(lambda: self.create_expression())
        self.dlg.spinBoxAnfang_Min.valueChanged.connect(lambda: self.create_expression())
        self.dlg.spinBoxAnfang_Max.valueChanged.connect(lambda: self.create_expression())
        self.dlg.comboBoxEnde_Genauigkeit.addItems(self.get_unique_values('Ende_Genauigkeit_text'))
        self.dlg.comboBoxEnde_Genauigkeit.checkedItemsChanged.connect(lambda: self.create_expression())#spinBoxAnfang_Min
        self.dlg.spinBoxEndeMin.valueChanged.connect(lambda: self.create_expression())#spinBoxAnfang_Min
        self.dlg.spinBoxEndeMax.valueChanged.connect(lambda: self.create_expression())#spinBoxAnfang_Min
        self.dlg.comboBoxBesatzung.addItems(self.get_splited_unique_values('Besatzung'))
        self.dlg.comboBoxBesatzung.checkedItemsChanged.connect(lambda: self.create_expression())
        self.dlg.mLineEditBesatzung_Einheit.valueChanged.connect(lambda: self.create_expression())

        self.dlg.radioButtonAnfangMinLessOrEqual.toggled.connect(lambda: self.create_expression())
        self.dlg.radioButtonAnfangMinMoreOrEqual.toggled.connect(lambda: self.create_expression())
        self.dlg.radioButtonAnfangMinNotEqual.toggled.connect(lambda: self.create_expression())
        self.dlg.radioButtonAnfangMinEqual.toggled.connect(lambda: self.create_expression())
        self.dlg.radioButtonAnfangMaxLessOrEqual.toggled.connect(lambda: self.create_expression())
        self.dlg.radioButtonAnfangMaxMoreOrEqual.toggled.connect(lambda: self.create_expression())
        self.dlg.radioButtonAnfangMaxNotEqual.toggled.connect(lambda: self.create_expression())
        self.dlg.radioButtonAnfangMaxEqual.toggled.connect(lambda: self.create_expression())
        self.dlg.radioButtonEndeMinLessOrEqual.toggled.connect(lambda: self.create_expression())
        self.dlg.radioButtonEndeMinMoreOrEqual.toggled.connect(lambda: self.create_expression())
        self.dlg.radioButtonEndeMinNotEqual.toggled.connect(lambda: self.create_expression())
        self.dlg.radioButtonEndeMinEqual.toggled.connect(lambda: self.create_expression())
        self.dlg.radioButtonEndeMaxLessOrEqual.toggled.connect(lambda: self.create_expression())
        self.dlg.radioButtonEndeMaxMoreOrEqual.toggled.connect(lambda: self.create_expression())
        self.dlg.radioButtonEndeMaxNotEqual.toggled.connect(lambda: self.create_expression())
        self.dlg.radioButtonEndeMaxEqual.toggled.connect(lambda: self.create_expression())
        self.dlg.radioButtonGrosseLessOrEqual.toggled.connect(lambda: self.create_expression())
        self.dlg.radioButtonGrosseMoreOrEqual.toggled.connect(lambda: self.create_expression())
        self.dlg.radioButtonGrosseNotEqual.toggled.connect(lambda: self.create_expression())
        self.dlg.radioButtonGrosseEqual.toggled.connect(lambda: self.create_expression())
        self.dlg.radioButtonAnnexLessOrEqual.toggled.connect(lambda: self.create_expression())
        self.dlg.radioButtonAnnexMoreOrEqual.toggled.connect(lambda: self.create_expression())
        self.dlg.radioButtonAnnexNotEqual.toggled.connect(lambda: self.create_expression())
        self.dlg.radioButtonAnnexEqual.toggled.connect(lambda: self.create_expression())

    def delete_attributes(self, layer):
        attributes = ['Id', 'Anfang_Genauigkeit', 'Ende_Genauigkeit']
        for attribute in attributes:
            self.delete_attribute(layer, attribute)

    def delete_attribute(self, layer, attribute_name):
        layer.startEditing()
        my_field = layer.fields().indexFromName(attribute_name)
        layer.dataProvider().deleteAttributes([my_field])
        layer.updateFields()
        layer.commitChanges()
        
    def run(self):
        """Run method that performs all the real work"""

        # Create the dialog with elements (after translation) and keep reference
        # Only create GUI ONCE in callback, so that it will only load when the plugin is started

        self.download_layer()
        self.create_layer()
        #if self.first_start == True:
        #    self.first_start = False
        self.dlg = LimesDialog()

        # show the dialog
        self.init_inputs(self.dlg)
        self.dlg.expressionField.setLayer(self.layer)
        self.dlg.filterButton.clicked.connect(lambda *args: self.filter_features())
        self.dlg.button_box.accepted.connect(lambda *args: self.save_result())
        self.dlg.button_box.buttons()[0].setEnabled(False)
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            # Do something useful here - delete the line containing pass and
            # substitute with your code.
            QgsProject.instance().removeMapLayers( [self.layer.id()] )
            QgsMessageLog.logMessage('Closing plugin: Limes', level=Qgis.Info)
            del self.dlg
            self.first_start = True
