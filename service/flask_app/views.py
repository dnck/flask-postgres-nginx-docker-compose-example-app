# -*- coding: utf-8 -*-
"""Flask app for accepting GPS tracking data.

The service.py here adheres to the user story defined in the project
root ./README_USER_STORY.md file. For this reason, we repeat certain lines
from the user-story within this service to mark out how the user demands
map to code. Lines from the user-story are annotated with >>.

Example:
    It is best to just use docker-compose from the parent directory.

        $ cd .. && docker-compose up

"""
import datetime
import json
import logging
import sys

from flask import Flask, request

import controller
import models

logging.basicConfig(
    stream=sys.stdout,
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%m/%d/%Y %I:%M:%S %p",
)

# >> The application is a small service.
APP = Flask(__name__)


SECRET = "hello"


@APP.route("/initialize_db/", methods=["POST"])
def initialize_db():
    """bootstrap_endpoint

    Bootstraps the database using the models.initialize_db() method.

    Returns:
        dict, 201 response code: success
        dict, 500 response code: failure

    """
    secret_key = request.get_json()
    if secret_key["key"] == SECRET:
        models.initialize_db()
        exists = models.db_exists(models.DB_NAME)
        routes_table_exists = models.table_exists("routes")
        route_lengths_exists = models.table_exists("route_lengths")
        assert exists == routes_table_exists == route_lengths_exists
        APP.logger.info("PostGres DB with tables is online.")
        return (
            json.dumps({"Success!": "PostGres DB with postgis extensions is created."}),
            201,
        )
    APP.logger.warn("Error! Failed to initialize the db.")
    return json.dumps({"Error": "Failed to initialize the db"}), 500


@APP.route("/route/", methods=["POST"])
def create_route():
    """route_endpoint

    >> The service accepts data from a GPS tracker device.
    >> In the beginning of a track, the service requests a route to be created...
    """
    APP.logger.debug("New route_id requested.")
    new_route = controller.create_route()
    APP.logger.debug("New route_id assigned: %s.", new_route)
    return json.dumps(new_route), 201


@APP.route("/route/<int:route_id>/way_point/", methods=["POST"])
def add_way_point(route_id):
    """route_add_way_point_endpoint

    >> It continuously populates the route with data points (WGS84 coordinates).
    >> A route is expected to be done within a day.
    >> After a day, the user can not add more data points.

    Args:
        route_id (int): A route_id supplied by the user in the POST

    Returns:
        dict, 201 response code:
        dict, 404 response code: if the route_id does not exist in the dict, route_lengths table
        dict, 403 response code: if the creation time of the route_id is older than today
    """
    coordinates = request.get_json()
    assert "lat" in coordinates# Good! Sanitize the input. Check that this is
    assert "lon" in coordinates# done elsewhere in the code. It is good!
    return controller.update_route(route_id, coordinates["lon"], coordinates["lat"])


@APP.route("/route/<int:route_id>/length/")
def calculate_length(route_id):
    """route_length_endpoint

    >> Eventually a request to get the length of the route is made.'

    "Eventually" is ambiguous, so we allow for queries on the length of a
    route that is still in progress.

    Args:
        route_id (int): A route_id supplied by the user in a POST

    Returns:
        dict, 201 response code: success
        dict, 404 response code: if the route_id has no waypoints
    """
    route_id_has_waypoints = controller.route_id_has_waypoints(route_id)
    if not route_id_has_waypoints:
        return (
            json.dumps(
                {"Error": "route_id {} has not added any waypoints".format(route_id)}
            ),
            404,
        )
    length_of_route = controller.get_length_of_single_route(route_id)
    return json.dumps({"route_id": route_id, "km": length_of_route[0]}), 201



@APP.route("/longest-route/<string:query_date>")
def calculate_longest_route_for_day(query_date):
    """route_longest_route_in_day_endpoint

    >> There is also a second part of the challenge which is to calculate
    >> the longest path for each day.
    >> past days can't have new routes included,
    >> nor new points added to routes from past days.

    Args:
        query_date (str): in the form of %Y-%m-%d

    Returns:
        dict, 201 response code: if there were waypoints for query_date older than today
        dict, 403 response code): if the route_id was created today
        dict, 404 response code: if there are no waypoints for query_date
    """
    if controller.query_date_is_in_cache(query_date):# This is db lookuo #1
        return (
            json.dumps(
                {
                    "date": query_date,
                    "route_id": controller.LONGEST_ROUTE_IN_DAY_CACHE[query_date][0],
                    "km": controller.LONGEST_ROUTE_IN_DAY_CACHE[query_date][1],
                }
            ),
            201,
        )

    query_older_than_today = \
        controller.is_query_date_older_than_today(query_date)# ram op

    if not query_older_than_today:
        return (
            json.dumps({"Error": "The request will only query days in the past."}),
            403,
        )
    # This is db lookuo #2
    longest_route_in_a_day = controller.query_longest_route_in_day()

    if longest_route_in_a_day:
        controller.update_long_route_cache(query_date, longest_route_in_a_day)
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


if __name__ == "__main__":
    APP.run(host="0.0.0.0", debug=True)
