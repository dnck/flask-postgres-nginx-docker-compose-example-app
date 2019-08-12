import requests
import datetime

SERVICE_ENDPOINT = "http://localhost:5000/"
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

    def test_calculate_longest_route_for_today(self):
        query_date = datetime.datetime.today().strftime("%Y-%m-%d")
        response = requests.get(
            ROUTE_LONGEST_ROUTE_IN_DAY_ENDPOINT.format(query_date)
        )
        query_result = response.json()
        assert query_result["Error"] == "The request will only query days in the past."

    # TODO add to database at start for yesterdays route.
    def test_calculate_longest_route_for_yesterday(self):
        query_date = datetime.datetime.strftime(datetime.datetime.now() - datetime.timedelta(1), '%Y-%m-%d')
        response = requests.get(
            ROUTE_LONGEST_ROUTE_IN_DAY_ENDPOINT.format(query_date)
        )
        query_result = response.json()
        acceptable_error_messages = ["The request will only query days in the past.", "No routes recorded for {}".format(query_date)]
        if query_result.get("Error"):
            assert query_result["Error"] in acceptable_error_messages
        else:
            assert "km" in query_result.keys()


def do_all_tests():
    test_route = TestRoute()
    test_route.setup()
    test_route.test_length_calculation()
    #test_route.test_calculate_longest_route_for_today()
    #test_route.test_calculate_longest_route_for_yesterday()

do_all_tests()
