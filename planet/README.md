# Usage

With docker-compose:
```
docker-compose up
```
The service is available for development on localhost:5000.

To test the system functionality, open a new terminal and type,
```
python integration_test.py
```

The service accepts POST requests to create a new ```route_id```, and update existing waypoints for a route_id.

Additionally, the service allows the user to

* query the length of a route_id using the endpoint, ```/route/<int:route_id>/length/```.

* query for the route_id that maps to the longest route on a particular ```query_date``` using the endpoint, ```/longest-route/<string:query_date>```.
The query_date is expected to be in the format of year-month-date string, ```%Y-%m-%d```.

To clean up,

```
docker-compose down
```

And if you wish,

```
docker volumes prune
```

## ISSUES

1. **Persist useful data for servicing requests!**

  Currently, the service uses an in-memory cache of recently requested dates for the user's longest route query. If the node fails, however, it may lose relevant data for servicing new requests. Persist all lengths from longest day query in the database.

2. **CONSIDER CHANGING:**

  The service is currently using postgis Geometry types for coordinate storage. Depending on the degree of precision required by the user in terms of length calculations, the service could change to using Geography data types instead.