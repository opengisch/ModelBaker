# -*- coding: utf-8 -*-
"""
/***************************************************************************
    begin                :    04/10/17
    git sha              :    :%H$
    copyright            :    (C) 2017 by Germán Carrillo (BSF-Swissphoto)
    email                :    gcarrillo@linuxmail.org
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

class DBConnector:
    '''SuperClass for all DB connectors.'''
    def __init__(self, uri, schema):
        self.QGIS_DATE_TYPE = 'date'
        self.QGIS_TIME_TYPE = 'time'
        self.QGIS_DATE_TIME_TYPE = 'datetime'
        self.iliCodeName = '' # For Domain-Class relations, specific for each DB

    def map_data_types(self, data_type):
        '''Map provider date/time types to QGIS date/time types'''
        return None

    def metadata_exists(self):
        '''Whether t_ili2db_table_prop table exists or not.'''
        return False

    def get_tables_info(self):
        '''
        Info about tables found in the database (or database schema).

        Return:
            Iterable allowing to access rows, each row should allow to access
            specific columns by name (e.g., a list of dicts {column_name:value})
            Expected columns are:
                schemaname
                tablename
                primary_key
                geometry_column
                srid
                type  (Geometry Type)
                is_domain
                table_alias
        '''
        return []

    def get_fields_info(self, table_name):
        '''
        Info about fields of a given table in the database.

        Return:
            Iterable allowing to access rows, each row should allow to access
            specific columns by name (e.g., a list of dicts {column_name:value})
            Expected columns are:
                column_name
                data_type
                comment
                unit
                texttype
                column_alias
        '''
        return []

    def get_constraints_info(self, table_name):
        '''
        Info about range constraints found in a given table.

        Return:
            Dictionary with keys corresponding to column names and values
            corresponding to tuples in the form (min_value, max_value)
        '''
        return {}

    def get_relations_info(self):
        '''
        Info about relations found in a database (or database schema).

        Return:
            Iterable allowing to access rows, each row should allow to access
            specific columns by name (e.g., a list of dicts {column_name:value})
            Expected columns are:
                constraint_name
                referencing_table_name
                referencing_column_name
                constraint_schema
                referenced_table_name
                referenced_column_name
        '''
        return []

    def get_domainili_domaindb_mapping(self, domains):
        """TODO: remove when ili2db issue #19 is solved"""
        return {}

    def get_models(self):
        """TODO: remove when ili2db issue #19 is solved"""
        return {}

    def get_classili_classdb_mapping(self, models_info, extended_classes):
        """TODO: remove when ili2db issue #19 is solved"""
        return {}

    def get_attrili_attrdb_mapping(self, models_info_with_ext):
        """TODO: remove when ili2db issue #19 is solved"""
        return {}
