# -*- coding: utf-8 -*-
"""models.py contains basic psycopg2 scripts for interacting with the db.

models.py is imported by the views.py Flask application.

"""

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

import querys

PERSISTENCE_PROVIDER = "postgres"
DB_HOST = "db"
DB_PORT = 5432
DB_USER = "postgres"
DB_PASS = "password"
DB_NAME = "gps_tracker_service"


def create_new_database():
    """
    Creates a database DB_NAME (module constant) using the default constants.

    Returns:
        bool: True for success

    """
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=PERSISTENCE_PROVIDER,
        user=DB_USER,
        password=DB_PASS,
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    cur.execute(querys.CREATE_DB.format(DB_NAME))
    close_and_commit(cur, conn)
    return True


def activate_postgis_extension():
    """Turns on the postgis extension in the postgres database, DB_NAME

    Returns:
        bool: True for success

    """
    conn, cur = execute_pgscript(querys.ADD_POSTGIS_TO_DB)
    close_and_commit(cur, conn)
    return True


def create_route_table():
    """Creates the routes table in db DB_NAME

    Returns:
        bool: True for success

    """
    conn, cur = execute_pgscript(querys.CREATE_ROUTE_TABLE)
    close_and_commit(cur, conn)
    return True


def create_route_length_table():
    """Creates the route_lengths table in db DB_NAME

    Returns:
        bool: True for success,

    """
    conn, cur = execute_pgscript(querys.CREATE_ROUTE_LEN_TABLE)
    close_and_commit(cur, conn)
    return True


def add_geometry_column_to_table():
    """Adds a Geometry type column to the routes table in db DB_NAME

    Returns:
        bool: True for success

    """
    conn, cur = execute_pgscript(querys.ADD_GEOM_COLUMN_TO_TABLE.format("routes"))
    close_and_commit(cur, conn)
    return True


def bootstrap_tables():
    """Creates first records in the route and route_lengths tables"""
    conn, cur = execute_pgscript(querys.ADD_TRANSACTION_ROW_0)
    close_and_commit(cur, conn)
    conn, cur = execute_pgscript(querys.ADD_TRANSACTION_ROW_1)
    close_and_commit(cur, conn)
    conn, cur = execute_pgscript(querys.ADD_TRANSACTION_ROW_2)
    close_and_commit(cur, conn)


def execute_pgscript(pgscript):
    """General method for querying the database DB_NAME with the supplied pgscript

    Args:
        pgscript (str): a postgres SQL script from the querys.py module

    Returns:
        tuple (conn, cur)
            WHERE
            conn is the connection used to connect to the db DB_NAME
            cur is the cursor used to retrieve results from the query

    """
    conn = psycopg2.connect(
        host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASS
    )
    cur = conn.cursor()
    cur.execute(pgscript)
    return conn, cur


def db_exists(db_name):
    """Checks that the db db_name exists in the public schemas of PERSISTENCE_PROVIDER

    Args:
        db_name (str): the db name to check for existence

    Returns:
        bool: True for success, False otherwise.

    """
    exists = ""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=PERSISTENCE_PROVIDER,
            user=DB_USER,
            password=DB_PASS,
        )
        cur = conn.cursor()
        cur.execute(querys.DB_EXISTS.format(db_name))
        exists = cur.fetchone()
    except psycopg2.Error as err:
        close_and_commit(cur, conn)
        return err
    close_and_commit(cur, conn)
    if exists and exists[0] == db_name:
        return True
    return False


def table_exists(table_name):
    """Checks that the param table_name exists in module constant DB_NAME

    Args:
        table_name (str): the db name to check for existence

    Returns:
        bool: True for success, False otherwise.

    """
    exists = False
    try:
        conn, cur = execute_pgscript(querys.TABLE_EXISTS.format(table_name))
        exists = cur.fetchone()[0]
    except psycopg2.Error as err:
        close_and_commit(cur, conn)
        return err
    close_and_commit(cur, conn)
    return exists


def drop_table(table_name):
    """Drops table_name in DB_NAME if it exists

    Args:
        table_name (str): The table name to drop

    Returns:
        bool: True for success

    """
    conn, cur = execute_pgscript(querys.DROP_TABLE.format(table_name))
    close_and_commit(cur, conn)
    return True


def drop_database():
    """Drops db DB_NAME from the public schemas of PERSISTENCE_PROVIDER

    Returns:
        bool: True for success

    """
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=PERSISTENCE_PROVIDER,
        user=DB_USER,
        password=DB_PASS,
    )
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute(querys.DROP_DB.format(DB_NAME))
    close_and_commit(cur, conn)
    return True


def close_and_commit(cur, conn):
    """Closes the cursor and connection used to query a db,
    also commits the transaction.

    Args:
        cur (int): the connection used to connect to the db DB_NAME
        conn (str): the cursor used to retrieve results from the query

    """
    cur.close()
    conn.commit()
    conn.close()


def initialize_db():
    """Initialize the database and tables

    This function checks for the existence of the DB_NAME. If it does not
    exist, the function creates it and activates the postgis extension. Next,
    it checks for the existence of the tables, routes and route_lengths, and
    creates them if they do not exist, adding a Geometry type column to the
    routes table. Finally, it bootstraps both tables by adding route_id 0
    to the routes_lengths table with a date in the far past, and two way points
    for the route_id 0 in the routes table.

    Returns:
        bool: True for success.

    """
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
        bootstrap_tables()
    return True
