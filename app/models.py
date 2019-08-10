"""
Initialization and schemas for the database
"""
import datetime

import psycopg2

from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

DEBUG = False

TODAY = datetime.datetime.now().strftime("%m-%d-%Y")

DB_USER = "postgres"
DB_PASS = "entropy09"
DB_HOST = "db"
DB_PORT = "5432"
DB_NAME = "planet"
DB_TABLE_NAME = "routes"


# Need to add the appropriate types here
CREATE_TABLE_SCRIPT = """
    CREATE TABLE {} (
    route_id SERIAL,
    timestamp TIMESTAMP,
    route_length REAL
    );
    """.format(
    DB_TABLE_NAME
)

ADD_POSTGIS_EXT_TO_DB_SCRIPT = "CREATE EXTENSION IF NOT EXISTS postgis"

ADD_GEOM_COLUMN_TO_TABLE_SCRIPT = (
    "SELECT AddGeometryColumn('public', 'routes', 'geom', 4326, 'POINT', 2);"
)

NEW_ROUTE_ID_SCRIPT = "SELECT max(route_id) + 1 FROM routes;"

UPDATE_ROUTE_SCRIPT = "INSERT INTO routes (route_id, timestamp, geom) VALUES ({}, now(), 'SRID=4326; POINT({} {})');"

COLLECT_POINTS_IN_ROUTE_SCRIPT = "SELECT * FROM routes WHERE route_id = {} AND geom IS NOT NULL ORDER BY timestamp;;"

COLLECT_ROUTES_IN_DAY = """SELECT * FROM routes WHERE timestamp BETWEEN '{}' and '{}'::date + interval '24 hours' AND geom IS NOT NULL;"""

def create_new_database():
    conn = psycopg2.connect(
        "dbname=postgres user={} password={}".format(DB_USER, DB_PASS)
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    cur.execute("CREATE DATABASE {};".format(DB_NAME))
    close_and_commit(cur, conn)


def activate_pg_extensions(ext_script):
    conn = psycopg2.connect(
        "dbname={} user={} password={}".format(DB_NAME, DB_USER, DB_PASS)
    )
    cur = conn.cursor()
    cur.execute(ext_script)
    close_and_commit(cur, conn)


def create_table():
    conn = psycopg2.connect(
        "dbname={} user={} password={}".format(DB_NAME, DB_USER, DB_PASS)
    )
    cur = conn.cursor()
    cur.execute(CREATE_TABLE_SCRIPT)
    close_and_commit(cur, conn)


def add_geometry_column():
    conn = psycopg2.connect(
        "dbname={} user={} password={}".format(DB_NAME, DB_USER, DB_PASS)
    )
    cur = conn.cursor()
    cur.execute(ADD_GEOM_COLUMN_TO_TABLE_SCRIPT)
    close_and_commit(cur, conn)

# TODO: implement and test against what was supplied
# After pass test, move on to attack second question.
# Dockerfile will just be the Postgres and the Flask app communicating with one another
# BUt, we will need to allow for external communication to the Flask app, maybe add nginx as a server?
def calculate_distance_between_points():
    # -- SELECT ST_Distance_Spheroid(geometry(a.geom), geometry(b.geom)) / 1000. as km
    # -- FROM test a, test b
    # -- WHERE a.name='Point1' AND b.name='Point2';
    pass


def create_new_route():
    """
    Gets a new route ID, and commits this to the db
    Returns new route id for the user
    """
    conn = psycopg2.connect(
        "dbname={} user={} password={}".format(DB_NAME, DB_USER, DB_PASS)
    )
    cur = conn.cursor()
    cur.execute(NEW_ROUTE_ID_SCRIPT)
    new_route_id = cur.fetchone()
    if str(new_route_id[0]) == 'None': # TODO test if we need the conversion here
        cur.execute("INSERT INTO routes (route_id, timestamp) VALUES (0, now());")
        close_and_commit(cur, conn)
        return {"route_id": 0}
    cur.execute("INSERT INTO routes (route_id, timestamp) VALUES ({}, now());".format(new_route_id[0]))
    close_and_commit(cur, conn)
    return {"route_id": str(new_route_id[0])}


def update_route(route_id, longitude, latitude):
    """
    Handles date internally
    """
    #   date = datetime.datetime.today().strftime("%d-%m-%Y")
    conn = psycopg2.connect(
        "dbname={} user={} password={}".format(DB_NAME, DB_USER, DB_PASS)
    )
    cur = conn.cursor()
    cur.execute(UPDATE_ROUTE_SCRIPT.format(route_id, longitude, latitude))
    close_and_commit(cur, conn)

def close_and_commit(cur, conn):
    cur.close()
    conn.commit()
    conn.close()

def given_date_query_orders_correctly(date):
    conn = psycopg2.connect(
        "dbname={} user={} password={}".format(DB_NAME, DB_USER, DB_PASS)
    )
    cur = conn.cursor()
    cur.execute(COLLECT_ROUTES_IN_DAY.format(date, date))
    results = cur.fetchall()
    close_and_commit(cur, conn)
    return results

def collect_points_in_route(route_id):
    conn = psycopg2.connect(
        "dbname={} user={} password={}".format(DB_NAME, DB_USER, DB_PASS)
    )
    cur = conn.cursor()
    cur.execute(COLLECT_POINTS_IN_ROUTE_SCRIPT.format(route_id))
    results = cur.fetchall()
    close_and_commit(cur, conn)
    return results



if __name__ == "__main__":
    if DEBUG:
        create_new_database()
        activate_pg_extensions(ADD_POSTGIS_EXT_TO_DB_SCRIPT)
        create_table()
        add_geometry_column()
        create_new_route()
        update_route(0, -25.4025905,  -49.3124416)
        update_route(0, -23.559798,  -46.634971)
        update_route(0, 59.3258414,  17.70188)
        update_route(0,  54.273901,  18.591889)
        print(collect_points_in_route(0))
        print()
        print(given_date_query_orders_correctly(TODAY))
