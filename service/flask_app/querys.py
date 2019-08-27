# -*- coding: utf-8 -*-
"""Scripts for Postgres.

This module provides scripts for querying the service's postgres sql database.
All member variables are strings. Some member variables require formatting by
the calling function from models.py

Example:
    $ import querys
    $ querys.CREATE_DB.format('gps_tracker_service')
    $ querys.ADD_POSTGIS_TO_DB
    $ querys.UPDATE_ROUTE_LENGTH.format(0, 1234.5678)

Attributes:
    CREATE_DB (str): format with the database name
    DB_EXISTS (str): format with the database name
    ADD_POSTGIS_TO_DB (str): no format required, however postgis must be
        installed
    DROP_DB (str): format with the database name
    TABLE_EXISTS (str): format with the table name
    DROP_TABLE (str): format with the table name
    CREATE_ROUTE_TABLE (str): no format required, specific for the service
    ADD_GEOM_COLUMN_TO_TABLE (str): format with the table name, requires postgis
        is activated by ADD_POSTGIS_TO_DB script.
    CREATE_ROUTE_LEN_TABLE (str): no format required, specific for the service
    GET_NEW_ROUTE_ID (str): no format required, specific for the service
        route_lengths table
    START_NEW_ROUTE (str): format with the new route_id
    ROUTE_ID_EXISTS (str): format with the route_id to check if exists
    ROUTE_ID_HAS_WAYPOINTS (str): format with the route_id to check if it has waypoints
    UPDATE_ROUTE (str): format with (route_id, longitude, latitude)
    SELECT_ALL (str): format with the table name
    SINGLE_ROUTE_LENGTH (str): format with the route_id to query for its length
    UPDATE_ROUTE_LENGTH (str): format with the (route_length, route_id)
    UPDATE_ALL_ROUTES_IN_DAY_LENGTH (str): format with a string "%Y-%m-%d"
    LONGEST_ROUTE_IN_DAY (str): format with the a string "%Y-%m-%d"
    CHECK_ORIGIN_TIME (str): format with a route_id
    ADD_TRANSACTION_ROW_1 (str): no format required, specific for the service
    ADD_TRANSACTION_ROW_0 (str): no format required, specific for the service
    ADD_TRANSACTION_ROW_2 (str): no format required, specific for the service

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

ROUTE_ID_HAS_WAYPOINTS = """
    SELECT route_id FROM routes WHERE route_id = {} LIMIT 1;
"""

UPDATE_ROUTE = """
    INSERT INTO routes (route_id, timestamp, geom)
    VALUES ({}, now(), 'SRID=4326; POINT({} {})');
"""

SELECT_ALL = "SELECT * FROM {};"

SINGLE_ROUTE_LENGTH = """
    SELECT sum(route_length) *.001 as km from (
        SELECT
        ST_DistanceSphere(geom, lag(geom, 1) OVER (ORDER BY timestamp)) as route_length
        FROM routes
        WHERE route_id = {}
    ) as route_length_table;
"""

UPDATE_ROUTE_LENGTH = """
    UPDATE route_lengths SET route_length = {} WHERE route_id = {};
"""
# TODO - NOT IN USE, REMOVE AFTER SEPT 2019
UPDATE_ALL_ROUTES_IN_DAY_LENGTH = """
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
