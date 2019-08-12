import datetime
import json

from flask import Flask, request
from flask.logging import create_logger
import logging

import models

logging.basicConfig(level=logging.DEBUG)

APP = Flask(__name__)
LOG = create_logger(APP)
SECRET = "hello-planet-labs"

LONGEST_ROUTE_IN_DAY_CACHE = {"1984-01-28": [0, 833.77]}

@APP.route("/initialize_db/", methods=["POST"])
def initialize_db():
    """This must be called before anything else."""
    secret_key = request.get_json()
    if secret_key["key"] == SECRET:
        models.initialize_db_with_extension_and_tables()
        exists = models.db_exists(models.DB_NAME)
        routes_table_exists = models.table_exists("routes")
        route_lengths_exists = models.table_exists("route_lengths")
        assert exists == routes_table_exists == route_lengths_exists
        return json.dumps({"Success!": "PostGres DB with postgis extensions is created."}), 201


@APP.route("/route/", methods=["POST"])
def create_route():
    """
    The service accepts data from a GPS tracker device.

    In the beginning of a track, the service requests a route to be created...
    """
    LOG.debug("New route_id requested.")
    new_route = _create_route()
    return json.dumps(new_route), 201


def _create_route():
    """
    If there are no records in the DB,
        return 0 as the route_id
    else,
        return the max route_id in the DB + 1 as the route_id.

    In both case, a new row, (route_id, creation_time, route_length)
    is stored in the route_lengths table.
    """
    conn, cur = models.execute_pgscript(models.GET_NEW_ROUTE_ID_SCRIPT)
    new_route_id = cur.fetchone()
    if str(new_route_id[0]) == "None":
        LOG.debug("Our first track on route_id 0!")
        cur.execute(models.START_NEW_ROUTE_SCRIPT.format(0))
        models.close_and_commit(cur, conn)
        return {"route_id": 0}
    LOG.debug("Assigning route_id {} to new route.".format(new_route_id[0]))
    cur.execute(models.START_NEW_ROUTE_SCRIPT.format(new_route_id[0]))
    models.close_and_commit(cur, conn)
    return {"route_id": str(new_route_id[0])}


@APP.route("/route/<int:route_id>/way_point/", methods=["POST"])
def add_way_point(route_id):
    """
    It continuously populates the route with data points (WGS84 coordinates).

    A route is expected to be done within a day.

    After a day, the user can not add more data points.
    """
    coordinates = request.get_json()
    assert "lat" in coordinates
    assert "lon" in coordinates
    _update_route(route_id, coordinates["lon"], coordinates["lat"])
    return "OK", 201


def _update_route(route_id, longitude, latitude):
    """
    If the user tries to update an old route,
        then they receive a 403 response with a helpful message for debugging.
    """
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
        models.UPDATE_ROUTE_SCRIPT.format(route_id, longitude, latitude)
    )
    LOG.debug("Updating the route of id {}".format(route_id))
    models.close_and_commit(cur, conn)
    return "OK", 201


def is_origin_time_older_than_today(route_id):
    """
    A simple check that helps prevent queries for longest routes of the
    current day.
    """
    conn, cur = models.execute_pgscript(
        models.CHECK_ORIGIN_TIME_SCRIPT.format(route_id)
    )
    creation_time = cur.fetchone()
    models.close_and_commit(cur, conn)
    creation_time = creation_time[0].strftime("%Y-%m-%d")
    older_than_today = is_query_date_older_than_today(creation_time)
    return older_than_today


@APP.route("/route/<int:route_id>/length/")
def calculate_length(route_id):
    """
    'Eventually a request to get the length of the route is made.'

    "Eventually" here is ambiguous, so we allow for queries on the length of a
    route that is still in progress.
    """
    length_of_route = _get_length_of_single_route(route_id)
    return json.dumps({"route_id": route_id, "km": length_of_route[0]}), 201


def _get_length_of_single_route(route_id):
    """
    The Postgres server is called on to service a request
    for the length of a route.

    returns length (km) of route_id.
    """
    LOG.debug("Finding the length of route_id = {}".format(route_id))
    conn, cur = models.execute_pgscript(
        models.SINGLE_ROUTE_LENGTH_QUERY.format(route_id)
    )
    length_of_route = cur.fetchone()
    models.close_and_commit(cur, conn)
    return length_of_route


@APP.route("/longest-route/<string:query_date>")
def calculate_longest_route_for_day(query_date):
    """
    There is also a second part of the challenge which is to calculate
    the longest path for each day.
    ...
    past days can't have new routes included,
    nor new points added to routes from past days.
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
    #The request is for a date older than today, so we query the
    #Postgres server with a longest-route script.
    #This script maps a route_id to the max(km)
    #traveled within a given day.
    conn, cur = models.execute_pgscript(
        models.LONGEST_ROUTE_IN_DAY_QUERY.format(query_date, query_date)
    )
    longest_route_in_a_day = cur.fetchone()
    models.close_and_commit(cur, conn)
    # It is possible there were no routes for that day, so we check
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
    return (
        json.dumps({"Error": "No routes recorded for {}".format(query_date)}),
        404,
        )


def query_date_is_in_cache(query_date):
    """A simple check that the query date is in the check"""
    return query_date in LONGEST_ROUTE_IN_DAY_CACHE


def update_long_route_cache(query_date, longest_route_in_a_day):
    """
    'This information is expected to be highly requested'

    If the query date was not in the cache, we update the cache with this
    new information.
    """
    LONGEST_ROUTE_IN_DAY_CACHE.update(
        {query_date: [longest_route_in_a_day[0], longest_route_in_a_day[1]]}
    )


def is_query_date_older_than_today(query_date):
    """
    'the request will only query days in the past'
    """
    today = datetime.datetime.today()
    query_datetime_obj = datetime.datetime.strptime(query_date, "%Y-%m-%d")
    days_since_today = (today - query_datetime_obj).days
    if days_since_today < 1:
        return False
    return True


if __name__ == "__main__":
    APP.run(host="0.0.0.0", debug=True)
