# -*- coding: utf-8 -*-
"""
/***************************************************************************
    begin                :    08/04/19
    git sha              :    :%H$
    copyright            :    (C) 2019 by Yesid Polania
    email                :    yesidpol.3@gmail.com
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
from abc import ABC, abstractmethod


class DbFactory:

    @abstractmethod
    def get_db_connector(self, uri, schema):
        pass

    @abstractmethod
    def get_config_panel(self, parent):
        pass

    @abstractmethod
    def get_db_uri(self):
        pass

    @abstractmethod
    def get_layer_uri(self, uri):
        pass

    @abstractmethod
    def save_settings(self, configuration):
        pass

    @abstractmethod
    def load_settings(self, configuration):
        pass
