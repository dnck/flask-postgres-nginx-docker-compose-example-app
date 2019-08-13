# Usage

With docker-compose:
```
docker-compose up
```
The service is available for development on localhost:5000. It uses uWSGI as an http server for flask and nginx as the user proxy.

The service accepts POST requests to create a new ```route_id```, and update existing waypoints for a route_id.

Additionally, the service allows the user to

* query the length of a route_id using the endpoint, ```/route/<int:route_id>/length/```.

* query for the route id that maps to the longest route on a particular ```query_date``` using the endpoint, ```/longest-route/<string:query_date>```.
The query_date is expected to be in the format of year-month-date string, ```%Y-%m-%d```.

To test the system functionality, use the integration_test,
```
python integration_test.py
```

To clean up after your done,

```
docker-compose down
```

And if you wish,

```
docker volumes prune
```

## TODO

1. **Persist useful data for servicing requests.**

  Currently, the service uses an in-memory cache of recently requested dates for the user's longest route query. If the node fails, however, it will lose this information. One idea is to persist all lengths from longest day querys in the database. The query.UPDATE_ALL_ROUTES_IN_DAY_LENGTH already
  has this query written out for postgres, it just needs to be decided where it should come into play.

2. **Consider changing to Geography dtypes in postgres:**

  The service is currently using postgis Geometry types for coordinate storage. Depending on the degree of precision required by the user in terms of length calculations, the service could change to using Geography data types instead.
