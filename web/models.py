import datetime

import psycopg2

from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT


TODAY = datetime.datetime.now().strftime("%m-%d-%Y")

PERSISTENCE_PROVIDER = "postgres"
DB_USER = "postgres"
DB_PASS = "entropy09"
DB_PORT = "5432"
DB_NAME = "planet"

# Postgres scripts for db
CREATE_DB_SCRIPT = "CREATE DATABASE {};"

DB_EXISTS_SCRIPT = """
    SELECT datname
    FROM pg_catalog.pg_database
    WHERE lower(datname) = lower('{}');"
"""

ADD_POSTGIS_TO_DB_SCRIPT = "CREATE EXTENSION IF NOT EXISTS postgis"

DROP_DB_SCRIPT = """DROP DATABASE IF EXISTS {}"""

TABLE_EXISTS_SCRIPT = """
    SELECT exists(SELECT relname FROM pg_class WHERE relname='{}')
"""

CREATE_ROUTE_TABLE_SCRIPT = """
    CREATE TABLE routes (
    route_id SERIAL,
    timestamp TIMESTAMP
    );
"""

ADD_GEOM_COLUMN_TO_TABLE_SCRIPT = """
    SELECT AddGeometryColumn('public', '{}', 'geom', 4326, 'POINT', 2);
"""

CREATE_ROUTE_LEN_TABLE_SCRIPT = """
    CREATE TABLE route_lengths (
    route_id SERIAL,
    creation_time TIMESTAMP,
    route_length REAL
    );
"""

GET_NEW_ROUTE_ID_SCRIPT = "SELECT max(route_id) + 1 FROM route_lengths;"

START_NEW_ROUTE_SCRIPT = """
    INSERT INTO route_lengths (route_id, creation_time, route_length)
    VALUES ({}, now(),  0.00);
"""

UPDATE_ROUTE_SCRIPT = """
    INSERT INTO routes (route_id, timestamp, geom)
    VALUES ({}, now(), 'SRID=4326; POINT({} {})');
"""

SINGLE_ROUTE_LENGTH_QUERY = """
    SELECT sum(route_length) as km from (
        SELECT
        ST_Distance_Sphere(geom, lag(geom, 1) OVER (ORDER BY timestamp)) / 1000 as route_length
        FROM routes
        WHERE route_id = {}
    ) as route_length_table;
"""

UPDATE_ROUTE_LENGTH_SCRIPT = """
    UPDATE route_lengths SET route_length = {} WHERE route_id = {};
"""

DROP_TABLE_SCRIPT = """DROP TABLE IF EXISTS {}"""

LONGEST_ROUTE_IN_DAY_QUERY = """
    SELECT route_id, sum(km) as total_km
    FROM
    	(SELECT route_id, km as km
    	 FROM (
    		SELECT route_id, ST_Distance_Sphere(geom, lag(geom, 1) OVER (partition by route_id ORDER BY timestamp)) / 1000 as km
    		FROM routes
    	 	WHERE timestamp BETWEEN '{}' and '{}'::date + interval '24 hours'
    	 ) as route_length_table)
    	as table_two
    group by route_id
    order by total_km DESC LIMIT 1;
"""

CHECK_ORIGIN_TIME_SCRIPT = """
    SELECT creation_time FROM route_lengths WHERE route_id = {};
"""

ADD_ZERO_TRANSACTION_BLOCK = """

"""

def create_new_database():
    """
    PERSISTENCE_PROVIDER is default
    """
    conn = psycopg2.connect(
        "dbname={} user={} password={}".format(PERSISTENCE_PROVIDER, DB_USER, DB_PASS)
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    cur.execute(CREATE_DB_SCRIPT.format(DB_NAME))
    close_and_commit(cur, conn)
    return True

def activate_postgis_extension():
    conn, cur = execute_pgscript(ADD_POSTGIS_TO_DB_SCRIPT)
    close_and_commit(cur, conn)
    return True

def create_route_table():
    conn, cur = execute_pgscript(CREATE_ROUTE_TABLE_SCRIPT)
    close_and_commit(cur, conn)

def create_route_length_table():
    conn, cur = execute_pgscript(CREATE_ROUTE_LEN_TABLE_SCRIPT)
    close_and_commit(cur, conn)

def add_geometry_column_to_table():
    conn, cur = execute_pgscript(ADD_GEOM_COLUMN_TO_TABLE_SCRIPT.format(
    "routes"))
    close_and_commit(cur, conn)

def execute_pgscript(pgscript):
    conn = psycopg2.connect(
        "dbname={} user={} password={}".format(DB_NAME, DB_USER, DB_PASS)
    )
    cur = conn.cursor()
    cur.execute(pgscript)
    return conn, cur

def bootstrap_tables_with_first_route_id():
    pass

def db_exists(db_name):
    exists = ""
    try:
        conn = psycopg2.connect(
            "dbname={} user={} password={}".format(PERSISTENCE_PROVIDER, DB_USER, DB_PASS)
        )
        cur = conn.cursor()
        cur.execute(DB_EXISTS_SCRIPT.format(db_name))
        exists = cur.fetchone()
    except psycopg2.Error as err:
        close_and_commit(cur, conn)
        return err
    close_and_commit(cur, conn)
    if exists and exists[0]==db_name:
        return True
    return False

def table_exists(table_name):
    exists = False
    try:
        conn, cur = execute_pgscript(TABLE_EXISTS_SCRIPT.format(table_name))
        exists = cur.fetchone()[0]
    except psycopg2.Error as err:
        close_and_commit(cur, conn)
        return err
    close_and_commit(cur, conn)
    return exists

def drop_table(table_name):
    conn, cur = execute_pgscript(DROP_TABLE_SCRIPT.format(table_name))
    close_and_commit(cur, conn)
    return True

def drop_database():
    conn = psycopg2.connect(
        "dbname={} user={} password={}".format(PERSISTENCE_PROVIDER, DB_USER, DB_PASS)
    )
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute(DROP_DB_SCRIPT.format(DB_NAME))
    close_and_commit(cur, conn)
    return True

def close_and_commit(cur, conn):
    cur.close()
    conn.commit()
    conn.close()

def initialize_db_with_extension_and_tables():
    exists = db_exists(DB_NAME)
    if not exists:
        create_new_database()
        activate_postgis_extension()
    exists = table_exists("routes")
    if not exists:
        create_route_table()
        add_geometry_column_to_table()
    exists = table_exists("route_lengths")
    if not exists:
        create_route_length_table()
    #bootstrap_tables_with_first_route_id()
    return True
