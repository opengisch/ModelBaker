# -*- coding: utf-8 -*-
"""
/***************************************************************************
                              -------------------
        begin                : 06.07.2021
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

from enum import Enum
import os
from PyQt5.QtCore import pyqtSignal

from PyQt5.QtWidgets import QGridLayout, QToolButton
from PyQt5.uic.uiparser import _parse_alignment

from qgis.PyQt.QtWidgets import (
    QWizardPage,
    QHeaderView,
    QStyledItemDelegate,
    QComboBox,
    QAction,
    QWidget,
    QHBoxLayout,
    QStyle,
    QStyleOptionComboBox,
    QApplication,
    QLayout,
    QFrame
)

from qgis.PyQt.QtGui import (
    QIcon,
    QStandardItemModel,
    QStandardItem
)

from qgis.PyQt.QtCore import (
    Qt,
    QVariant
)

from ...libqgsprojectgen.db_factory.db_simple_factory import DbSimpleFactory
from ...libqgsprojectgen.dbconnector.db_connector import DBConnectorError
from QgisModelBaker.gui.panel.log_panel import LogPanel

from QgisModelBaker.gui.ili2db_options import Ili2dbOptionsDialog

from ...utils import get_ui_class

PAGE_UI = get_ui_class('workflow_wizard/import_data_configuration.ui')

DEFAULT_DATASETNAME = "defaultdataset"
class SourceModel(QStandardItemModel):

    print_info = pyqtSignal([str], [str, str])
    class Roles(Enum):
        NAME = Qt.UserRole + 1
        TYPE = Qt.UserRole + 2
        PATH = Qt.UserRole + 3
        DATASET_NAME = Qt.UserRole + 5

        def __int__(self):
            return self.value

    def __init__(self):
        super().__init__()
        self.setColumnCount(2)

    def flags(self, index):
        if index.column() > 0:
            return Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled

    def headerData(self, section, orientation, role):
        if orientation == Qt.Vertical and role == Qt.DisplayRole:
            return "↑ ↓"
        return QStandardItemModel.headerData(self, section,orientation,role)

    def data(self, index, role):
        item = self.item(index.row(), index.column())
        if role == Qt.DisplayRole:
            if index.column() > 0:
                return item.data(int(SourceModel.Roles.DATASET_NAME))
            if item.data(int(SourceModel.Roles.TYPE)) != 'model':
                return self.tr('{} ({})').format(item.data(int(Qt.DisplayRole)), item.data(int(SourceModel.Roles.PATH)))
        if role == Qt.DecorationRole:
            if index.column() == 0:
                type = 'data'
                if item.data(int(SourceModel.Roles.TYPE)) and item.data(int(SourceModel.Roles.TYPE)).lower() in ['model','ili', 'xtf', 'xml']:
                    type = item.data(int(SourceModel.Roles.TYPE)).lower()
                return QIcon(os.path.join(os.path.dirname(__file__), f'../../images/file_types/{type}.png'))
        return item.data(int(role))

    def add_source(self, name, type, path):
        if self.source_in_model(name, type, path):
            self.print_info.emit(self.tr("Source alread added {} ({})").format(
                name, path if path else 'repository'))
            return

        item = QStandardItem()
        item.setData(name, int(Qt.DisplayRole))
        item.setData(name, int(SourceModel.Roles.NAME))
        item.setData(type, int(SourceModel.Roles.TYPE))
        item.setData(path, int(SourceModel.Roles.PATH))
        self.appendRow([item, QStandardItem()])

        self.print_info.emit(self.tr("Add source {} ({})").format(
            name, path if path else 'repository'))

    def source_in_model(self, name, type, path):
        match_existing = self.match(self.index(
            0, 0), SourceModel.Roles.NAME, name, -1, Qt.MatchExactly)
        if match_existing and type == match_existing[0].data(int(SourceModel.Roles.TYPE)) and path == match_existing[0].data(int(SourceModel.Roles.PATH)):
            return True
        return False

    def setData(self, index, data, role):
        if index.column() > 0:
            return QStandardItemModel.setData(self, index, data, int(SourceModel.Roles.DATASET_NAME))
        return QStandardItemModel.setData(self, index, data, role)

    def remove_sources(self, indices):
        for index in sorted(indices):
            path = index.data(int(SourceModel.Roles.PATH))
            self.print_info.emit(self.tr("Remove source {} ({})").format(
                index.data(int(SourceModel.Roles.NAME)), path if path else 'repository'))
            self.removeRow(index.row())

class DatasetComboDelegate(QStyledItemDelegate):
    def __init__(self, parent, db_connector):
        super().__init__(parent)
        self.refresh_datasets(db_connector)
    def refresh_datasets(self, db_connector):
        datasets_info = db_connector.get_datasets_info()
        self.items = [record['datasetname'] for record in datasets_info]
    def createEditor(self, parent, option, index):
        self.editor = QComboBox(parent)
        self.editor.addItems(self.items)
        return self.editor
    def setEditorData(self, editor, index):
        value = index.data(int(SourceModel.Roles.DATASET_NAME))
        if value:
            num = self.items.index(value)
            editor.setCurrentIndex(num)
    def setModelData(self, editor, model, index):
        value = editor.currentText()
        model.setData(index, value, int(SourceModel.Roles.DATASET_NAME))
    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)
class ImportDataConfigurationPage(QWizardPage, PAGE_UI):
    def __init__(self, parent, title):
        QWizardPage.__init__(self, parent)
        self.workflow_wizard = parent

        self.setupUi(self)
        self.setMinimumSize(600, 500)
        self.setTitle(title)

        self.workflow_wizard = parent

        self.workflow_wizard.import_data_file_model.sourceModel(
        ).setHorizontalHeaderLabels([self.tr('Import File'), self.tr('Dataset')])
        self.file_table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.file_table_view.setModel(
            self.workflow_wizard.import_data_file_model)
        self.file_table_view.verticalHeader().setSectionsMovable(True)
        self.file_table_view.verticalHeader().setDragEnabled(True)
        self.file_table_view.verticalHeader().setDragDropMode(QHeaderView.InternalMove)
            
        self.ili2db_options = Ili2dbOptionsDialog()
        self.ili2db_options_button.clicked.connect(self.ili2db_options.open)
        self.ili2db_options.finished.connect(self.fill_toml_file_info_label)

    def order_list(self):
        order_list = []
        for visual_index in range(0, self.file_table_view.verticalHeader().count()):
            order_list.append(
                self.file_table_view.verticalHeader().logicalIndex(visual_index))
        return order_list

    def fill_toml_file_info_label(self):
        text = None
        if self.ili2db_options.toml_file():
            text = self.tr('Extra Model Information File: {}').format(('…'+self.ili2db_options.toml_file()[len(
                self.ili2db_options.toml_file())-40:]) if len(self.ili2db_options.toml_file()) > 40 else self.ili2db_options.toml_file())
        self.toml_file_info_label.setText(text)
        self.toml_file_info_label.setToolTip(self.ili2db_options.toml_file())

    def restore_configuration(self):
        # takes settings from QSettings and provides it to the gui (not the configuration)
        # since delete data should be turned off the only left thingy is the toml-file
        self.fill_toml_file_info_label()
        # set chk_delete_data always to unchecked because otherwise the user could delete the data accidentally
        self.chk_delete_data.setChecked(False)

        # setup dataset handling
        db_connector = self._get_db_connector(self.workflow_wizard.import_data_configuration)
        if db_connector.get_basket_handling():
            # fill up the dataset combobox
            self.file_table_view.setItemDelegateForColumn(1, DatasetComboDelegate(self, db_connector))
            # set defaults
            for row in range( self.workflow_wizard.import_data_file_model.rowCount() ):
                index = self.workflow_wizard.import_data_file_model.index(row, 1)
                value = index.data(int(SourceModel.Roles.DATASET_NAME))
                if not value:
                    self.workflow_wizard.import_data_file_model.setData(index, DEFAULT_DATASETNAME, int(SourceModel.Roles.DATASET_NAME))
        else:
            self.file_table_view.setColumnHidden(1, True)

    def update_configuration(self, configuration):
        # takes settings from the GUI and provides it to the configuration
        configuration.delete_data = self.chk_delete_data.isChecked()
        # ili2db_options
        configuration.inheritance = self.ili2db_options.inheritance_type()
        configuration.tomlfile = self.ili2db_options.toml_file()
        configuration.create_basket_col = self.ili2db_options.create_basket_col()
        configuration.create_import_tid = self.ili2db_options.create_import_tid()
        configuration.stroke_arcs = self.ili2db_options.stroke_arcs()
        configuration.pre_script = self.ili2db_options.pre_script()
        configuration.post_script = self.ili2db_options.post_script()

    def nextId(self):
        return self.workflow_wizard.next_id()

    def _get_db_connector(self, configuration):
        # migth be moved to db_utils...
        db_simple_factory = DbSimpleFactory()
        schema = configuration.dbschema

        db_factory = db_simple_factory.create_factory(configuration.tool)
        config_manager = db_factory.get_db_command_config_manager(configuration)
        uri_string = config_manager.get_uri(configuration.db_use_super_login)

        try:
            return db_factory.get_db_connector(uri_string, schema)
        except (DBConnectorError, FileNotFoundError):
            return None