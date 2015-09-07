#!/usr/local/bin/python
from flask import Flask, jsonify, request
import json, requests, argparse, logging
from logging.handlers import RotatingFileHandler


baseurl = "http://localhost:5000/"
director_service =  baseurl + "find"

app = Flask(__name__)

@app.route('/log', methods=['POST'])
def log():
    if not request.json:
        app.logger.error('Parser error, data dump: %s, headers: %s', request.data, request.headers )
        return 'Parser error', 500
    mess = request.json['message']
    level = request.json['level']
    if level == 'debug':
        app.logger.debug(mess)
    elif level == 'info':
        app.logger.info(mess)
    elif level == 'error':
        app.level.error(mess)
    return jsonify({'status':'ok'}),200

def rlog(level,mess):
    resp = requests.post(baseurl + "log",
        json.dumps({ 'level': level, 'message': mess}),
        headers={'Content-type': 'application/json'}
        )
    return resp.status_code == 200

@app.route('/find', methods=['POST','GET'])
def find():
    operator = ''
    if request.method == 'POST':
        if not request.json:
            app.logger.error('Parser error, data dump: %s, headers: %s', request.data, request.headers )
            return 'Parser error', 500
        operator= request.json['operator']
    elif request.method == 'GET':
        operator = request.form.get('operator','+')

    ops = { '+' : 'plus',
            '-' : 'minus',
            'log' : 'log'
            }

    result = {'service' : ops[operator]}
    return jsonify(result), 200

@app.route('/plus', methods=['POST','GET'])
def plus():
    if not request.json:
        abort(400)
    a = float(request.json['a'])
    b = float(request.json['b'])
    result = { 'answer' : a + b }
    rlog('info', "{} + {} = {}".format(a,b,a+b))
    return jsonify(result), 200

@app.route('/minus', methods=['POST','GET'])
def minus():
    if not request.json:
        abort(400)
    a = float(request.json['a'])
    b = float(request.json['b'])
    result = { 'answer' : a - b }
    rlog('info', "{} - {} = {}".format(a,b,a-b))
    return jsonify(result), 200

@app.route('/calculate', methods=['POST','GET'])
def calculate():
    op = ''
    a = b = 0

    if request.method == 'POST':
        if not request.json:
            app.logger.error('Parser error, data dump: %s, headers: %s', request.data, request.headers )
            return 'Parser error', 500
        a = float(request.json['a'])
        b = float(request.json['b'])
        op = request.json['operator']
    elif request.method == 'GET':
        op = request.form.get('operator','+')
        a = float(request.form.get('a',0))
        b = float(request.form.get('b',0))
    app.logger.info('info', 'Just about to log it')
    app.logger.info('info', 'calc: %f %s %f', a,op, b)
    resp = requests.post(director_service, 
        json.dumps({ 'operator' : op}),
        headers={'Content-type': 'application/json'}
        )
    service = resp.json()['service']
    operator_url = baseurl + service
    
    rlog('info','Director said to use {}'.format(operator_url ))

    resp = requests.post(operator_url, 
        json.dumps({'a':a,'b':b, 'operator':op}),
        headers={'Content-type': 'application/json'}
        )

    return resp.text, 200

parser = argparse.ArgumentParser()
parser.add_argument("port", help="Port number to listen on", type=int)
args = parser.parse_args()

if __name__ == '__main__':
    handler = RotatingFileHandler('app.log', maxBytes=10000000, backupCount=5)
#    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.DEBUG)
    app.logger.setLevel(logging.DEBUG)
    log.addHandler(handler)
    app.run(debug=True,port=args.port, use_reloader=True, processes=5)
