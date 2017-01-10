# -*- coding: utf-8 -*-
"""
/***************************************************************************
 MimicSplit
                                 A QGIS plugin
 This plugin splits a line layer every 500 vertices, by feature
                              -------------------
        begin                : 2016-11-10
        git sha              : $Format:%H$
        copyright            : (C) 2016 by Chris Lowrie
        email                : lowriech@msu.edu
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
from PyQt4.QtGui import QAction, QIcon
# Initialize Qt resources from file resources.py
import resources
# Import the code for the dialog
from split_feature_dialog import MimicSplitDialog
import os.path
import math
from qgis.core import *
import processing
from PyQt4.QtCore import *
from PyQt4.QtGui import *

class MimicSplit:
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
        self.fileName = ""
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'MimicSplit_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)


        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Mimic Split Feature')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'MimicSplit')
        self.toolbar.setObjectName(u'MimicSplit')

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
        return QCoreApplication.translate('MimicSplit', message)


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
        self.dlg = MimicSplitDialog()

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
            self.iface.addPluginToVectorMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/MimicSplit/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Split feature every 5000 nodes'),
            callback=self.run,
            parent=self.iface.mainWindow())


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginVectorMenu(
                self.tr(u'&Mimic Split Feature'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar
    ####################################################################################################
    ####################################################################################################
    
    def extractAsSingle(self, geom):
        multiGeom = QgsGeometry()
        geometries = []
        if geom.type() == QGis.Point:
            if geom.isMultipart():
                multiGeom = geom.asMultiPoint()
                for part in multiGeom:
                    geometries.append(QgsGeometry().fromPoint(part))
            else:
                geometries.append(geom)
        elif geom.type() == QGis.Line:
            if geom.isMultipart():
                multiGeom = geom.asMultiPolyline()
                for part in multiGeom:
                    geometries.append(QgsGeometry().fromPolyline(part))
            else:
                geometries.append(geom)
        elif geom.type() == QGis.Polygon:
            if geom.isMultipart():
                multiGeom = geom.asMultiPolygon()
                for part in multiGeom:
                    geometries.append(QgsGeometry().fromPolygon(part))
            else:
                geometries.append(geom)
        return geometries

    def split_line_by_vertex(self, linestring, cutoff):
        geometries = []
        #print(linestring)
        points = linestring.asPolyline()
        point_count = len(points)
        quotient  = point_count / cutoff
        remainder = point_count % cutoff
        if quotient == 0:
        	print('x')
        	geometries.append((QgsGeometry.fromPolyline(points), remainder))
        else:
        	for idx in range(quotient):
        		print("Feature {} of {}".format(str(idx+1), quotient+1))
        		start = 0 if idx == 0 else (idx*cutoff)-1
        		#Case for last linestring
        		if quotient == idx:
        			if remainder == 1:
        				pass
        			elif remainder > 1:
        				to_append = QgsGeometry.fromPolyline(points[(idx*cutoff):point_count])
        				print(to_append)
        				geometries.append((to_append, remainder))
        			#Case for all other linestrings
        		else:
        			end = (idx+1)*cutoff
        			to_append = QgsGeometry.fromPolyline(points[start:end])
        			print(to_append)
        			geometries.append((to_append, 5000))     
        #print(geometries)
        return geometries

    def get_path(self):
        fileName = QFileDialog.getSaveFileName()
        if fileName[-5:-1] == '.shp':
            pass
        else:
            fileName = fileName + '.shp'
        
        self.dlg.path_lbl.setText(fileName)
        self.fileName = fileName


    def main(self, lineLayer, writer):
        Vertex_Count = 5000
        
        current = 0
        output_feature = QgsFeature()
        line_features = processing.features(lineLayer)
        total = 100.0 / float(len(line_features))
        for feature in line_features:
            geometries = self.extractAsSingle(feature.geometry())
            #print(type(geometries[0]))
            for geom in geometries:
                linestrings = self.split_line_by_vertex(geom, Vertex_Count)


                for linestring in linestrings:
                	print('x')
                	print(linestring[0])
                	print(linestring[1])
                	output_feature.setGeometry(linestring[0])
                	output_feature.setAttributes([linestring[1]])
                	writer.addFeature(output_feature)
                
    def check_type(self, layer):
    	provider = layer.dataProvider()
    	if not provider.geometryType() in (QGis.WKBLineString, QGis.WKBMultiLineString, QGis.WKBMultiLineString25D, QGis.WKBLineString25D):
    		return 0
    	else:
    		return 1


    def run(self):
        """Run method that performs all the real work"""
        # show the dialog
        layers = self.iface.legendInterface().layers()
        self.dlg.selectLayer.clear()
        layer_list = []
        for layer in layers:
            layer_list.append(layer.name())
        self.dlg.selectLayer.addItems(layer_list)
        self.dlg.path_btn.clicked.connect(self.get_path)
        
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            selectedLayerIndex = self.dlg.selectLayer.currentIndex()
            layer = layers[selectedLayerIndex]
            is_line = self.check_type(layer)
            if is_line:
            	field = QgsFields()
            	field.append(QgsField('Vertex Count', QVariant.Double))
            	writer = QgsVectorFileWriter(self.fileName, "CP1250", field, QGis.WKBLineString, None, "ESRI Shapefile")
            	self.main(layer, writer)
            else:
            	mw = self.iface.mainWindow()
            	QMessageBox.warning(mw, "Bad Layer Type", "Select a line layer")
