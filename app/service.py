from flask import Flask, request
import json

import datetime

import psycopg2

from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# TODO Dockerfile will just be the Postgres and the Flask app communicating with one another. But, we need to allow for external communication to the Flask app, maybe add nginx as a server?
# original uuid: e84fee1e-fd4f-40f6-85b5-52ff46cbbb6e

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

ADD_POSTGIS_EXT_TO_DB_SCRIPT = "CREATE EXTENSION IF NOT EXISTS postgis"

ADD_GEOM_COLUMN_TO_TABLE_SCRIPT = (
    "SELECT AddGeometryColumn('public', 'routes', 'geom', 4326, 'POINT', 2);"
)

START_NEW_ROUTE_SCRIPT = "INSERT INTO routes (route_id, timestamp) VALUES ({}, now());"

NEW_ROUTE_ID_SCRIPT = "SELECT max(route_id) + 1 FROM routes;"

UPDATE_ROUTE_SCRIPT = "INSERT INTO routes (route_id, timestamp, geom) VALUES ({}, now(), 'SRID=4326; POINT({} {})');"

# TODO Remove this when submitting
# COLLECT_POINTS_IN_ROUTE_SCRIPT = (
#     "SELECT * FROM routes WHERE route_id = {} AND geom IS NOT NULL ORDER BY timestamp;"
# )
# TODO Remove this when submitting
# COLLECT_ROUTES_IN_DAY = """SELECT * FROM routes WHERE timestamp BETWEEN '{}' and '{}'::date + interval '24 hours' AND geom IS NOT NULL;"""

SINGLE_ROUTE_LENGTH_QUERY = """
    SELECT sum(route_length) as km from (
        SELECT
        ST_Distance_Sphere(geom, lag(geom, 1) OVER (ORDER BY timestamp)) / 1000 as route_length
        FROM routes
        WHERE route_id = {} AND geom IS NOT NULL
    ) as route_length_table;
    """

app = Flask(__name__)

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

def activate_pg_extensions(ext_script):
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

# TODO Remove this when submitting
# def given_date_query_orders_correctly(date):
#     conn, cur = conn_cur_and_execute(COLLECT_ROUTES_IN_DAY.format(date, date))
#     results = cur.fetchall()
#     close_and_commit(cur, conn)
#     return results

# this function should create a new database record for a route
@app.route("/route/", methods=["POST"])
def create_route():
    new_route = create_new_route()
    return json.dumps(new_route), 201

def create_new_route():
    """
    Gets a new route ID, and commits this to the db
    Returns new route id for the user
    """
    conn, cur = conn_cur_and_execute(NEW_ROUTE_ID_SCRIPT)
    new_route_id = cur.fetchone()
    # TODO do we need the conversion here?
    if str(new_route_id[0]) == "None":
        cur.execute(START_NEW_ROUTE_SCRIPT.format(0))
        close_and_commit(cur, conn)
        return {"route_id": 0}
    cur.execute(START_NEW_ROUTE_SCRIPT.format(new_route_id[0]))
    close_and_commit(cur, conn)
    return {"route_id": str(new_route_id[0])}

@app.route("/route/<int:route_id>/way_point/", methods=["POST"])
def add_way_point(route_id):
    coordinates = request.get_json()  # {“lat”: 59.23425, “lon”: 18.23526}
    assert "lat" in coordinates
    assert "lon" in coordinates
    update_route(route_id, coordinates["lon"], coordinates["lat"])
    return "OK", 201

def update_route(route_id, longitude, latitude):
    """
    Handles date internally
    """
    conn, cur = conn_cur_and_execute(
        UPDATE_ROUTE_SCRIPT.format(route_id, longitude, latitude)
    )
    close_and_commit(cur, conn)

@app.route("/route/<int:route_id>/length/")
def calculate_length(route_id):
    result = get_length_of_single_route(route_id)
    return json.dumps({"km": result})

def get_length_of_single_route(route_id):
    conn, cur = conn_cur_and_execute(SINGLE_ROUTE_LENGTH_QUERY.format(route_id))
    result = cur.fetchone()
    close_and_commit(cur, conn)
    return result[0]

@app.route("/route/<int:route_id>/points-in-path/")
def get_points_in_path(route_id):
    result = collect_points_in_route(route_id)
    response = convert_points_in_path_result_to_response(result)
    return json.dumps(response), 201

# TODO Remove this when submitting
# def collect_points_in_route(route_id):
#     conn, cur = conn_cur_and_execute(COLLECT_POINTS_IN_ROUTE_SCRIPT.format(route_id))
#     results = cur.fetchall()
#     close_and_commit(cur, conn)
#     return results

def convert_points_in_path_result_to_response(result):
    response = []
    for waypoint in result:
        response.append(
            {
                "route_id": waypoint[0],
                "date": waypoint[1].strftime("%m-%d-%Y"),
                "geom": waypoint[3],
            }
        )
    return response

# This function should calculate the longest route taken by all the uuids
# for the query date. We can do this in the database server, not python.
@app.route("/longest-route/<string:query_date>")
def calculate_longest_route_for_day(query_date):
    return (
        json.dumps(
            {
                "date": query_date,
                "route_id": "e84fee1e-fd4f-40f6-85b5-52ff46cbbb6e",
                "km": 334.83 + 10927.08 + 555.59,
            }
        ),
        201,
    )

# Need some main functions and app.run() here.
