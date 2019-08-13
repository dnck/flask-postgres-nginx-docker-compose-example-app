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
import unittest

SECRET_KEY = "hello-planet-labs"
SERVICE_ENDPOINT = "http://localhost:5000/"
BOOTSTRAP_ENDPOINT = "{}initialize_db/".format(SERVICE_ENDPOINT)
ROUTE_ENDPOINT = "{}route/".format(SERVICE_ENDPOINT)
ROUTE_ADD_WAY_POINT_ENDPOINT = "{}{}/way_point/".format(ROUTE_ENDPOINT, "{}")
ROUTE_LENGTH_ENDPOINT = "{}{}/length/".format(ROUTE_ENDPOINT, "{}")
ROUTE_LONGEST_ROUTE_IN_DAY_ENDPOINT = "{}longest-route/{}".format(
    SERVICE_ENDPOINT, "{}"
)


class TestRoute(unittest.TestCase):
    """Class for testing the service from a client perspective"""

    wgs84_coordinates = [
        {"lat": -25.4025905, "lon": -49.3124416},
        {"lat": -23.559798, "lon": -46.634971},
        {"lat": 59.3258414, "lon": 17.70188},
        {"lat": 54.273901, "lon": 18.591889},
    ]

    def setUp(self):
        """
        Bootstraps the database with its first past-day record and afterwards,
        creates a new route_id for today, adds the waypoints from instance variable
        wgs84_coordinates, and finally querys for the new route_ids length.

        This method can be run multiple times without over-writing the db,
        thanks to the checks in the models.initialize_db() method.
        """
        bootstrap_msg = requests.post(BOOTSTRAP_ENDPOINT, json={"key": SECRET_KEY})

    def test_planet_provided(self):
        """Planet provided test for query on the length of the wgs84_coordinates added to the db.

        Refactored from: self.test_length_calculation()
        """
        route_id = self._start_new_route()
        self._push_route(route_id)
        length_get = requests.get(ROUTE_LENGTH_ENDPOINT.format(route_id))
        length = length_get.json()
        assert 11750 < length["km"] < 11900

    def _start_new_route(self):
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

    def test_bootstrap_route_length(self):
        """
        Test that the bootstrap route is within the given interval.
        """
        bootstrap_len = self._get_route_id_length(0)
        self.assertTrue(800 < bootstrap_len["km"] < 850)

    def _get_route_id_length(self, route_id):
        route_len = requests.get(ROUTE_LENGTH_ENDPOINT.format(route_id))
        route_len = route_len.json()
        return route_len

    def test_get_unkown_route_id_length(self):
        """
        Nothing was specified in the user description for the service for requests
        for lengths of unknown route_ids.
        """
        unknown_route_id = 999999
        error_response = self._get_route_id_length(unknown_route_id)
        expectation = "route_id {} has not added any waypoints".format(unknown_route_id)
        self.assertEqual(error_response["Error"], expectation)

    def test_add_waypoint_to_stale_route(self):
        response = requests.post(
            ROUTE_ADD_WAY_POINT_ENDPOINT.format(0),
            json={"lat": 52.520008, "lon": 13.404954},  # Berlin
        )
        self.assertTrue(response.status_code in [403, 404])

    def test_calculate_longest_route_for_today(self):
        """Test that the longest route for query date of today returns an Error
        per the service definitions:
            "The request will only query days in the past"
        """
        query_date = datetime.datetime.today().strftime("%Y-%m-%d")
        response = requests.get(ROUTE_LONGEST_ROUTE_IN_DAY_ENDPOINT.format(query_date))
        self.assertEqual(response.status_code, 403)
        query_result = response.json()
        self.assertTrue(query_result["Error"] == "The request will only query days in the past.")

    def test_calculate_longest_route_for_past_day(self):
        """Test that the service returns a result for querys for a previous
        days longest route. The request is formatted with variable query_date (str)
        in the format of %Y-%m-%d. As the service may not have waypoints for
        a particular date, acceptable error messages are caught and checked as well.
        """
        query_date = "1984-01-28"
        response = requests.get(ROUTE_LONGEST_ROUTE_IN_DAY_ENDPOINT.format(query_date))
        query_result = response.json()
        expected_error_messages = [
            "The request will only query days in the past.",
            "No routes recorded for {}".format(query_date),
        ]
        if query_result.get("Error"):
            self.assertTrue(response.status_code in [403, 404])
            self.assertTrue(query_result["Error"] in expected_error_messages)
        else:
            self.assertEqual(type(query_result["km"]), float)

    def test_add_many_waypoints(self):
        route_id = self._start_new_route()

        for i in range(random.randint(1, 10)):
            coordinates = self._random_lon_lat()
            response = requests.post(
                ROUTE_ADD_WAY_POINT_ENDPOINT.format(route_id), json=coordinates
            )
            time.sleep(0.1)

        if not response.status_code in [404, 403]:
            route_len = self._get_route_id_length(route_id)
            self.assertTrue(type(route_len["km"]) == float)
        else:
            self.assertTrue("Error" in response.json().keys())

    def _random_lon_lat(self):
        """Helper function for test_random_route

        Returns:
            coordinates (dict):
                key: 'lat' (str); value: (float) - a random latitude
                key: 'lon' (str); value: (float) - a random longitude
        """
        lon, lat = random.uniform(-180, 180), random.uniform(-90, 90)
        return {"lat": lat, "lon": lon}

if __name__=='__main__':
    unittest.main()#warnings='ignore'
