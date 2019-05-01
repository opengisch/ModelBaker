# -*- coding: utf-8 -*-
"""
/***************************************************************************
    begin                :    30/04/19
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
from .layer_uri import LayerUri


class PgLayerUri(LayerUri):

    def __init__(self, uri):
        LayerUri.__init__(self, uri)
        self.provider = 'postgres'

    def get_data_source_uri(self, record):
        if record['geometry_column']:
            data_source_uri = '{uri} key={primary_key} estimatedmetadata={estimated_metadata} srid={srid} type={type} table="{schema}"."{table}" ({geometry_column})'.format(
                uri=self.uri,
                primary_key=record['primary_key'],
                estimated_metadata=self.pg_estimated_metadata,
                srid=record['srid'],
                type=record['type'],
                schema=record['schemaname'],
                table=record['tablename'],
                geometry_column=record['geometry_column']
            )
        else:
            data_source_uri = '{uri} key={primary_key} table="{schema}"."{table}"'.format(
                uri=self.uri,
                primary_key=record['primary_key'],
                schema=record['schemaname'],
                table=record['tablename']
            )

        return data_source_uri