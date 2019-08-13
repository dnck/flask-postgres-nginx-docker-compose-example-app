# -*- coding: utf-8 -*-
"""Scripts for Postgres.

This module demonstrates documentation as specified by the `Google Python
Style Guide`_. Docstrings may extend over multiple lines. Sections are created
with a section header and a colon followed by a block of indented text.

Example:
    Examples can be given using either the ``Example`` or ``Examples``
    sections. Sections support any reStructuredText formatting, including
    literal blocks::

        $ python example_google.py

Section breaks are created by resuming unindented text. Section breaks
are also implicitly created anytime a new section starts.

Attributes:
    module_level_variable1 (int): Module level variables may be documented in
        either the ``Attributes`` section of the module docstring, or in an
        inline docstring immediately following the variable.

        Either form is acceptable, but the two should not be mixed. Choose
        one convention to document module level variables and be consistent
        with it.

Todo:
    * For module TODOs
    * You have to also use ``sphinx.ext.todo`` extension

"""


CREATE_DB = "CREATE DATABASE {};"

DB_EXISTS = """
    SELECT datname
    FROM pg_catalog.pg_database
    WHERE lower(datname) = lower('{}');
"""

ADD_POSTGIS_TO_DB = "CREATE EXTENSION IF NOT EXISTS postgis;"

DROP_DB = "DROP DATABASE IF EXISTS {};"

TABLE_EXISTS = """
    SELECT exists(SELECT relname FROM pg_class WHERE relname='{}');
"""

DROP_TABLE = """DROP TABLE IF EXISTS {};"""

CREATE_ROUTE_TABLE = """
    CREATE TABLE routes (
    route_id SERIAL,
    timestamp TIMESTAMP
    );
"""

ADD_GEOM_COLUMN_TO_TABLE = """
    SELECT AddGeometryColumn('public', '{}', 'geom', 4326, 'POINT', 2);
"""

CREATE_ROUTE_LEN_TABLE = """
    CREATE TABLE route_lengths (
    route_id SERIAL,
    creation_time TIMESTAMP,
    route_length REAL
    );
"""

GET_NEW_ROUTE_ID = "SELECT max(route_id) + 1 FROM route_lengths;"

START_NEW_ROUTE = """
    INSERT INTO route_lengths (route_id, creation_time, route_length)
    VALUES ({}, now(),  0.00);
"""

ROUTE_ID_EXISTS = """
    SELECT route_id FROM route_lengths WHERE route_id = {} LIMIT 1;
"""

UPDATE_ROUTE = """
    INSERT INTO routes (route_id, timestamp, geom)
    VALUES ({}, now(), 'SRID=4326; POINT({} {})');
"""

SELECT_ALL = "SELECT * FROM {};"

SINGLE_ROUTE_LENGTH = """
    SELECT sum(route_length) *.001 as km from (
        SELECT
        ST_DistanceSphere(geom, lag(geom, 1) OVER (ORDER BY timestamp)) as   route_length
        FROM routes
        WHERE route_id = {}
    ) as route_length_table;
"""

UPDATE_ROUTE_LENGTH = """
    UPDATE route_lengths SET route_length = {} WHERE route_id = {};
"""

UPDATE_DAYS_ROUTE_LENGTH """
    with new_values as (
       SELECT route_id, sum(km) as total_km
        FROM
        	(SELECT route_id, km as km
        	 FROM (
        		SELECT route_id, ST_DistanceSphere(geom, lag(geom, 1) OVER (partition by route_id ORDER BY timestamp)) / 1000 as km
        		FROM routes
        	 	WHERE timestamp BETWEEN '{}' and '{}'::date + interval '24 hours'
        	 ) as route_length_table)
        	as table_two
        group by route_id
    )
    UPDATE route_lengths rl
      set route_length = new_values.total_km
    from new_values
    where new_values.route_id = rl.route_id;
"""

LONGEST_ROUTE_IN_DAY = """
    SELECT route_id, sum(km) as total_km
    FROM
    	(SELECT route_id, km as km
    	 FROM (
    		SELECT route_id, ST_DistanceSphere(geom, lag(geom, 1) OVER (partition by route_id ORDER BY timestamp)) / 1000 as km
    		FROM routes
    	 	WHERE timestamp BETWEEN '{}' and '{}'::date + interval '24 hours'
    	 ) as route_length_table)
    	as table_two
    group by route_id
    order by total_km DESC LIMIT 1;
"""

CHECK_ORIGIN_TIME = """
    SELECT creation_time FROM route_lengths WHERE route_id = {};
"""
# Longitude / Latitude Philadelphia
ADD_TRANSACTION_ROW_1 = """
    INSERT INTO routes (route_id, timestamp, geom)
    VALUES (0, '1984-01-28 00:00:01', 'SRID=4326; POINT(-89.11673 32.77152)');
"""
# Longitude / Latitude Tampa
ADD_TRANSACTION_ROW_0 = """
   INSERT INTO routes (route_id, timestamp, geom)
   VALUES (0, '1984-01-28 00:00:00', 'SRID=4326; POINT(-82.45843 27.94752)')
"""
ADD_TRANSACTION_ROW_2 = """
    INSERT INTO route_lengths (route_id, creation_time, route_length)
    VALUES (0, '1984-01-28 00:00:01',  1520.7042);
"""
