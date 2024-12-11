"""
/***************************************************************************
                              -------------------
        begin                : 26.08.2024
        git sha              : :%H$
        copyright            : (C) 2024 by Germán Carrillo
        email                : german at opengis ch
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

from qgis.core import Qgis, QgsApplication, QgsMessageLog, QgsProject
from qgis.PyQt.QtWidgets import QDialog, QMessageBox

from QgisModelBaker.gui.create_baskets import CreateBasketDialog
from QgisModelBaker.gui.edit_basket import EditBasketDialog
from QgisModelBaker.gui.panel.summary_basket_panel import SummaryBasketPanel
from QgisModelBaker.libs.modelbaker.iliwrapper.ili2dbconfig import (
    Ili2DbCommandConfiguration,
)
from QgisModelBaker.libs.modelbaker.utils.ili2db_utils import Ili2DbUtils
from QgisModelBaker.utils import gui_utils

DIALOG_UI = gui_utils.get_ui_class("basket_manager.ui")


class BasketManagerDialog(QDialog, DIALOG_UI):
    def __init__(
        self,
        iface,
        parent=None,
        db_connector=None,
        datasetname=None,
        configuration: Ili2DbCommandConfiguration = None,
    ):
        QDialog.__init__(self, parent)
        self.setupUi(self)

        self.iface = iface
        self.datasetname = datasetname
        self.db_connector = db_connector
        self.configuration = configuration

        self.buttonBox.accepted.connect(self.accept)

        # baskets part
        self.baskets_panel = SummaryBasketPanel(self)
        self.baskets_layout.addWidget(self.baskets_panel)
        self.baskets_panel.basket_view.doubleClicked.connect(self._edit_basket)

        self.baskets_panel.load_basket_config(self.db_connector, self.datasetname)

        self.add_button.clicked.connect(self._add_basket)
        self.edit_button.clicked.connect(self._edit_basket)
        self.delete_button.clicked.connect(self._delete_basket)
        self.baskets_panel.basket_view.selectionModel().selectionChanged.connect(
            lambda: self._enable_basket_handling(True)
        )

        self.add_button.setIcon(QgsApplication.getThemeIcon("/symbologyAdd.svg"))
        self.edit_button.setIcon(QgsApplication.getThemeIcon("/symbologyEdit.svg"))
        self.delete_button.setIcon(QgsApplication.getThemeIcon("/symbologyRemove.svg"))

        self._enable_basket_handling(True)  # Initial widget status

    def _enable_basket_handling(self, enable):
        self.add_button.setEnabled(enable)
        self.edit_button.setEnabled(self._valid_selection())
        self.delete_button.setEnabled(self._valid_selection())

    def _valid_selection(self):
        """
        Returns if at least one dataset is selected
        """
        return bool(self.baskets_panel.basket_view.selectedIndexes())

    def _refresh_baskets(self):
        self.baskets_panel.bid_model.load_basket_config(
            self.db_connector, self.datasetname
        )
        self._enable_basket_handling(True)

    def _add_basket(self):
        create_basket_dialog = CreateBasketDialog(
            self, self.db_connector, self.datasetname
        )
        if create_basket_dialog.baskets_can_be_created():
            create_basket_dialog.exec_()

            # Refresh existing baskets in basket manager after creation
            self._refresh_baskets()
        else:
            QMessageBox.information(
                self,
                self.tr("Create Baskets"),
                self.tr(
                    f"The dataset '{self.datasetname}' already contains one basket for each topic.\n\n"
                    f"No additional baskets can be created."
                ),
                QMessageBox.Close,
            )

    def _edit_basket(self) -> None:
        if self._valid_selection():
            selected_basket_settings = self.baskets_panel.selected_basket_settings()
            edit_basket_dialog = EditBasketDialog(
                self, self.db_connector, selected_basket_settings
            )
            edit_basket_dialog.exec_()

            # Refresh existing baskets in basket manager after edition
            self._refresh_baskets()

    def _delete_basket(self) -> None:
        if self._valid_selection():
            if not self.db_connector.get_basket_handling():
                QMessageBox.warning(
                    self,
                    self.tr("Delete Basket"),
                    self.tr(
                        "Delete baskets is only available for database schemas created with --createBasketCol parameter."
                    ),
                    QMessageBox.Close,
                )
                return

            if (
                QMessageBox.warning(
                    self,
                    self.tr("Delete Basket"),
                    self.tr(
                        "Deleting a Basket will also delete all the data it contains. This operation cannot be reverted.\n\nAre you sure you want to proceed?"
                    ),
                    QMessageBox.No | QMessageBox.Yes,
                )
                == QMessageBox.Yes
            ):
                basket_config = self.baskets_panel.selected_basket_settings()
                ili2db_utils = Ili2DbUtils()
                ili2db_utils.log_on_error.connect(self._log_on_delete_baskets_error)
                res, msg = ili2db_utils.delete_baskets(
                    basket_config["bid_value"], self.configuration
                )

                if res:
                    # After deletion, make sure canvas is refreshed
                    self._refresh_map_layers()

                    # Refresh existing baskets in basket manager after deletion
                    self._refresh_baskets()

                warning_box = QMessageBox(self)
                warning_box.setIcon(
                    QMessageBox.Information if res else QMessageBox.Warning
                )
                warning_box.setWindowTitle(self.tr("Delete Basket"))
                warning_box.setText(msg)
                warning_box.exec_()

    def _refresh_map_layers(self):
        # Refresh layer data sources and also their symbology (including feature count)
        layer_tree_view = self.iface.layerTreeView()
        for tree_layer in QgsProject.instance().layerTreeRoot().findLayers():
            layer = tree_layer.layer()
            layer.dataProvider().reloadData()
            layer_tree_view.refreshLayerSymbology(layer.id())

    def _log_on_delete_baskets_error(self, log):
        QgsMessageLog.logMessage(log, self.tr("Delete basket from DB"), Qgis.Critical)
