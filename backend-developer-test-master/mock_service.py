from flask import Flask, request
import json


app = Flask(__name__)


@app.route('/route/', methods=['POST'])
def create_route():
    return json.dumps({"route_id": "e84fee1e-fd4f-40f6-85b5-52ff46cbbb6e"}), 201


@app.route('/route/e84fee1e-fd4f-40f6-85b5-52ff46cbbb6e/way_point/', methods=["POST"])
def add_way_point():
    coordinates = request.get_json()  # {“lat”: 59.23425, “lon”: 18.23526}
    assert 'lat' in coordinates
    assert 'lon' in coordinates
    return "", 201

@app.route('/route/e84fee1e-fd4f-40f6-85b5-52ff46cbbb6e/length/')
def calculate_length():
    return json.dumps({"km": 334.83 + 10927.08 + 555.59})
