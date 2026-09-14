import logging

from mysql.connector import Error

from app.database import get_db_connection


logger = logging.getLogger(__name__)


def add_student(name):
    """Insert a new student and return the generated ID."""

    name = name.strip()

    if not name:
        raise ValueError("Student name cannot be empty")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        try:
            cursor.execute(
                "INSERT INTO students (name) VALUES (%s)",
                (name,)
            )

            student_id = cursor.lastrowid
            conn.commit()

            return student_id

        except Error:
            conn.rollback()
            logger.exception("Failed to add student")
            raise

        finally:
            cursor.close()


def mark_attendance(student_id, attendance_date, status="Present"):
    """Create or update attendance for a student on a specific date."""

    if status not in ("Present", "Absent"):
        raise ValueError("Invalid attendance status")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                INSERT INTO attendance
                    (student_id, date, status)
                VALUES
                    (%s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    status = VALUES(status)
                """,
                (student_id, attendance_date, status)
            )

            conn.commit()

        except Error:
            conn.rollback()
            logger.exception("Failed to mark attendance")
            raise

        finally:
            cursor.close()


def get_attendance():
    """Fetch attendance records."""

    with get_db_connection() as conn:
        cursor = conn.cursor(dictionary=True)

        try:
            cursor.execute(
                """
                SELECT
                    s.id AS student_id,
                    s.name,
                    a.date,
                    a.status
                FROM attendance a
                INNER JOIN students s
                    ON a.student_id = s.id
                ORDER BY a.date DESC, s.name ASC
                """
            )

            return cursor.fetchall()

        finally:
            cursor.close()


def get_attendance_stats(start_date, end_date):
    """Fetch Present vs Absent count for a date range."""

    with get_db_connection() as conn:
        cursor = conn.cursor(dictionary=True)

        try:
            cursor.execute(
                """
                SELECT
                    status,
                    COUNT(*) AS count
                FROM attendance
                WHERE date BETWEEN %s AND %s
                GROUP BY status
                """,
                (start_date, end_date)
            )

            data = {
                row["status"]: row["count"]
                for row in cursor.fetchall()
            }

            return {
                "Present": data.get("Present", 0),
                "Absent": data.get("Absent", 0),
            }

        finally:
            cursor.close()


def get_student_attendance(name, start_date, end_date):
    """Fetch attendance statistics for a specific student."""

    with get_db_connection() as conn:
        cursor = conn.cursor(dictionary=True)

        try:
            cursor.execute(
                """
                SELECT
                    a.status,
                    COUNT(*) AS count
                FROM attendance a
                INNER JOIN students s
                    ON a.student_id = s.id
                WHERE
                    s.name = %s
                    AND a.date BETWEEN %s AND %s
                GROUP BY a.status
                """,
                (name, start_date, end_date)
            )

            data = {
                row["status"]: row["count"]
                for row in cursor.fetchall()
            }

            return {
                "Student": name,
                "Present": data.get("Present", 0),
                "Absent": data.get("Absent", 0),
            }

        finally:
            cursor.close()