# -*- coding: utf-8 -*-
"""
/***************************************************************************
    begin                :    11.01.2019
    git sha              :    :%H$
    copyright            :    (C) 2019 Matthias Kuhn
    email                :    matthias@opengis.ch
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
import tempfile
import os
import logging

from QgisModelBaker.libili2db import iliimporter
from QgisModelBaker.libili2db.globals import DbIliMode
from QgisModelBaker.tests.utils import iliimporter_config, testdata_path
from QgisModelBaker.libqgsprojectgen.generator.generator import Generator
from QgisModelBaker.libqgsprojectgen.dataobjects import Project
from qgis.testing import unittest, start_app
from qgis.core import (
    QgsVectorLayerUtils,
    QgsGeometry,
    QgsExpressionContext,
    QgsExpressionContextUtils,
    QgsProject,
    Qgis
)


start_app()


class TestGpkgPrimaryKey(unittest.TestCase):

    @unittest.skipIf(Qgis.QGIS_VERSION_INT < 30500, "Default value expression only available in QGIS 3.6 (3.5 and later)")
    def test_gpkg_primary_key(self):
        testpath = tempfile.mkdtemp()
        gpkg_path = os.path.join(testpath, 'exceptional_loads_route.gpkg')

        # Schema Import
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2gpkg
        importer.configuration = iliimporter_config(
            importer.tool, 'ilimodels')
        importer.configuration.ilimodels = 'ExceptionalLoadsRoute_LV95_V1'
        importer.configuration.dbfile = gpkg_path
        importer.configuration.epsg = 2056
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        self.assertEqual(importer.run(), iliimporter.Importer.SUCCESS)

        generator = Generator(DbIliMode.ili2gpkg,
                              gpkg_path,
                              importer.configuration.inheritance)

        available_layers = generator.layers()
        relations, _ = generator.relations(available_layers)
        legend = generator.legend(available_layers)

        project = Project()
        project.layers = available_layers
        project.relations = relations
        project.legend = legend
        project.post_generate()

        qgis_project = QgsProject.instance()
        project.create(None, qgis_project)

        obstacle_layer = next((layer for layer in available_layers if 'obstacle' in layer.uri))

        scopes = QgsExpressionContextUtils.globalProjectLayerScopes(obstacle_layer.layer)
        context = QgsExpressionContext(scopes)

        obstacle_layer.layer.startEditing()
        self.assertIsNotNone(obstacle_layer.layer.dataProvider().transaction())

        feature = QgsVectorLayerUtils.createFeature(obstacle_layer.layer, QgsGeometry(), {}, context)
        self.assertEqual(feature['T_Id'], 0)
        feature = QgsVectorLayerUtils.createFeature(obstacle_layer.layer, QgsGeometry(), {}, context)
        self.assertEqual(feature['T_Id'], 1)

    def print_info(self, text):
        logging.info(text)

    def print_error(self, text):
        logging.info(text)
