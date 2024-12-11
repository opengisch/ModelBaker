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

from enum import IntEnum

from qgis.PyQt.QtCore import QAbstractTableModel, QModelIndex, Qt
from qgis.PyQt.QtWidgets import QHeaderView, QWidget

import QgisModelBaker.utils.gui_utils as gui_utils

WIDGET_UI = gui_utils.get_ui_class("basket_panel.ui")


class BasketModel(QAbstractTableModel):
    """
    ItemModel providing all the existing baskets in the given dataset.
    It provides the topic, the BIDs (t_ili_tid), among others.
    """

    class Columns(IntEnum):
        DATASET = 0
        TOPIC = 1
        BID_DOMAIN = 2
        BID_VALUE = 3
        ATTACHMENT_KEY = 4

    def __init__(self):
        super().__init__()
        self.basket_settings = {}

    def columnCount(self, parent):
        return len(BasketModel.Columns)

    def rowCount(self, parent):
        return len(self.basket_settings)

    def flags(self, index):
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled

    def index(self, row: int, column: int, parent: QModelIndex = ...) -> QModelIndex:
        """
        default override
        """
        return super().createIndex(row, column, parent)

    def parent(self, index):
        """
        default override
        """
        return index

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            if section == BasketModel.Columns.DATASET:
                return self.tr("Dataset")
            if section == BasketModel.Columns.TOPIC:
                return self.tr("Topic")
            if section == BasketModel.Columns.BID_DOMAIN:
                return self.tr("BID (OID Type)")
            if section == BasketModel.Columns.BID_VALUE:
                return self.tr("BID Value")
            if section == BasketModel.Columns.ATTACHMENT_KEY:
                return self.tr("Attachment key")

    def data(self, index, role):
        if role == int(Qt.DisplayRole) or role == int(Qt.EditRole):
            key = list(self.basket_settings.keys())[index.row()]
            if index.column() == BasketModel.Columns.DATASET:
                return self.basket_settings[key]["datasetname"]
            if index.column() == BasketModel.Columns.TOPIC:
                return key
            if index.column() == BasketModel.Columns.BID_DOMAIN:
                return self.basket_settings[key]["bid_domain"] or "---"
            if index.column() == BasketModel.Columns.BID_VALUE:
                return self.basket_settings[key]["bid_value"]
            if index.column() == BasketModel.Columns.ATTACHMENT_KEY:
                return self.basket_settings[key]["attachmentkey"]
        elif role == int(Qt.ToolTipRole):
            key = list(self.basket_settings.keys())[index.row()]
            if index.column() == BasketModel.Columns.DATASET:
                return self.tr("Dataset this basket belongs to")
            if index.column() == BasketModel.Columns.TOPIC:
                return key
            if index.column() == BasketModel.Columns.BID_DOMAIN:
                message = self.tr(
                    "<html><head/><body><p>The OID format is not defined, you can use whatever you want, but it should always start with an underscore <code>_</code> or an alphanumeric value.</p></body></html>"
                )
                oid_domain = self.basket_settings[key].get("oid_domain", "")
                if oid_domain[-7:] == "UUIDOID":
                    message = self.tr(
                        "<html><head/><body><p>The OID should be an Universally Unique Identifier (OID TEXT*36).</p></body></html>"
                    )
                elif oid_domain[-11:] == "STANDARDOID":
                    message = self.tr(
                        """<html>
                        <body>
                        <p>
                        The OID format requireds an 8 char prefix and 8 char postfix.
                        </p>
                        <p><b>Prefix (2 + 6 chars):</b> Country identifier + a 'global' identification part assigned once by the official authority.</p>
                        </p><p><b>Postfix (8 chars):</b> Sequence (numeric or alphanumeric) of your system as 'local' identification part.</p>
                        </body>
                        </html>
                """
                    )
                elif oid_domain[-6:] == "I32OID":
                    message = self.tr(
                        "<html><head/><body><p>The OID must be an integer value (OID 0 .. 2147483647).</p></body></html>"
                    )
                elif oid_domain[-6:] == "ANYOID":
                    message = self.tr(
                        "<html><head/><body><p>The OID format could vary depending in what basket the object (entry) is located.</p><p>These objects could be in the following topics: {topics}</body></html>".format(
                            topics=self.basket_settings[key]["interlis_topic"]
                        )
                    )
                return message
            # if index.column() == BasketModel.Columns.BID_VALUE:  # TODO: Move this tooltip to the Edit Basket dialog instead?
            #    return "<html><head/><body><p>Use `{t_id}` as placeholder when you want to use the next T_Id sequence value.</body></html>"
            if index.column() == BasketModel.Columns.ATTACHMENT_KEY:
                return "Attachment key"
        return None

    def basket_config_by_index(self, index: QModelIndex) -> dict:
        # Return the basket config for the row corresponding to the given index.
        # This includes the whole basket configuration (t_id, dataset_id,
        # topic, etc.)
        return list(self.basket_settings.values())[index.row()]

    def load_basket_config(self, db_connector, dataset):
        self.beginResetModel()
        self.basket_settings.clear()

        for topic_record in db_connector.get_topics_info():
            basket_setting = {}
            topic_key = f"{topic_record['model']}.{topic_record['topic']}"

            for basket_record in db_connector.get_baskets_info():
                if (
                    basket_record["datasetname"] == dataset
                    and topic_key == basket_record["topic"]
                ):
                    basket_setting["bid_value"] = basket_record["basket_t_ili_tid"]
                    basket_setting["attachmentkey"] = basket_record["attachmentkey"]
                    basket_setting["datasetname"] = basket_record["datasetname"]
                    basket_setting["bid_domain"] = topic_record["bid_domain"]

                    # Additional basket info, not displayed by the view, but useful
                    # in other operations (e.g., edit) to fully identify baskets
                    basket_setting["basket_t_id"] = basket_record["basket_t_id"]
                    basket_setting["dataset_t_id"] = basket_record["dataset_t_id"]
                    basket_setting["topic"] = basket_record["topic"]
                    self.basket_settings[basket_record["topic"]] = basket_setting
                    break  # Go to next topic

        self.endResetModel()


class SummaryBasketPanel(QWidget, WIDGET_UI):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        self.setupUi(self)
        self.parent = parent
        self.bid_model = BasketModel()
        self.basket_view.setModel(self.bid_model)

        self.basket_view.horizontalHeader().setSectionResizeMode(
            BasketModel.Columns.DATASET, QHeaderView.ResizeToContents
        )
        self.basket_view.horizontalHeader().setSectionResizeMode(
            BasketModel.Columns.TOPIC, QHeaderView.Stretch
        )
        self.basket_view.horizontalHeader().setSectionResizeMode(
            BasketModel.Columns.BID_DOMAIN, QHeaderView.ResizeToContents
        )
        self.basket_view.horizontalHeader().setSectionResizeMode(
            BasketModel.Columns.BID_VALUE, QHeaderView.ResizeToContents
        )
        self.basket_view.horizontalHeader().setSectionResizeMode(
            BasketModel.Columns.ATTACHMENT_KEY, QHeaderView.ResizeToContents
        )

    def load_basket_config(self, db_connector, dataset):
        self.bid_model.load_basket_config(db_connector, dataset)

    def selected_basket_settings(self) -> dict:
        # Returns the whole configuration for the selected basket
        selected_baskets = self.basket_view.selectedIndexes()
        if selected_baskets:
            # Pick the first index, since all others belong to the same row
            return self.bid_model.basket_config_by_index(selected_baskets[0])

        return {}
