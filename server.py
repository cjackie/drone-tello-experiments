from flask import Flask, render_template, Response, send_from_directory
from tinydb import TinyDB, Query
from telemetry_streamer import TelemetryStreamer
import json

app = Flask(__name__)

@app.route('/data/dump')
def data_dump():
  db = TinyDB('data/drone_db.json')
  telemetry = db.table("Telemetry")
  all_data = telemetry.all()
  return Response(json.dumps(all_data), "application/json")

@app.route("/data/streaming")
def data_streaming():  
  streamer = TelemetryStreamer()
  generator = (data_point for data_point in streamer.get())
  return Response(generator, mimetype="application/json")

@app.route('/plot/telemetry')
def plot_telemetry():
  return render_template('plot_telemetry.html')

@app.route('/js/<path:path>')
def send_js(path):
    return send_from_directory('js', path)

@app.route('/plot/streaming_telemetry')
def streaming_telemetry():
  return render_template('plot_streaming_telemetry.html')

@app.route('/')
def index():
  return render_template('index.html')

if __name__ == '__main__':
  app.run(host='localhost', threaded=True)
