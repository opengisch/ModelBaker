# -*- coding: utf-8 -*-
"""
/***************************************************************************
                              -------------------
        begin                : 08/08/17
        git sha              : :%H$
        copyright            : (C) 2017 by OPENGIS.ch
        email                : info@opengis.ch
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

from qgis.core import (
    QgsEditFormConfig,
    QgsAttributeEditorContainer,
    QgsAttributeEditorRelation,
    QgsAttributeEditorField
)


class Form(object):
    def __init__(self):
        self.__elements = list()

    def elements(self):
        return self.__elements

    def create(self, layer):
        edit_form_config = QgsEditFormConfig()
        root_container = edit_form_config.invisibleRootContainer()
        for element in self.__elements:
            root_container.addChildElement(element.create(root_container, layer))
        edit_form_config.setLayout(QgsEditFormConfig.TabLayout)
        return edit_form_config

    def add_element(self, element):
        self.__elements.append(element)


class FormTab(object):
    def __init__(self, name):
        self.name = name
        self.children = list()

    def addChild(self, child):
        self.children.append(child)

    def create(self, parent, layer):
        container = QgsAttributeEditorContainer(self.name, parent)
        container.setIsGroupBox(False)
        for child in self.children:
            container.addChildElement(child.create(container, layer))
        return container


class FormGroupBox(object):
    def __init__(self, name):
        self.name = name
        self.children = list()

    def addChild(self, child):
        self.children.append(child)

    def create(self, parent, layer):
        container = QgsAttributeEditorContainer(self.name)
        container.setIsGroupBox(True)
        for child in self.children:
            container.addChildElement(child, layer)
        return container


class FormFieldWidget(object):
    def __init__(self, name, field_name):
        self.name = name if name else field_name
        self.field_name = field_name

    def create(self, parent, layer):
        index = layer.fields().indexOf(self.field_name)
        widget = QgsAttributeEditorField(self.name, index, parent)
        return widget


class FormRelationWidget(object):
    def __init__(self, name, relation):
        self.name = name
        self.relation = relation

    def create(self, parent, layer):
        widget = QgsAttributeEditorRelation(self.name, self.relation.id, parent)
        return widget
