# -*- coding: utf-8 -*-
"""Example Google style docstrings.

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
import datetime

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

import querys

#TODO Remove this today variable
TODAY = datetime.datetime.now().strftime("%m-%d-%Y")

PERSISTENCE_PROVIDER = "postgres"
DB_HOST = "db"
DB_PORT = 5432
DB_USER = "postgres"
DB_PASS = "password"
DB_NAME = "planet"

def create_new_database():
    """Example function with types documented in the docstring.

    `PEP 484`_ type annotations are supported. If attribute, parameter, and
    return types are annotated according to `PEP 484`_, they do not need to be
    included in the docstring:

    Args:
        param1 (int): The first parameter.
        param2 (str): The second parameter.

    Returns:
        bool: The return value. True for success, False otherwise.

    .. _PEP 484:
        https://www.python.org/dev/peps/pep-0484/

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
    """Example function with types documented in the docstring.

    `PEP 484`_ type annotations are supported. If attribute, parameter, and
    return types are annotated according to `PEP 484`_, they do not need to be
    included in the docstring:

    Args:
        param1 (int): The first parameter.
        param2 (str): The second parameter.

    Returns:
        bool: The return value. True for success, False otherwise.

    .. _PEP 484:
        https://www.python.org/dev/peps/pep-0484/

    """
    conn, cur = execute_pgscript(querys.ADD_POSTGIS_TO_DB)
    close_and_commit(cur, conn)
    return True


def create_route_table():
    """Example function with types documented in the docstring.

    `PEP 484`_ type annotations are supported. If attribute, parameter, and
    return types are annotated according to `PEP 484`_, they do not need to be
    included in the docstring:

    Args:
        param1 (int): The first parameter.
        param2 (str): The second parameter.

    Returns:
        bool: The return value. True for success, False otherwise.

    .. _PEP 484:
        https://www.python.org/dev/peps/pep-0484/

    """
    conn, cur = execute_pgscript(querys.CREATE_ROUTE_TABLE)
    close_and_commit(cur, conn)
    return True


def create_route_length_table():
    """Example function with types documented in the docstring.

    `PEP 484`_ type annotations are supported. If attribute, parameter, and
    return types are annotated according to `PEP 484`_, they do not need to be
    included in the docstring:

    Args:
        param1 (int): The first parameter.
        param2 (str): The second parameter.

    Returns:
        bool: The return value. True for success, False otherwise.

    .. _PEP 484:
        https://www.python.org/dev/peps/pep-0484/

    """
    conn, cur = execute_pgscript(querys.CREATE_ROUTE_LEN_TABLE)
    close_and_commit(cur, conn)


def add_geometry_column_to_table():
    """Example function with types documented in the docstring.

    `PEP 484`_ type annotations are supported. If attribute, parameter, and
    return types are annotated according to `PEP 484`_, they do not need to be
    included in the docstring:

    Args:
        param1 (int): The first parameter.
        param2 (str): The second parameter.

    Returns:
        bool: The return value. True for success, False otherwise.

    .. _PEP 484:
        https://www.python.org/dev/peps/pep-0484/

    """
    conn, cur = execute_pgscript(querys.ADD_GEOM_COLUMN_TO_TABLE.format("routes"))
    close_and_commit(cur, conn)


def bootstrap_tables():
    """Example function with types documented in the docstring.

    `PEP 484`_ type annotations are supported. If attribute, parameter, and
    return types are annotated according to `PEP 484`_, they do not need to be
    included in the docstring:

    Args:
        param1 (int): The first parameter.
        param2 (str): The second parameter.

    Returns:
        bool: The return value. True for success, False otherwise.

    .. _PEP 484:
        https://www.python.org/dev/peps/pep-0484/

    """
    conn, cur = execute_pgscript(querys.ADD_TRANSACTION_ROW_0)
    close_and_commit(cur, conn)
    conn, cur = execute_pgscript(querys.ADD_TRANSACTION_ROW_1)
    close_and_commit(cur, conn)
    conn, cur = execute_pgscript(querys.ADD_TRANSACTION_ROW_2)
    close_and_commit(cur, conn)


