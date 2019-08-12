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

## TODO
1. The service is vulnerable to attacks. An attack can add new way points to today's on-going routes simply by passing an integer route_id to the endpoint for updating waypoints. Although convenient during development, int data types should not be used for the route_ids.

2. Currently, the service uses an in-memory cache of recently requested dates for the longest route query. These are not persisted, but they should be, because in the event of failure, the node could resume serving queries quickly.

3. The service is currently using postgis Geometry types for coordinate storage. Depending on the degree of precision required by the user in terms of length calculations, the service could change to using Geography types instead.

4. 
