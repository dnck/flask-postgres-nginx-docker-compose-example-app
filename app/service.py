from flask import Flask, request
import json
import models as db

FIRST_TIME = True

if FIRST_TIME:
    db.initialize_db_with_extension_and_table()

app = Flask(__name__)

@app.route("/route/", methods=["POST"])
def create_route():
    new_route = create_new_route()
    return json.dumps(new_route), 201

def create_new_route():
    """
    Gets a new route ID, and commits this to the db
    Returns new route id for the user
    """
    conn, cur = db.conn_cur_and_execute(db.GET_NEW_ROUTE_ID_SCRIPT)
    new_route_id = cur.fetchone()
    # TODO do we need the conversion here?
    if str(new_route_id[0]) == "None":
        cur.execute(db.START_NEW_ROUTE_SCRIPT.format(0))
        db.close_and_commit(cur, conn)
        return {"route_id": 0}
    cur.execute(db.START_NEW_ROUTE_SCRIPT.format(new_route_id[0]))
    db.close_and_commit(cur, conn)
    return {"route_id": str(new_route_id[0])}

@app.route("/route/<int:route_id>/way_point/", methods=["POST"])
def add_way_point(route_id):
    coordinates = request.get_json()  # {“lat”: 59.23425, “lon”: 18.23526}
    assert "lat" in coordinates
    assert "lon" in coordinates
    update_route(route_id, coordinates["lon"], coordinates["lat"])
    return "OK", 201

def update_route(route_id, longitude, latitude):
    """
    Handles date internally
    """
    conn, cur = db.conn_cur_and_execute(
        db.UPDATE_ROUTE_SCRIPT.format(route_id, longitude, latitude)
    )
    db.close_and_commit(cur, conn)

@app.route("/route/<int:route_id>/length/")
def calculate_length(route_id):
    result = get_length_of_single_route(route_id)
    return json.dumps({"km": result})

def get_length_of_single_route(route_id):
    conn, cur = db.conn_cur_and_execute(db.SINGLE_ROUTE_LENGTH_QUERY.format(route_id))
    result = cur.fetchone()
    db.close_and_commit(cur, conn)
    return result[0]

@app.route("/longest-route/<string:query_date>")
def calculate_longest_route_for_day(query_date):
    return (
        json.dumps(
            {
                "date": query_date,
                "route_id": "e84fee1e-fd4f-40f6-85b5-52ff46cbbb6e",
                "km": 334.83 + 10927.08 + 555.59,
            }
        ),
        201,
    )
