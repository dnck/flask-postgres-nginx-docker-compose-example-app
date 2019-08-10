from test import integration_test

if __name__ == "__main__":
    test_route = integration_test.TestRoute()
    test_route.setup()
    test_route.test_length_calculation()
    test_route.test_calculate_longest_route_for_day()
    test_route.test_get_points_in_path()
