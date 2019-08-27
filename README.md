### Background  
This is a toy app that shows how to combine several services with docker-compose to create a Flask app to accept fake gps data from a device.

The hypothetical device can request a new route to be created. It can then continuously populate its route with data points, which are stored as WGS84 coordinates in a postgres db with postgis enabled.

Each route is expected to be done within a day. A day is defined by the server.

After the day end, the device can NOT add more data points. It must request a new ID for a new route if it wishes to continue adding coordinates.

Anyone can request the length of a route, and also the ID of the longest route
for a given day. However, while the length of a route can be made for any route ID, a request for the longest route in a day can only query days in the past.


# Usage

With docker-compose:
```
docker-compose up
```
The service is available for development on localhost:5000. It uses uWSGI as an http server for flask and nginx as the reverse proxy. You can visit the endpoints in your browser, or use the enclosed test to interact with the service.

The service accepts POST requests to create a new ```route_id```, and update existing coordinates for a route_id.

The service allows the user to

* query the length of a route_id using the endpoint, ```/route/<int:route_id>/length/```.

* query for the route_id that maps to the longest route on a particular ```query_date``` using the endpoint, ```/longest-route/<string:query_date>```.
The query_date is expected to be in the format of year-month-date string, ```%Y-%m-%d```.

To test the system functionality, use the test,
```
python test.py
```

To clean up after your done,

```
docker-compose down
```

And if you wish,

```
docker volumes prune
```
