import requests
import datetime

SECRET_KEY = "hello-planet-labs"
SERVICE_ENDPOINT = "http://localhost:5000/"
BOOTSTRAP_ENDPOINT = "{}initialize_db/".format(SERVICE_ENDPOINT)
ROUTE_ENDPOINT = "{}route/".format(SERVICE_ENDPOINT)
ROUTE_ADD_WAY_POINT_ENDPOINT = "{}{}/way_point/".format(ROUTE_ENDPOINT, "{}")
ROUTE_LENGTH_ENDPOINT = "{}{}/length/".format(ROUTE_ENDPOINT, "{}")
ROUTE_LONGEST_ROUTE_IN_DAY_ENDPOINT = "{}longest-route/{}".format(
    SERVICE_ENDPOINT, "{}"
)

class TestRoute(object):
    wgs84_coordinates = [
        {"lat": -25.4025905, "lon": -49.3124416},
        {"lat": -23.559798, "lon": -46.634971},
        {"lat": 59.3258414, "lon": 17.70188},
        {"lat": 54.273901, "lon": 18.591889}
    ]

    def setup(self):
        self.bootstrap_msg = requests.post(
            BOOTSTRAP_ENDPOINT, json={"key": SECRET_KEY}
        )
        self.route_post = requests.post(ROUTE_ENDPOINT)
        route = self.route_post.json()
        route_id = route["route_id"]
        self._push_route(route_id)
        self.length_get = requests.get(ROUTE_LENGTH_ENDPOINT.format(route_id))

    def _push_route(self, route_id):
        for coordinates in self.wgs84_coordinates:
            requests.post(
                ROUTE_ADD_WAY_POINT_ENDPOINT.format(route_id), json=coordinates
            )

    def test_length_calculation(self):
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
        """
        Should fail
        """
        query_date = datetime.datetime.today().strftime("%Y-%m-%d")
        response = requests.get(
            ROUTE_LONGEST_ROUTE_IN_DAY_ENDPOINT.format(query_date)
        )
        assert response.status_code == 403
        query_result = response.json()
        assert query_result["Error"] == "The request will only query days in the past."

    def test_calculate_longest_route_for_past_day(self):
        query_date = "1984-01-28" # %Y-%m-%d
        response = requests.get(
            ROUTE_LONGEST_ROUTE_IN_DAY_ENDPOINT.format(query_date)
        )
        query_result = response.json()
        acceptable_error_messages = \
            ["The request will only query days in the past.",
            "No routes recorded for {}".format(query_date)]
        if query_result.get("Error"):
            assert response.status_code in [403, 404]
            assert query_result["Error"] in acceptable_error_messages
        else:
            assert "km" in query_result.keys()

def do_all_tests():
    test_route = TestRoute()
    test_route.setup()
    test_route.test_length_calculation()
    test_route.test_bootstrap_route_length()
    test_route.test_calculate_longest_route_for_today()
    test_route.test_calculate_longest_route_for_past_day()

do_all_tests()
