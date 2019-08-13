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
    """This method does a test"""

    wgs84_coordinates = [
        {"lat": -25.4025905, "lon": -49.3124416},
        {"lat": -23.559798, "lon": -46.634971},
        {"lat": 59.3258414, "lon": 17.70188},
        {"lat": 54.273901, "lon": 18.591889},
    ]

    def setup(self):
        """This method does a test"""
        bootstrap_msg = requests.post(BOOTSTRAP_ENDPOINT, json={"key": SECRET_KEY})
        route_id = self.start_new_route()
        self._push_route(route_id)
        self.length_get = requests.get(ROUTE_LENGTH_ENDPOINT.format(route_id))

    def start_new_route(self):
        """Pass"""
        self.route_post = requests.post(ROUTE_ENDPOINT)
        route = self.route_post.json()
        return route["route_id"]

    def _push_route(self, route_id):
        """This method does a test"""
        for coordinates in self.wgs84_coordinates:
            requests.post(
                ROUTE_ADD_WAY_POINT_ENDPOINT.format(route_id), json=coordinates
            )

    def test_length_calculation(self):
        """This method does a test"""
        length = self.length_get.json()
        assert 11750 < length["km"] < 11900

    def test_bootstrap_route_length(self):
        """
        Passes with the first route we add for bootstrapping the db
        """
        bootstrap_len = requests.get(ROUTE_LENGTH_ENDPOINT.format(0))
        bootstrap_len = bootstrap_len.json()
        assert 800 < bootstrap_len["km"] < 850

    # TODO refactor into smaller test cases
    def test_calculate_longest_route_for_today(self):
        """This method does a test"""
        query_date = datetime.datetime.today().strftime("%Y-%m-%d")
        response = requests.get(ROUTE_LONGEST_ROUTE_IN_DAY_ENDPOINT.format(query_date))
        assert response.status_code == 403
        query_result = response.json()
        assert query_result["Error"] == "The request will only query days in the past."

    def test_calculate_longest_route_for_past_day(self):
        """Client %Y-%m-%d"""
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

    def test_random_route(self):
        func = random.choice([self.random_route_id, self.start_new_route])
        route_id = func()
        for x in range(random.randint(1, 100)):
            coordinates = self.random_lon_lat()
            response = requests.post(
                ROUTE_ADD_WAY_POINT_ENDPOINT.format(route_id), json=coordinates
            )
            time.sleep(0.25)

    def random_route_id(self):
        return random.randint(1, 10)

    def random_lon_lat(self):
        lon, lat = random.uniform(-180,180), random.uniform(-90, 90)
        return {"lat": lat, "lon": lon}

    def test_many_random_routes(self):
        for x in range(20):
            self.test_random_route()
            time.sleep(0.25)


def do_all_tests():
    """This method does a test"""
    test_route = TestRoute()
    test_route.setup()
    test_route.test_length_calculation()
    test_route.test_bootstrap_route_length()
    test_route.test_calculate_longest_route_for_today()
    test_route.test_calculate_longest_route_for_past_day()
    test_route.test_many_random_routes()

if __name__ == "__main__":
    do_all_tests()
