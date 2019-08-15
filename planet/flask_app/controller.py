import logging
import json
import models
import datetime

logging.basicConfig(level=logging.DEBUG)

LONGEST_ROUTE_IN_DAY_CACHE = {"1984-01-28": [0, 833.77]}

def create_route():
    """
    If there are no records in the DB, the service returns 0 as the route_id
    else, it returns the max route_id from the route_lengths table + 1 as
    the route_id.

    In both case, a new row,
        (route_id, creation_time, route_length)
    is stored in the route_lengths table.

    Returns:
        dict
            'route_id' (str): route_id (int)
    """
    conn, cur = models.execute_pgscript(models.querys.GET_NEW_ROUTE_ID)
    new_route_id = cur.fetchone()
    if str(new_route_id[0]) == "None":
        logging.info( # This check is essential to the test
            "Our first track on route_id 0!" # The body of the condition
            ) # should only ever execute after the first zero transaction.
        cur.execute(models.querys.START_NEW_ROUTE.format(0))
        models.close_and_commit(cur, conn)
        return {"route_id": 0}
    logging.debug("Assigning route_id {} to new route...".format(new_route_id[0]))
    cur.execute(models.querys.START_NEW_ROUTE.format(new_route_id[0]))
    models.close_and_commit(cur, conn)
    return {"route_id": str(new_route_id[0])}


def update_route(route_id, longitude, latitude):
    """
    If the user tries to update an stale route (older than 1 day),
        then they receive a 403 response with a helpful message for debugging.

    Args:
        route_id (int): A route_id supplied by the user in the POST
        longitude (float): the longitude supplied by the user in the POST
        latitude (float): the latitude supplied by the user in the POST

    Returns:
        dict, 201 response code: success
        dict, 404 response code: if the route_id does not exist in the route_lengths table
        dict, 403 response code: if the creation time of the route_id is older than today

    """
    route_id_exist = route_id_exists(route_id)
    if not route_id_exist:
        # Now would be a good time to check on the client ip address
        return json.dumps({"Error": "route_id does not exist!"}), 404

    older_than_today = is_origin_time_older_than_today(route_id)
    if older_than_today:
        logging.debug("Error: You can not add more data points to this object.")
        return (
            json.dumps(
                {
                    "Error": "You can not add more data points to this object."
                }
            ),
            403,
        )

    conn, cur = models.execute_pgscript(
        models.querys.UPDATE_ROUTE.format(route_id, longitude, latitude)
    )
    models.close_and_commit(cur, conn)
    return json.dumps({"Ok": "Updated waypoint for route_id".format(route_id)}), 201

def route_id_exists(route_id):
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
            True if the route_id was created in a previous day,
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



def get_length_of_single_route(route_id):
    """
    The Postgres server is called on to service a request for the length of
    a route.

    Args:
        route_id (int): A route_id supplied by the user in a POST

    Returns:
        length_of_route (float): length (km) of route_id
    """
    logging.debug("Finding the length of route_id = {}".format(route_id))
    conn, cur = models.execute_pgscript(
        models.querys.SINGLE_ROUTE_LENGTH.format(route_id)
    )
    length_of_route = cur.fetchone()
    models.close_and_commit(cur, conn)
    return length_of_route


def route_id_has_waypoints(route_id):
    """A check that the route_id has waypoints added to it.

    Args:
        route_id (int): A route_id supplied by the user in a POST

    Returns:
        bool:
            True if the route_id has waypoints in the routes table;
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

def query_longest_route_in_day():
    conn, cur = models.execute_pgscript(
        models.querys.LONGEST_ROUTE_IN_DAY.format(query_date, query_date)
    )
    longest_route_in_a_day = cur.fetchone()
    models.close_and_commit(cur, conn)



def query_date_is_in_cache(query_date):
    """A simple check that the query date is in the check

    Args:
        query_date (str): in the form of %Y-%m-%d

    """
    return query_date in LONGEST_ROUTE_IN_DAY_CACHE


def update_long_route_cache(query_date, longest_route_in_a_day):
    """
    >> This information is expected to be highly requested
    If the query date was not in the cache, we update the cache with this
    new information.

    Args:
        query_date (str): %Y-%m-%d format

        longest_route_in_a_day (dict):
            e.g.
            {
            'date' (str): val (str) - date for which the route_id is the longest,
            'route_id': val (int) - id of route,
            'km' (str): val (float) - length in km of route
             }
    """
    LONGEST_ROUTE_IN_DAY_CACHE.update(
        {query_date: [longest_route_in_a_day[0], longest_route_in_a_day[1]]}
    )


def is_query_date_older_than_today(query_date):
    """A check that prevents longest route querys for the current day.

    >> the request will only query days in the past

    Returns:
        bool: True if the query_date is not today, false otherwise

    """
    today = datetime.datetime.today()
    query_datetime_obj = datetime.datetime.strptime(query_date, "%Y-%m-%d")
    days_since_today = (today - query_datetime_obj).days
    if days_since_today < 1:
        return False
    return True
