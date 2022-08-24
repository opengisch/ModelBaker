# -*- coding: utf-8 -*-
"""
/***************************************************************************
                              -------------------
        begin                : 2022-07-17
        git sha              : :%H$
        copyright            : (C) 2022 by Dave Signer
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

import configparser
import os
from typing import Union

from QgisModelBaker.internal_libs.toppingmaker import ProjectTopping, Target
from QgisModelBaker.internal_libs.toppingmaker.utils import slugify, toppingfile_link

from .ili2dbsettings import Ili2dbSettings


class MetaConfig(object):

    METACONFIG_TYPE = "metaconfig"

    def __init__(self):
        # generated sections
        # configuration_section["ch.interlis.referenceData"] = ...
        # configuration_section["qgis.modelbaker.projecttopping"] = ...
        self.referencedata_paths = []
        self.projecttopping_path = None
        # ili2db configuration - toml and sql files should be appended as topping
        self.ili2db_settings = Ili2dbSettings()

    def update_referencedata_paths(self, value: Union[list, bool]):
        if isinstance(value, str):
            value = [value]
        self.referencedata_paths.extend(value)

    def update_projecttopping_path(self, value: str):
        self.projecttopping_path = value

    def generate_files(self, target: Target):
        """
        [CONFIGURATION]
        qgis.modelbaker.projecttopping=ilidata:ch.opengis.config.KbS_LV95_V1_4_projecttopping
        ch.interlis.referenceData=ilidata:ch.opengis.config.KbS_Codetexte_V1_4

        [ch.ehi.ili2db]
        defaultSrsCode = 2056
        smart2Inheritance = true
        strokeArcs = false
        importTid = true
        createTidCol = false
        models = KbS_Basis_V1_4
        preScript=ilidata:ch.opengis.config.KbS_LV95_V1_4_prescript
        iliMetaAttrs=ilidata:ch.opengis.config.KbS_LV95_V1_4_toml
        """

        configuration_section = {}

        # append project topping and reference data links
        if self.projecttopping_path:
            # generate toppingfile of projettopping (most possibly already an id, so no generation needed)
            projecttopping_link = self._generate_toppingfile_link(
                target, ProjectTopping.PROJECTTOPPING_TYPE, self.projecttopping_path
            )
            configuration_section[
                "qgis.modelbaker.projecttopping"
            ] = f"ilidata:{projecttopping_link}"

        if self.referencedata_paths:
            # generate toppingfiles of the reference data
            referencedata_links = ",".join(
                [
                    f"ilidata:{self._generate_toppingfile_link(target, IliProjectTopping.REFERENCEDATA_TYPE, path)}"
                    for path in self.referencedata_paths
                ]
            )
            configuration_section["ch.interlis.referenceData"] = referencedata_links

        ili2db_section = {}

        # append models and the ili2db parameters
        ili2db_section["models"] = ",".join(self.ili2db_settings.models)
        ili2db_section.update(self.ili2db_settings.parameters)

        # generate metaattr and prescript / postscript files
        if self.ili2db_settings.metaattr_path:
            ili2db_section[
                "iliMetaAttrs"
            ] = f"ilidata:{self._generate_toppingfile_link(target, IliProjectTopping.METAATTR_TYPE, self.ili2db_settings.metaattr_path)}"
        if self.ili2db_settings.prescript_path:
            ili2db_section[
                "preScript"
            ] = f"ilidata:{self._generate_toppingfile_link(target, IliProjectTopping.SQLSCRIPT_TYPE, self.ili2db_settings.prescript_path)}"
        if self.ili2db_settings.postscript_path:
            ili2db_section[
                "postScript"
            ] = f"ilidata:{self._generate_toppingfile_link(target, IliProjectTopping.SQLSCRIPT_TYPE, self.ili2db_settings.postscript_path)}"

        # make the full conifg
        metaconfig = configparser.ConfigParser()
        metaconfig["CONFIGURATION"] = configuration_section
        metaconfig["ch.ehi.ili2db"] = ili2db_section

        # write INI file
        metaconfig_slug = f"{slugify(target.projectname)}.ini"
        absolute_filedir_path, relative_filedir_path = target.filedir_path(
            MetaConfig.METACONFIG_TYPE
        )

        with open(
            os.path.join(absolute_filedir_path, metaconfig_slug), "w"
        ) as configfile:
            output = metaconfig.write(configfile)
            print(output)

        return target.path_resolver(target, metaconfig_slug, MetaConfig.METACONFIG_TYPE)

    def _generate_toppingfile_link(self, target: Target, type, path):
        if not os.path.isfile(path):
            # it's already an id pointing to somewhere, no toppingfile needs to be created
            return path
        # copy file from path to our target, and return the ilidata_pathresolved id
        return toppingfile_link(target, type, path)