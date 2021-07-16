# -*- coding: utf-8 -*-
"""
/***************************************************************************
 SuppresionRoute
                                 A QGIS plugin
 supprime les routes déjà scanné
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2021-07-16
        copyright            : (C) 2021 by Cochet Quentin / Diagway
        email                : quentin.cochet@outlook.com
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
    """Load SuppresionRoute class from file SuppresionRoute.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .SuppresionRoute import SuppresionRoute
    return SuppresionRoute(iface)
