from flask import Flask, jsonify
import json, os

app = Flask(__name__)
JSON_FILE = os.path.join(os.path.dirname(__file__), "tasa_actual.json")

@app.route("/api/tasa")
def tasa():
    if not os.path.exists(JSON_FILE):
        return {"error": "JSON no generado aún"}, 503
    with open(JSON_FILE, encoding="utf-8") as f:
        return jsonify(json.load(f))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
