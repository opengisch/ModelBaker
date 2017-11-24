# -*- coding: utf-8 -*-
"""
/***************************************************************************
    begin                :    04/10/17
    git sha              :    :%H$
    copyright            :    (C) 2017 by Germán Carrillo (BSF-Swissphoto)
                              (C) 2016 by OPENGIS.ch
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
import psycopg2
import psycopg2.extras
import re

from .db_connector import DBConnector

PG_METADATA_TABLE = 't_ili2db_table_prop'

class PGConnector(DBConnector):
    def __init__(self, uri, schema):
        DBConnector.__init__(self, uri, schema)
        self.conn = psycopg2.connect(uri)
        self.schema = schema
        self._bMetadataTable = self._metadata_exists()
        self.iliCodeName = 'ilicode'

    def map_data_types(self, data_type):
        data_type = data_type.lower()
        if 'timestamp' in data_type:
            return self.QGIS_DATE_TIME_TYPE
        elif 'date' in data_type:
            return self.QGIS_DATE_TYPE
        elif 'time' in data_type:
            return self.QGIS_TIME_TYPE

        return data_type.lower()

    def metadata_exists(self):
        return self._bMetadataTable

    def _metadata_exists(self):
        if self.schema:
            cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cur.execute("""
                        SELECT
                          count(tablename)
                        FROM pg_catalog.pg_tables
                        WHERE schemaname = '{}' and tablename = '{}'
            """.format(self.schema, PG_METADATA_TABLE))
        return bool(cur.fetchone()[0])

    def get_tables_info(self):
        is_domain_field = ''
        domain_left_join = ''
        schema_where = ''
        table_alias = ''
        alias_left_join = ''

        if self.schema:
            if self._bMetadataTable:
                is_domain_field = "p.setting AS is_domain,"
                table_alias = "alias.setting AS table_alias,"
                domain_left_join = """LEFT JOIN {}.t_ili2db_table_prop p
                              ON p.tablename = tbls.tablename
                              AND p.tag = 'ch.ehi.ili2db.tableKind'""".format(self.schema)
                alias_left_join = """LEFT JOIN {}.t_ili2db_table_prop alias
                              ON alias.tablename = tbls.tablename
                              AND alias.tag = 'ch.ehi.ili2db.dispName'""".format(self.schema)
            schema_where = "AND schemaname = '{}'".format(self.schema)

        cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("""
                    SELECT
                      tbls.schemaname AS schemaname,
                      tbls.tablename AS tablename,
                      a.attname AS primary_key,
                      g.f_geometry_column AS geometry_column,
                      g.srid AS srid,
                      {is_domain_field}
                      {table_alias}
                      g.type AS type
                    FROM pg_catalog.pg_tables tbls
                    LEFT JOIN pg_index i
                      ON i.indrelid = CONCAT(tbls.schemaname, '.', tbls.tablename)::regclass
                    LEFT JOIN pg_attribute a
                      ON a.attrelid = i.indrelid
                      AND a.attnum = ANY(i.indkey)
                    {domain_left_join}
                    {alias_left_join}
                    LEFT JOIN public.geometry_columns g
                      ON g.f_table_schema = tbls.schemaname
                      AND g.f_table_name = tbls.tablename
                    WHERE i.indisprimary {schema_where}
        """.format(is_domain_field = is_domain_field, table_alias = table_alias,
                   domain_left_join = domain_left_join, alias_left_join = alias_left_join,
                   schema_where = schema_where))

        return cur

    def get_fields_info(self, table_name):
        # Get all fields for this table
        fields_cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        fields_cur.execute("""
            SELECT
              c.column_name,
              c.data_type,
              pgd.description AS comment,
              unit.setting AS unit,
              txttype.setting AS texttype,
              alias.setting AS column_alias
            FROM pg_catalog.pg_statio_all_tables st
            LEFT JOIN information_schema.columns c ON c.table_schema=st.schemaname AND c.table_name=st.relname
            LEFT JOIN pg_catalog.pg_description pgd ON pgd.objoid=st.relid AND pgd.objsubid=c.ordinal_position
            LEFT JOIN {schema}.t_ili2db_column_prop unit ON c.table_name=unit.tablename AND c.column_name=unit.columnname AND unit.tag = 'ch.ehi.ili2db.unit'
            LEFT JOIN {schema}.t_ili2db_column_prop txttype ON c.table_name=txttype.tablename AND c.column_name=txttype.columnname AND txttype.tag = 'ch.ehi.ili2db.textKind'
            LEFT JOIN {schema}.t_ili2db_column_prop alias ON c.table_name=alias.tablename AND c.column_name=alias.columnname AND alias.tag = 'ch.ehi.ili2db.dispName'
            WHERE st.relid = '{schema}.{table}'::regclass;
            """.format(schema=self.schema, table=table_name))

        return fields_cur

    def get_constraints_info(self, table_name):
        # Get all 'c'heck constraints for this table
        constraints_cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        constraints_cur.execute("""
            SELECT
              consrc,
              regexp_matches(consrc, '\(\((.*) >= [\'']?([-]?[\d\.]+)[\''::integer|numeric]*\) AND \((.*) <= [\'']?([-]?[\d\.]+)[\''::integer|numeric]*\)\)') AS check_details
            FROM pg_constraint
            WHERE conrelid = '{schema}.{table}'::regclass
            AND contype = 'c'
            """.format(schema=self.schema, table=table_name))

        # Create a mapping in the form of
        #
        # fieldname: (min, max)
        constraint_mapping = dict()
        for constraint in constraints_cur:
            constraint_mapping[constraint['check_details'][0]] = (constraint['check_details'][1], constraint['check_details'][3])

        return constraint_mapping

    def get_relations_info(self):
        cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        schema_where1 = "AND KCU1.CONSTRAINT_SCHEMA = '{}'".format(self.schema) if self.schema else ''
        schema_where2 = "AND KCU2.CONSTRAINT_SCHEMA = '{}'".format(self.schema) if self.schema else ''

        cur.execute("""SELECT RC.CONSTRAINT_NAME, KCU1.TABLE_NAME AS referencing_table, KCU1.COLUMN_NAME AS referencing_column, KCU2.CONSTRAINT_SCHEMA, KCU2.TABLE_NAME AS referenced_table, KCU2.COLUMN_NAME AS referenced_column, KCU1.ORDINAL_POSITION
                        FROM INFORMATION_SCHEMA.REFERENTIAL_CONSTRAINTS AS RC
                        INNER JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE AS KCU1
                        ON KCU1.CONSTRAINT_CATALOG = RC.CONSTRAINT_CATALOG AND KCU1.CONSTRAINT_SCHEMA = RC.CONSTRAINT_SCHEMA AND KCU1.CONSTRAINT_NAME = RC.CONSTRAINT_NAME {schema_where1}
                        INNER JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE AS KCU2
                          ON KCU2.CONSTRAINT_CATALOG = RC.UNIQUE_CONSTRAINT_CATALOG AND KCU2.CONSTRAINT_SCHEMA = RC.UNIQUE_CONSTRAINT_SCHEMA AND KCU2.CONSTRAINT_NAME = RC.UNIQUE_CONSTRAINT_NAME
                          AND KCU2.ORDINAL_POSITION = KCU1.ORDINAL_POSITION {schema_where2}
                        GROUP BY RC.CONSTRAINT_NAME, KCU1.TABLE_NAME, KCU1.COLUMN_NAME, KCU2.CONSTRAINT_SCHEMA, KCU2.TABLE_NAME, KCU2.COLUMN_NAME, KCU1.ORDINAL_POSITION
                        ORDER BY KCU1.ORDINAL_POSITION
                        """.format(schema_where1=schema_where1, schema_where2=schema_where2))
        return cur

    def get_domainili_domaindb_mapping(self, domains):
        """TODO: remove when ili2db issue #19 is solved"""
        # Map domain ili name with its correspondent pg name
        cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        domain_names = "'" + "','".join(domains) + "'"
        cur.execute("""SELECT iliname, sqlname
                        FROM {schema}.t_ili2db_classname
                        WHERE sqlname IN ({domain_names})
                    """.format(schema=self.schema, domain_names=domain_names))
        return cur

    def get_models(self):
        """TODO: remove when ili2db issue #19 is solved"""
        # Get MODELS
        cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("""SELECT modelname, content
                       FROM {schema}.t_ili2db_model
                    """.format(schema=self.schema))
        return cur

    def get_classili_classdb_mapping(self, models_info, extended_classes):
        """TODO: remove when ili2db issue #19 is solved"""
        cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        class_names = "'" + "','".join(list(models_info.keys())+list(extended_classes.keys())) + "'"
        cur.execute("""SELECT *
                       FROM {schema}.t_ili2db_classname
                       WHERE iliname IN ({class_names})
                    """.format(schema=self.schema, class_names=class_names))
        return cur

    def get_attrili_attrdb_mapping(self, models_info_with_ext):
        """TODO: remove when ili2db issue #19 is solved"""
        cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        all_attrs = list()
        for c, dict_attr_domain in models_info_with_ext.items():
            all_attrs.extend(list(dict_attr_domain.keys()))
        attr_names = "'" + "','".join(all_attrs) + "'"
        cur.execute("""SELECT iliname, sqlname, owner
                       FROM {schema}.t_ili2db_attrname
                       WHERE iliname IN ({attr_names})
                    """.format(schema=self.schema, attr_names=attr_names))
        return cur
