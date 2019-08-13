# -*- coding: utf-8 -*-
"""Flask app for accepting GPS tracking data.

The service.py here adheres to the user story defined in the project
root ./README_USER_STORE.md file. For this reason, we repeat certain lines
from the user-story within this service to mark out how the user demands
map to code. Lines from the user-story are preceeded by the > symbol

Example:
    It is best to just use docker-compose from the parent directory.

        $ cd .. && docker-compose up

"""
import datetime
import json
import logging

from flask import Flask, request
from flask.logging import create_logger

import models

logging.basicConfig(level=logging.DEBUG)
# > The application is a small service.
APP = Flask(__name__)
LOG = create_logger(APP)
SECRET = "hello-planet-labs"

LONGEST_ROUTE_IN_DAY_CACHE = {"1984-01-28": [0, 833.77]}


@APP.route("/initialize_db/", methods=["POST"])
def initialize_db():
    """Bootstraps the database using the models.initialize_db() method.

    Returns:
        201 response code - success
        500 response code - failure

    """
    secret_key = request.get_json()
    if secret_key["key"] == SECRET:
        models.initialize_db()
        exists = models.db_exists(models.DB_NAME)
        routes_table_exists = models.table_exists("routes")
        route_lengths_exists = models.table_exists("route_lengths")
        assert exists == routes_table_exists == route_lengths_exists
        return (
            json.dumps({"Success!": "PostGres DB with postgis extensions is created."}),
            201,
        )
    return json.dumps({"Error": "Failed to initialize the db"}), 500


@APP.route("/route/", methods=["POST"])
def create_route():
    """
    > The service accepts data from a GPS tracker device.
    > In the beginning of a track, the service requests a route to be created...
    """
    LOG.debug("New route_id requested.")
    new_route = _create_route()
    return json.dumps(new_route), 201


def _create_route():
    """
    If there are no records in the DB, the service returns 0 as the route_id
    else, it returns the max route_id from the route_lengths table + 1 as
    the route_id.

    In both case, a new row,
        (route_id, creation_time, route_length)
    is stored in the route_lengths table.

    Returns:
        dict
            key: 'route_id' (str); value: (int) - new route id
    """
    conn, cur = models.execute_pgscript(models.querys.GET_NEW_ROUTE_ID)
    new_route_id = cur.fetchone()
    if str(new_route_id[0]) == "None":
        LOG.info("Our first track on route_id 0!")
        cur.execute(models.querys.START_NEW_ROUTE.format(0))
        models.close_and_commit(cur, conn)
        return {"route_id": 0}
    LOG.debug("Assigning route_id {} to new route.".format(new_route_id[0]))
    cur.execute(models.querys.START_NEW_ROUTE.format(new_route_id[0]))
    models.close_and_commit(cur, conn)
    return {"route_id": str(new_route_id[0])}


@APP.route("/route/<int:route_id>/way_point/", methods=["POST"])
def add_way_point(route_id):
    """
    > It continuously populates the route with data points (WGS84 coordinates).
    > A route is expected to be done within a day.
    > After a day, the user can not add more data points.

    Args:
        route_id (int): A route_id supplied by the user in the POST

    Returns:
        201 response code - success
        404 response code - if the route_id does not exist in the route_lengths table
        403 response code - if the creation time of the route_id is older than today
    """
    coordinates = request.get_json()
    assert "lat" in coordinates
    assert "lon" in coordinates
    return _update_route(route_id, coordinates["lon"], coordinates["lat"])


def _update_route(route_id, longitude, latitude):
    """
    If the user tries to update an stale route (older than 1 day),
        then they receive a 403 response with a helpful message for debugging.

    Args:
        route_id (int): A route_id supplied by the user in the POST
        longitude (float): the longitude supplied by the user in the POST
        latitude (float): the latitude supplied by the user in the POST

    Returns:
        201 response code - success
        404 response code - if the route_id does not exist in the route_lengths table
        403 response code - if the creation time of the route_id is older than today

    """
    route_id_exists = _route_id_exists(route_id)
    if not route_id_exists:
        return json.dumps({"Error": "route_id does not exist!"}), 404

    older_than_today = is_origin_time_older_than_today(route_id)
    if older_than_today:
        LOG.debug("Caught exception: The user can not add more data points.")
        return (
            json.dumps(
                {
                    "Error": "Route too old! New waypoints can not be added to this route."
                }
            ),
            403,
        )
    conn, cur = models.execute_pgscript(
        models.querys.UPDATE_ROUTE.format(route_id, longitude, latitude)
    )
    LOG.debug("Updating the route of id {}".format(route_id))
    models.close_and_commit(cur, conn)
    return json.dumps({"Ok": "Updated waypoint for route_id".format(route_id)}), 201


def _route_id_exists(route_id):
    """Checks that the route_id exists in the route_lengths table

    Args:
        route_id (int): A route_id supplied by the user in a POST

    Returns:
        bool: True if exist; false otherwise
    """
    conn, cur = models.execute_pgscript(models.querys.ROUTE_ID_EXISTS.format(route_id))
    route_id_exists = cur.fetchone()
    models.close_and_commit(cur, conn)
    if not route_id_exists:
        return False
    return True


