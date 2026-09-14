import logging
from datetime import date, datetime

from flask import jsonify, render_template, request
from mysql.connector import Error

from app import app
from app.database import check_database_connection
from app.models import (
    add_student,
    get_attendance,
    get_attendance_stats,
    get_student_attendance,
    mark_attendance,
)


logger = logging.getLogger(__name__)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/health")
def health():
    """
    Health check endpoint for Docker/Nginx/load balancer.
    """

    if check_database_connection():
        return jsonify({
            "status": "healthy",
            "database": "connected"
        }), 200

    return jsonify({
        "status": "unhealthy",
        "database": "unavailable"
    }), 503


@app.route("/register_student", methods=["POST"])
def register_student():
    data = request.get_json(silent=True) or {}

    name = str(data.get("name", "")).strip()

    if not name:
        return jsonify({
            "success": False,
            "error": "Name is required"
        }), 400

    if len(name) > 100:
        return jsonify({
            "success": False,
            "error": "Name must not exceed 100 characters"
        }), 400

    try:
        student_id = add_student(name)

        mark_attendance(
            student_id,
            date.today(),
            "Present"
        )

        return jsonify({
            "success": True,
            "message": f"Attendance recorded for {name}",
            "student_id": student_id
        }), 201

    except Error:
        logger.exception("Database error while registering student")

        return jsonify({
            "success": False,
            "error": "Unable to register student"
        }), 500

    except Exception:
        logger.exception("Unexpected error while registering student")

        return jsonify({
            "success": False,
            "error": "Internal server error"
        }), 500


@app.route("/mark_absent", methods=["POST"])
def mark_absent():
    data = request.get_json(silent=True) or {}

    student_id = data.get("student_id")

    if not student_id:
        return jsonify({
            "success": False,
            "error": "Student ID is required"
        }), 400

    try:
        student_id = int(student_id)

    except (TypeError, ValueError):
        return jsonify({
            "success": False,
            "error": "Student ID must be a valid number"
        }), 400

    try:
        mark_attendance(
            student_id,
            date.today(),
            "Absent"
        )

        return jsonify({
            "success": True,
            "message": "Student marked as Absent"
        }), 200

    except Error:
        logger.exception("Database error while marking absent")

        return jsonify({
            "success": False,
            "error": "Unable to update attendance"
        }), 500


@app.route("/get_attendance", methods=["GET"])
def fetch_attendance():
    try:
        records = get_attendance()

        return render_template(
            "attendance.html",
            records=records
        )

    except Error:
        logger.exception("Failed to fetch attendance")

        return jsonify({
            "success": False,
            "error": "Unable to fetch attendance"
        }), 500


@app.route("/analytics")
def analytics_page():
    return render_template("analytics.html")


@app.route("/attendance_stats", methods=["GET"])
def attendance_stats():
    start_date = request.args.get(
        "start_date",
        "2023-01-01"
    )

    end_date = request.args.get(
        "end_date",
        datetime.today().strftime("%Y-%m-%d")
    )

    student_name = request.args.get(
        "student_name"
    )

    try:
        datetime.strptime(start_date, "%Y-%m-%d")
        datetime.strptime(end_date, "%Y-%m-%d")

    except ValueError:
        return jsonify({
            "success": False,
            "error": "Dates must use YYYY-MM-DD format"
        }), 400

    if start_date > end_date:
        return jsonify({
            "success": False,
            "error": "start_date cannot be after end_date"
        }), 400

    try:
        if student_name:
            stats = get_student_attendance(
                student_name.strip(),
                start_date,
                end_date
            )
        else:
            stats = get_attendance_stats(
                start_date,
                end_date
            )

        return jsonify({
            "success": True,
            "data": stats
        }), 200

    except Error:
        logger.exception("Failed to fetch attendance statistics")

        return jsonify({
            "success": False,
            "error": "Unable to fetch attendance statistics"
        }), 500