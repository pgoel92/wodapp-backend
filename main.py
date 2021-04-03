from flask import Flask, request, render_template, json
from flask_cors import CORS
from datetime import datetime as dt
import threading
import threading
import logging
import json
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


def execute_read_query(q, params=()):
    try:
        con = connect(database='wodapp', user='wodserver')
        with con.cursor() as cur:
            cur.execute(q, params)
            result = cur.fetchall()
            con.close()
            return result
    except Exception as e:
        app.logger.error(e) 
        return False

def execute_write_query(q, params=()):
    try:
        con = connect(database='wodapp', user='wodserver')
        with con.cursor() as cur:
            result = cur.execute(q, params)
            con.commit()
        return True
    except Exception as e:
        app.logger.error(e) 
        return False

@app.before_first_request
def activate_job():
    pass

def write_customer_score(data):
    app.logger.info(data)
    program_id = data['program_id']
    athlete_id = data['athlete_id']
    score = data['score']
    notes = data['notes'] or ''
    scaled_wod = data['scaled_wod']
    is_rx = (scaled_wod == None)
    print("insert into scores(program_id, athlete_id, score, notes, is_rx, scaled_wod) values(%d, %d, '%s', '%s', %s, '%s')" % (program_id, athlete_id, json.dumps(score), notes, is_rx, json.dumps(scaled_wod)))
    is_successful = execute_write_query("insert into scores(program_id, athlete_id, score, notes, is_rx, scaled_wod) values(%d, %d, %s, %s, %s, %s)", (program_id, athlete_id, json.dumps(score), notes, is_rx, json.dumps(scaled_wod)))
    return is_successful

@app.route('/customers/<cid>', methods=['POST'])
def update(cid):
    data = request.json
    app.logger.info("Putting data for %s" % cid)
    is_successful = write_customer_score(data)
    status = 201 if is_successful else 500
    response = app.response_class(
        response=json.dumps({}),
        status=status,
        mimetype='application/json'
    )
    return response 

@app.route('/customers/scores')
def customer_scores():
    workout_id = request.args.get('workout_id')
    date = request.args.get('date')
    result = execute_read_query("select b.id, first_name, last_name, is_rx, a.score, scaled_wod->'type', workout_date from scores a join athletes b on a.athlete_id = b.id join program c on a.program_id = c.id where c.workout_id = %s and c.workout_date < %s", (workout_id, date))
    print(result)
    result = [{'cid' : item[0], 'first_name' : item[1], 'last_name' : item[2], 'is_rx' : item[3], 'score' : item[4], 'type' : item[5], 'date' : item[6].strftime('%B %d, %Y')} for item in result]
    
    response = app.response_class(
        response=json.dumps(result),
        status=200,
        mimetype='application/json'
    )
    return response

@app.route('/athletes')
def athletes():
    result = execute_read_query("select id, first_name, last_name from athletes")
    if result:
        athletes = [{"athlete_id" : athlete.id, "first_name" : athlete.first_name, "last_name" : athlete.last_name} for athlete in result]
    else:
        athletes = []
    response = app.response_class(
        response=json.dumps(athletes),
        status=200,
        mimetype='application/json'
    )
    return response 

@app.route('/wod')
def wod():
    try:
        date = request.args.get('date')
    except Exception:
        date = dt.strftime(dt.now(), "%Y-%m-%d")

    result = execute_read_query("select program.id, workout_id, workout_info from program join workouts on program.workout_id = workouts.id where workout_date = %s", (date,))
    if result:
        workout_info = result[0].workout_info
        workout_info['id'] = result[0].workout_id
        json_response = {'workout' : workout_info, 'id' : result[0].id} 
    else:
        json_response = {}

    response = app.response_class(
        response=json.dumps(json_response),
        status=200,
        mimetype='application/json'
    )
    return response

@app.route('/scores')
def scores():
    try:
        date = request.args.get('date')
    except Exception:
        date = dt.strftime(dt.now(), "%Y-%m-%d")
    result = execute_read_query("select b.id, first_name, last_name, is_rx, a.score, scaled_wod->'type' from scores a join athletes b on a.athlete_id = b.id join program c on a.program_id = c.id where c.workout_date = %s", (date,))
    result = [{'cid' : item[0], 'first_name' : item[1], 'last_name' : item[2], 'is_rx' : item[3], 'score' : item[4], 'type' : item[5]} for item in result]
    
    response = app.response_class(
        response=json.dumps(result),
        status=200,
        mimetype='application/json'
    )
    return response

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