def execute_pgscript(pgscript):
    """Example function with types documented in the docstring.

    `PEP 484`_ type annotations are supported. If attribute, parameter, and
    return types are annotated according to `PEP 484`_, they do not need to be
    included in the docstring:

    Args:
        param1 (int): The first parameter.
        param2 (str): The second parameter.

    Returns:
        bool: The return value. True for success, False otherwise.

    .. _PEP 484:
        https://www.python.org/dev/peps/pep-0484/

    """
    conn = psycopg2.connect(
        host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASS
    )
    cur = conn.cursor()
    cur.execute(pgscript)
    return conn, cur


def db_exists(db_name):
    """Example function with types documented in the docstring.

    `PEP 484`_ type annotations are supported. If attribute, parameter, and
    return types are annotated according to `PEP 484`_, they do not need to be
    included in the docstring:

    Args:
        param1 (int): The first parameter.
        param2 (str): The second parameter.

    Returns:
        bool: The return value. True for success, False otherwise.

    .. _PEP 484:
        https://www.python.org/dev/peps/pep-0484/

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
    """Example function with types documented in the docstring.

    `PEP 484`_ type annotations are supported. If attribute, parameter, and
    return types are annotated according to `PEP 484`_, they do not need to be
    included in the docstring:

    Args:
        param1 (int): The first parameter.
        param2 (str): The second parameter.

    Returns:
        bool: The return value. True for success, False otherwise.

    .. _PEP 484:
        https://www.python.org/dev/peps/pep-0484/

    """
    exists = False
    try:
        conn, cur = \
            execute_pgscript(querys.TABLE_EXISTS.format(table_name))
        exists = cur.fetchone()[0]
    except psycopg2.Error as err:
        close_and_commit(cur, conn)
        return err
    close_and_commit(cur, conn)
    return exists


def drop_table(table_name):
    """Example function with types documented in the docstring.

    `PEP 484`_ type annotations are supported. If attribute, parameter, and
    return types are annotated according to `PEP 484`_, they do not need to be
    included in the docstring:

    Args:
        param1 (int): The first parameter.
        param2 (str): The second parameter.

    Returns:
        bool: The return value. True for success, False otherwise.

    .. _PEP 484:
        https://www.python.org/dev/peps/pep-0484/

    """
    conn, cur = execute_pgscript(querys.DROP_TABLE.format(table_name))
    close_and_commit(cur, conn)
    return True


def drop_database():
    """Example function with types documented in the docstring.

    `PEP 484`_ type annotations are supported. If attribute, parameter, and
    return types are annotated according to `PEP 484`_, they do not need to be
    included in the docstring:

    Args:
        param1 (int): The first parameter.
        param2 (str): The second parameter.

    Returns:
        bool: The return value. True for success, False otherwise.

    .. _PEP 484:
        https://www.python.org/dev/peps/pep-0484/

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
    """Example function with types documented in the docstring.

    `PEP 484`_ type annotations are supported. If attribute, parameter, and
    return types are annotated according to `PEP 484`_, they do not need to be
    included in the docstring:

    Args:
        param1 (int): The first parameter.
        param2 (str): The second parameter.

    Returns:
        bool: The return value. True for success, False otherwise.

    .. _PEP 484:
        https://www.python.org/dev/peps/pep-0484/

    """
    cur.close()
    conn.commit()
    conn.close()

def initialize_db():
    """Example function with types documented in the docstring.

    `PEP 484`_ type annotations are supported. If attribute, parameter, and
    return types are annotated according to `PEP 484`_, they do not need to be
    included in the docstring:

    Args:
        param1 (int): The first parameter.
        param2 (str): The second parameter.

    Returns:
        bool: The return value. True for success, False otherwise.

    .. _PEP 484:
        https://www.python.org/dev/peps/pep-0484/

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
