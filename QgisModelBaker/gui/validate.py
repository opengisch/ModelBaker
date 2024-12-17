"""
/***************************************************************************
                              -------------------
        begin                : 11/11/21
        git sha              : :%H$
        copyright            : (C) 2021 by Dave Signer
        email                : david at opengis ch
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

from PyQt5.QtGui import QColor
from qgis.core import QgsApplication
from qgis.gui import QgsGui
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import QDockWidget

from QgisModelBaker.libs.modelbaker.db_factory.db_simple_factory import DbSimpleFactory
from QgisModelBaker.libs.modelbaker.iliwrapper.ilivalidator import ValidationResultModel
from QgisModelBaker.utils import gui_utils

DIALOG_UI = gui_utils.get_ui_class("validator.ui")


# validate tools
class ValidationResultTableModel(ValidationResultModel):
    """
    Model providing the data of the parsed xtf file to the defined columns for the table view use.
    """

    def __init__(self, roles):
        super().__init__()
        self.roles = roles
        self.setColumnCount(len(self.roles))
        self.setHorizontalHeaderLabels([role.name for role in self.roles])

    def flags(self, index):
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def data(self, index, role):
        item = self.item(index.row(), 0)
        if item:
            if role == Qt.DisplayRole:
                return item.data(int(self.roles[index.column()]))
            if role == Qt.DecorationRole:
                return (
                    QColor(gui_utils.SUCCESS_COLOR)
                    if item.data(int(ValidationResultModel.Roles.FIXED))
                    else QColor(gui_utils.ERROR_COLOR)
                )
            if role == Qt.ToolTipRole:
                tooltip_text = "{type} at {tid} in {object}".format(
                    type=item.data(int(ValidationResultModel.Roles.TYPE)),
                    object=item.data(int(ValidationResultModel.Roles.OBJ_TAG)),
                    tid=item.data(int(ValidationResultModel.Roles.TID)),
                )
                return tooltip_text
            return item.data(role)

    def setFixed(self, index):
        item = self.item(index.row(), 0)
        if item:
            item.setData(
                not item.data(int(ValidationResultModel.Roles.FIXED)),
                int(ValidationResultModel.Roles.FIXED),
            )


class ValidateDock(QDockWidget, DIALOG_UI):
    def __init__(self, base_config, iface):
        QDockWidget.__init__(self, iface.mainWindow())
        self.setupUi(self)
        self.iface = iface
        self.base_config = base_config
        self.db_simple_factory = DbSimpleFactory()
        QgsGui.instance().enableAutoGeometryRestore(self)

        self.flash_button.setIcon(
            QgsApplication.getThemeIcon("/mActionHighlightFeature.svg")
        )
        self.auto_pan_button.setIcon(QgsApplication.getThemeIcon("/mActionPanTo.svg"))
        self.auto_zoom_button.setIcon(QgsApplication.getThemeIcon("/mActionZoomTo.svg"))
