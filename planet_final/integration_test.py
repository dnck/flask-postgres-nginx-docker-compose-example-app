# -*- coding: utf-8 -*-
"""This module is provided as a client-server integration test.

Example:
    After the Flask app defined in service.py is running,

        $ python integration_test.py

    Constants:
        SECRET_KEY (str): passed to the BOOTSTRAP_ENDPOINT in a POST to
            initialize the database. This is for development purposes only.
        SERVICE_ENDPOINT (str): Flask app is running here
        BOOTSTRAP_ENDPOINT (str): POSTs to this endpoint will call
            the models.initialize_db() method
        ROUTE_ENDPOINT (str): POSTs to this endpoint will request a new route_id
            to be created in the route_lengths table of the service
        ROUTE_ADD_WAY_POINT_ENDPOINT (str): POSTs to this endpoint will
            add the latitude and longitude coordinates to the service routes table
        ROUTE_LENGTH_ENDPOINT (str): GETs to this endpoint formatted with a
            route_id (str) will return the length of the route_id
        ROUTE_LONGEST_ROUTE_IN_DAY_ENDPOINT (str): GETs to this endpoint
            formatted with a query_date (str) %Y-%m-%d will return the
            route_id and its length of the longest route in the query_date.

"""
import datetime
import random
import requests
import time

SECRET_KEY = "hello-planet-labs"
SERVICE_ENDPOINT = "http://localhost:5000/"
BOOTSTRAP_ENDPOINT = "{}initialize_db/".format(SERVICE_ENDPOINT)
ROUTE_ENDPOINT = "{}route/".format(SERVICE_ENDPOINT)
ROUTE_ADD_WAY_POINT_ENDPOINT = "{}{}/way_point/".format(ROUTE_ENDPOINT, "{}")
ROUTE_LENGTH_ENDPOINT = "{}{}/length/".format(ROUTE_ENDPOINT, "{}")
ROUTE_LONGEST_ROUTE_IN_DAY_ENDPOINT = "{}longest-route/{}".format(
    SERVICE_ENDPOINT, "{}"
)


class TestRoute():
    """Class for testing the service from a client perspective"""

    wgs84_coordinates = [
        {"lat": -25.4025905, "lon": -49.3124416},
        {"lat": -23.559798, "lon": -46.634971},
        {"lat": 59.3258414, "lon": 17.70188},
        {"lat": 54.273901, "lon": 18.591889},
    ]

    def setup(self):
        """
        Bootstraps the database with its first past-day record and afterwards,
        creates a new route_id for today, adds the waypoints from instance variable
        wgs84_coordinates, finally querys for the new route_ids length.
        """
        bootstrap_msg = requests.post(BOOTSTRAP_ENDPOINT, json={"key": SECRET_KEY})
        route_id = self.start_new_route()
        self._push_route(route_id)
        self.length_get = requests.get(ROUTE_LENGTH_ENDPOINT.format(route_id))

    def start_new_route(self):
        """Basic method for starting a new route_id

        Returns:
            route_id (str): the new route_id entered into the db
        """
        self.route_post = requests.post(ROUTE_ENDPOINT)
        route = self.route_post.json()
        return route["route_id"]

    def _push_route(self, route_id):
        """Planet provided function for adding waypoints from wgs84_coordinates"""
        for coordinates in self.wgs84_coordinates:
            requests.post(
                ROUTE_ADD_WAY_POINT_ENDPOINT.format(route_id), json=coordinates
            )

    def test_length_calculation(self):
        """Planet provided test for query on the length of the second route_id
        created by the setup method.
        """
        length = self.length_get.json()
        assert 11750 < length["km"] < 11900

    def test_bootstrap_route_length(self):
        """
        Test that the bootstrap route is within the given interval.
        """
        bootstrap_len = requests.get(ROUTE_LENGTH_ENDPOINT.format(0))
        bootstrap_len = bootstrap_len.json()
        assert 800 < bootstrap_len["km"] < 850

    def test_calculate_longest_route_for_today(self):
        """Test that the longest route for query date of today returns an Error
        per the service definitions:
            "The request will only query days in the past"
        """
        query_date = datetime.datetime.today().strftime("%Y-%m-%d")
        response = requests.get(ROUTE_LONGEST_ROUTE_IN_DAY_ENDPOINT.format(query_date))
        assert response.status_code == 403
        query_result = response.json()
        assert query_result["Error"] == "The request will only query days in the past."

    def test_calculate_longest_route_for_past_day(self):
        """Test that the service returns a result for querys for a previous
        days longest route. The request is formatted with variable query_date (str)
        in the format of %Y-%m-%d. As the service may not have waypoints for
        a particular date, acceptable error messages are caught and checked as well.
        """
        query_date = "1984-01-28"
        response = requests.get(ROUTE_LONGEST_ROUTE_IN_DAY_ENDPOINT.format(query_date))
        query_result = response.json()
        acceptable_error_messages = [
            "The request will only query days in the past.",
            "No routes recorded for {}".format(query_date),
        ]
        if query_result.get("Error"):
            assert response.status_code in [403, 404]
            assert query_result["Error"] in acceptable_error_messages
        else:
            assert "km" in query_result.keys()

    #TODO needs assertions
    def test_random_route(self):
        """
        Randomly requests a new route_id and adds waypoints,
        or attempts to add waypoints to an existing route_id.
        """
        func = random.choice([self._random_route_id, self.start_new_route])
        route_id = func()
        for x in range(random.randint(1, 20)):
            coordinates = self._random_lon_lat()
            response = requests.post(
                ROUTE_ADD_WAY_POINT_ENDPOINT.format(route_id), json=coordinates
            )
            time.sleep(0.25)

    def _random_route_id(self):
        """Helper function for test_random_route

        Returns:
            random route_id (int) in the interval 1 to 10
        """
        return random.randint(1, 10)

    def _random_lon_lat(self):
        """Helper function for test_random_route

        Returns:
            coordinates (dict):
                key: 'lat' (str); value: (float) - a random latitude
                key: 'lon' (str); value: (float) - a random longitude
        """
        lon, lat = random.uniform(-180,180), random.uniform(-90, 90)
        return {"lat": lat, "lon": lon}


def do_all_tests():
    """Function sets up an instance of the class TestRoute, and does the basic
    tests."""
    test_route = TestRoute()
    test_route.setup()
    test_route.test_length_calculation()
    test_route.test_bootstrap_route_length()
    test_route.test_calculate_longest_route_for_today()
    test_route.test_calculate_longest_route_for_past_day()
    test_route.test_random_route()

if __name__ == "__main__":
    do_all_tests()
