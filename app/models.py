import datetime

import psycopg2

from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT


TODAY = datetime.datetime.now().strftime("%m-%d-%Y")

DB_USER = "postgres"
DB_PASS = "entropy09"
DB_HOST = "db"
DB_PORT = "5432"
DB_NAME = "planet"
DB_TABLE_NAME = "routes"

CREATE_TABLE_SCRIPT = """
    CREATE TABLE {} (
    route_id SERIAL,
    timestamp TIMESTAMP,
    route_length REAL
    );
    """.format(
    DB_TABLE_NAME
)

ADD_EXT_TO_DB_SCRIPT = "CREATE EXTENSION IF NOT EXISTS {}"

ADD_GEOM_COLUMN_TO_TABLE_SCRIPT = (
    "SELECT AddGeometryColumn('public', 'routes', 'geom', 4326, 'POINT', 2);"
)

START_NEW_ROUTE_SCRIPT = "INSERT INTO routes (route_id, timestamp) VALUES ({}, now());"

GET_NEW_ROUTE_ID_SCRIPT = "SELECT max(route_id) + 1 FROM routes;"

UPDATE_ROUTE_SCRIPT = "INSERT INTO routes (route_id, timestamp, geom) VALUES ({}, now(), 'SRID=4326; POINT({} {})');"

SINGLE_ROUTE_LENGTH_QUERY = """
    SELECT sum(route_length) as km from (
        SELECT
        ST_Distance_Sphere(geom, lag(geom, 1) OVER (ORDER BY timestamp)) / 1000 as route_length
        FROM routes
        WHERE route_id = {} AND geom IS NOT NULL
    ) as route_length_table;
    """

def create_new_database():
    """
    dbname is default so we can create new database
    """
    conn = psycopg2.connect(
        "dbname=postgres user={} password={}".format(DB_USER, DB_PASS)
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    cur.execute("CREATE DATABASE {};".format(DB_NAME))
    close_and_commit(cur, conn)

def activate_pg_extension(ext_script):
    conn, cur = conn_cur_and_execute(ext_script)
    close_and_commit(cur, conn)

def create_table():
    conn, cur = conn_cur_and_execute(CREATE_TABLE_SCRIPT)
    close_and_commit(cur, conn)

def add_geometry_column():
    conn, cur = conn_cur_and_execute(ADD_GEOM_COLUMN_TO_TABLE_SCRIPT)
    close_and_commit(cur, conn)

def conn_cur_and_execute(pgscript):
    conn = psycopg2.connect(
        "dbname={} user={} password={}".format(DB_NAME, DB_USER, DB_PASS)
    )
    cur = conn.cursor()
    cur.execute(pgscript)
    return conn, cur

def close_and_commit(cur, conn):
    cur.close()
    conn.commit()
    conn.close()

def initialize_db_with_extension_and_table():
    create_new_database()
    activate_pg_extension(ADD_EXT_TO_DB_SCRIPT.format("postgis"))
    create_table()
    add_geometry_column()
    return True
