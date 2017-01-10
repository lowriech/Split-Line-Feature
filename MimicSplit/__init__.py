# -*- coding: utf-8 -*-
"""
/***************************************************************************
 MimicSplit
                                 A QGIS plugin
 This plugin splits a line layer every 500 vertices, by feature
                             -------------------
        begin                : 2016-11-10
        copyright            : (C) 2016 by Chris Lowrie
        email                : lowriech@msu.edu
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load MimicSplit class from file MimicSplit.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .split_feature import MimicSplit
    return MimicSplit(iface)
