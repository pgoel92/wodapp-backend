from flask import Flask, request, render_template, json
from flask_cors import CORS
from datetime import datetime as dt
import threading
import threading
import logging
import os
from pgdb import connect

app = Flask(__name__)
CORS(app)
app.config['DEBUG'] = True
today = dt.now().strftime('%Y_%m_%d')
file_handler = logging.FileHandler('wod_' + today + '.log')
file_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)
app.logger.addHandler(file_handler)

con = connect(database='wodapp', user='wodserver')

def execute_query(q, params):
    with con.cursor() as cur:
        cur.execute(q, params)
        return cur.fetchall()

score_data = [{'cid' : 1, 'cname': 'Prateek','wid' : 1,
    'score' : '12:09',
    'notes' : '10lb DB'}, {'cid' : 2, 'cname' : 'Ritu', 'wid' : 1,
    'score' : '11:12',
    'notes' : '15lb DB'}]

@app.before_first_request
def activate_job():
    #app.logger.info("Loading data for %s" % today)
    #load_data()
    pass

def write_customer_score(data):
    app.logger.info(data)
    score_data.append(data)

@app.route('/customers/<cid>', methods=['POST'])
def update(cid):
    data = request.json
    app.logger.info("Putting data for %s" % cid)
    write_customer_score(data)
    response = app.response_class(
        response=json.dumps({}),
        status=201,
        mimetype='application/json'
    )
    return response 

@app.route('/wod')
def wod():
    date = '2021-02-09'
    result = execute_query("select workout_info from program natural join workouts where workout_date = %s", (date,))
    workout_info = result[0].workout_info 
    response = app.response_class(
        response=json.dumps(workout_info),
        status=200,
        mimetype='application/json'
    )
    return response

@app.route('/scores')
def scores():
    response = app.response_class(
        response=json.dumps(score_data),
        status=200,
        mimetype='application/json'
    )
    return response

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
