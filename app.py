#!/usr/bin/env python3
"""
Progresif Vedik Astroloji — Flask Web Uygulaması
"""

from flask import Flask, render_template, request, jsonify
from vedic_chart import calculate_chart

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/calculate", methods=["POST"])
def api_calculate():
    try:
        data = request.get_json()

        year = int(data["year"])
        month = int(data["month"])
        day = int(data["day"])
        hour = int(data["hour"])
        minute = int(data["minute"])
        tz_offset = float(data["tz_offset"])
        lat = float(data["lat"])
        lon = float(data["lon"])

        if not (1 <= month <= 12):
            return jsonify({"error": "Geçersiz ay değeri"}), 400
        if not (1 <= day <= 31):
            return jsonify({"error": "Geçersiz gün değeri"}), 400
        if not (0 <= hour <= 23):
            return jsonify({"error": "Geçersiz saat değeri"}), 400
        if not (0 <= minute <= 59):
            return jsonify({"error": "Geçersiz dakika değeri"}), 400
        if not (-90 <= lat <= 90):
            return jsonify({"error": "Geçersiz enlem değeri"}), 400
        if not (-180 <= lon <= 180):
            return jsonify({"error": "Geçersiz boylam değeri"}), 400

        result = calculate_chart(year, month, day, hour, minute, tz_offset, lat, lon)
        return jsonify(result)

    except (KeyError, TypeError, ValueError) as e:
        return jsonify({"error": f"Geçersiz veri: {str(e)}"}), 400
    except Exception as e:
        return jsonify({"error": f"Hesaplama hatası: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