def is_origin_time_older_than_today(route_id):
    """A check that prevent updating waypoints for route_ids that are stale

    Args:
        route_id (int): A route_id supplied by the user in a POST

    Returns:
        bool:
            True if the route_id was created in a previous day
            False otherwise
    """
    conn, cur = models.execute_pgscript(
        models.querys.CHECK_ORIGIN_TIME.format(route_id)
    )
    creation_time = cur.fetchone()
    models.close_and_commit(cur, conn)
    creation_time = creation_time[0].strftime("%Y-%m-%d")
    older_than_today = is_query_date_older_than_today(creation_time)
    return older_than_today


@APP.route("/route/<int:route_id>/length/")
def calculate_length(route_id):
    """Route length endpoint

    > Eventually a request to get the length of the route is made.'

    "Eventually" is ambiguous, so we allow for queries on the length of a
    route that is still in progress.

    Args:
        route_id (int): A route_id supplied by the user in a POST

    Returns:
        201 response code - success
        404 response code - if the route_id has no waypoints
    """
    route_id_has_waypoints = _route_id_has_waypoints(route_id)
    #LOG.debug("Route {} has waypoints = {}".format(route_id, route_id_has_waypoints))
    if not route_id_has_waypoints:
        return json.dumps(
            {"Error": "route_id {} has not added any waypoints".format(route_id)}
        ), 404
    length_of_route = _get_length_of_single_route(route_id)
    return json.dumps({"route_id": route_id, "km": length_of_route[0]}), 201


def _get_length_of_single_route(route_id):
    """
    The Postgres server is called on to service a request for the length of
    a route.

    Args:
        route_id (int): A route_id supplied by the user in a POST

    Returns:
        length_of_route (float) - length (km) of route_id
    """
    LOG.debug("Finding the length of route_id = {}".format(route_id))
    conn, cur = models.execute_pgscript(
        models.querys.SINGLE_ROUTE_LENGTH.format(route_id)
    )
    length_of_route = cur.fetchone()
    models.close_and_commit(cur, conn)
    return length_of_route


def _route_id_has_waypoints(route_id):
    """A check that the route_id has waypoints added to it.

    Args:
        route_id (int): A route_id supplied by the user in a POST

    Returns:
        bool:
            True if the route_id has waypoints in the routes table
            False otherwise

    """
    conn, cur = models.execute_pgscript(
        models.querys.ROUTE_ID_HAS_WAYPOINTS.format(route_id)
    )
    route_id_exists = cur.fetchone()
    models.close_and_commit(cur, conn)
    if not route_id_exists:
        return False
    return True


@APP.route("/longest-route/<string:query_date>")
def calculate_longest_route_for_day(query_date):
    """
    > There is also a second part of the challenge which is to calculate
    > the longest path for each day.
    > past days can't have new routes included,
    > nor new points added to routes from past days.

    Args:
        query_date (str): in the form of %Y-%m-%d

    Returns:
        (dict, 201 response code): if there were waypoints for query_date older than today
        (dict, 403 response code): if the route_id was created today
        (dict, 404 response code): if there are no waypoints for query_date
    """
    if query_date_is_in_cache(query_date):
        return (
            json.dumps(
                {
                    "date": query_date,
                    "route_id": LONGEST_ROUTE_IN_DAY_CACHE[query_date][0],
                    "km": LONGEST_ROUTE_IN_DAY_CACHE[query_date][1],
                }
            ),
            201,
        )
    query_older_than_today = is_query_date_older_than_today(query_date)
    if not query_older_than_today:
        return (
            json.dumps({"Error": "The request will only query days in the past."}),
            403,
        )
    # The request is for a date older than today, so we query the
    # Postgres server with a longest-route script.
    # This script maps a route_id to the max(km)
    # traveled within a given day.
    conn, cur = models.execute_pgscript(
        models.querys.LONGEST_ROUTE_IN_DAY.format(query_date, query_date)
    )
    longest_route_in_a_day = cur.fetchone()
    models.close_and_commit(cur, conn)
    if longest_route_in_a_day:
        update_long_route_cache(query_date, longest_route_in_a_day)
        return (
            json.dumps(
                {
                    "date": query_date,
                    "route_id": longest_route_in_a_day[0],
                    "km": longest_route_in_a_day[1],
                }
            ),
            201,
        )
    # It is possible that there were no routes for query_date.
    return (json.dumps({"Error": "No routes recorded for {}".format(query_date)}), 404)


def query_date_is_in_cache(query_date):
    """A simple check that the query date is in the check

    Args:
        query_date (str): in the form of %Y-%m-%d

    """
    return query_date in LONGEST_ROUTE_IN_DAY_CACHE


def update_long_route_cache(query_date, longest_route_in_a_day):
    """
    > This information is expected to be highly requested
    If the query date was not in the cache, we update the cache with this
    new information.

    Args:
        query_date (str): in the form of %Y-%m-%d
        longest_route_in_a_day (dict):
            key (str) 'date': val (str) - date for which the route_id is the longest
            key (str) 'route_id': val (int) - id of route
            key (str) 'km': val (float) - length in km of route
    """
    LONGEST_ROUTE_IN_DAY_CACHE.update(
        {query_date: [longest_route_in_a_day[0], longest_route_in_a_day[1]]}
    )


def is_query_date_older_than_today(query_date):
    """A check that prevents longest route querys for the current day.

    > the request will only query days in the past'

    Returns:
        bool: True if the query_date is not today, false otherwise

    """
    today = datetime.datetime.today()
    query_datetime_obj = datetime.datetime.strptime(query_date, "%Y-%m-%d")
    days_since_today = (today - query_datetime_obj).days
    if days_since_today < 1:
        return False
    return True


if __name__ == "__main__":
    APP.run(host="0.0.0.0", debug=True)
