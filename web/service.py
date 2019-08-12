from flask import Flask, request
import datetime
import json
import models as db
import logging
import sys

logging.basicConfig(
        stream=sys.stdout,
        level=logging.DEBUG,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%m/%d/%Y %I:%M:%S %p")
"""
The application is a small service.
"""
app = Flask(__name__)


@app.route("/route/", methods=["POST"])
def create_route():
    """
    The service accepts data from a GPS tracker device.

    In the beginning of a track, the service requests a route to be created...
    """
    logging.debug("New route_id requested.")
    new_route = _create_route()
    return json.dumps(new_route), 201


def _create_route():
    """
    If there are no records in the DB,
        return 0 as the route_id
    else,
        return the max route_id in the DB + 1 as the route_id.

    In both case, a new row, (route_id, creation_time, route_length) is stored in the route_lengths table.
    """
    conn, cur = db.execute_pgscript(db.GET_NEW_ROUTE_ID_SCRIPT)
    new_route_id = cur.fetchone()
    if str(new_route_id[0]) == "None":
        logging.debug("Our first track on route_id 0!")
        cur.execute(db.START_NEW_ROUTE_SCRIPT.format(0))
        db.close_and_commit(cur, conn)
        return {"route_id": 0}
    logging.debug("Assigning route_id {} to new route.".format(new_route_id[0]))
    cur.execute(db.START_NEW_ROUTE_SCRIPT.format(new_route_id[0]))
    db.close_and_commit(cur, conn)
    return {"route_id": str(new_route_id[0])}


@app.route("/route/<int:route_id>/way_point/", methods=["POST"])
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
        logging.debug("Caught exception: The user can not add more data points.")
        return (
            json.dumps(
                {
                    "Error": "Route too old! New waypoints can not be added to this route."
                }
            ),
            403,
        )
    else:
        conn, cur = db.execute_pgscript(
        db.UPDATE_ROUTE_SCRIPT.format(route_id, longitude, latitude)
        )
        logging.debug("Updating the route of id {}".format(route_id))
        db.close_and_commit(cur, conn)


def is_origin_time_older_than_today(route_id):
    conn, cur = db.execute_pgscript(db.CHECK_ORIGIN_TIME_SCRIPT.format(route_id))
    creation_time = cur.fetchone()
    creation_time = creation_time[0].strftime("%Y-%m-%d")
    older_than_today = is_query_date_older_than_today(creation_time)
    if older_than_today:
        return True
    else:
        return False


@app.route("/route/<int:route_id>/length/")
def calculate_length(route_id):
    """
    Eventually a request to get the length of the route is made.
    """
    print(route_id)
    result = _get_length_of_single_route(route_id)
    return json.dumps({"km": result})


def _get_length_of_single_route(route_id):
    """
    In this method, Postgres server is called on to service a request
    for the length of a route.

    The method stores the route_id's length (km) in the route_lengths table.

    returns length (km) of route_id.
    """
    older_than_today = is_origin_time_older_than_today(route_id)
    if older_than_today:
        logging.debug("Finding the length of route_id = {}".format(route_id))
        conn, cur = db.execute_pgscript(db.SINGLE_ROUTE_LENGTH_QUERY.format(route_id))
        length_of_route = cur.fetchone()
        db.close_and_commit(cur, conn)
        conn, cur = db.execute_pgscript(
            db.UPDATE_ROUTE_LENGTH_SCRIPT.format(length_of_route[0], route_id)
        )
        db.close_and_commit(cur, conn)
        logging.debug("TODO: Conditional checks on these queries.")
        return result[0]
    else:
        json.dumps(
            {
                "Error": "Route too new! New waypoints may still be added today."
            }
        ),
        403,


# TODO
# Actually, we should not just return the single value, but we should update
# All records for the day
# We will make this fast by putting the nginx server with its caching features
# on top of the app.
# Over time, we will always have many of the records stored simply by single
# requests.
@app.route("/longest-route/<string:query_date>")
def calculate_longest_route_for_day(query_date):
    """
    There is also a second part of the challenge which is to calculate the longest path for each day.

    ... past days can't have new routes included, nor new points added to routes from past days.
    """
    query_older_than_today = is_query_date_older_than_today(query_date)
    if not query_older_than_today:
        return (
            json.dumps({"Error": "The request will only query days in the past."}),
            403,
        )
    """
    The request is for a date older than today, so we query the
    Postgres server with a longest-route script. This script returns a route_id that maps to the max(km) traveled within a given day by a route.
    """
    conn, cur = db.execute_pgscript(
        db.LONGEST_ROUTE_IN_DAY_QUERY.format(query_date, query_date)
    )
    longest_route_in_a_day = cur.fetchone()
    if longest_route_in_a_day:
        return (
            json.dumps({"date": query_date, "route_id": longest_route_in_a_day[0], "km": longest_route_in_a_day[1]}),
            201,
        )
    else:
        return (
            json.dumps({"Error": "No routes recorded for {}".format(query_date)}),
            404,
        )

def is_query_date_older_than_today(query_date):
    """
    the request will only query days in the past
    """
    today = datetime.datetime.today()  # .strftime("%Y-%m-%d")
    query_datetime_obj = datetime.datetime.strptime(query_date, "%Y-%m-%d")
    days_since_today = (today - query_datetime_obj).days
    if days_since_today < 1:
        return False
    else:
        return True
