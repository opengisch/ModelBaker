# -*- coding: utf-8 -*-
"""
/***************************************************************************
                              -------------------
        begin                : 8.11.2016
        git sha              : :%H$
        copyright            : (C) 2016 by OPENGIS.ch
        email                : matthias@opengis.ch
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

import argparse
import importlib
import sys

import yaml
from libqgsprojectgen.dataobjects.project import Project
from qgis.core import QgsApplication, QgsProject


def main(argv):
    parser = argparse.ArgumentParser(
        "Generate QGIS projects or QGIS dataobjects yaml templates."
    )
    parser.add_argument(
        "--generator", type=str, help="The generator to use. (Example: postgres)"
    )
    parser.add_argument(
        "--uri",
        type=str,
        help="Database uri, used as db entry point. (Example: service=pg_qgep)",
    )
    parser.add_argument(
        "out",
        type=str,
        help="Path to the generated dataobjects. (Example: /home/qgis/my_project)",
    )

    args = parser.parse_args()

    # Initialize qgis libraries
    QgsApplication([], True)
    QgsApplication.initQgis()

    def debug_log_message(message, tag, level):
        print("{}({}): {}".format(tag, level, message))

    QgsApplication.instance().messageLog().messageReceived.connect(debug_log_message)

    generator_module = importlib.import_module("generator." + args.generator)

    generator = generator_module.Generator(args.uri)

    available_layers = generator.layers()
    relations, _ = generator.relations(available_layers)

    project = Project()
    project.layers = available_layers
    project.relations = relations

    qgis_project = QgsProject.instance()
    project.create(args.out, qgis_project)

    yamlfile = args.out + ".yaml"
    with open(yamlfile, "w") as f:
        f.write(yaml.dump(project.dump(), default_flow_style=False))
        print("Project template written to {}".format(yamlfile))

    QgsApplication.exitQgis()


if __name__ == "__main__":
    # execute only if run as a script
    main(sys.argv[1:])
