Usage:

With docker-compose:
```
docker-compose up
```
The service is available for development on localhost:5000.

To test the system functionality,
```
python integration_test.py
```

To clean up,

```
docker-compose down
```

And if you wish,

```
docker volumes prune
```

**TODO**
models.py needs docstrings
service.py missing docstring at module level and log complaints on line 65, 106, 145
Refact integration_test.py
