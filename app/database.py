import logging
import os
from contextlib import contextmanager

import mysql.connector
from mysql.connector import Error
from mysql.connector.pooling import MySQLConnectionPool


logger = logging.getLogger(__name__)


DB_CONFIG = {
    "host": os.getenv("DB_HOST", "mysql-db"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME", "attendance_db"),
    "charset": "utf8mb4",
}


if not DB_CONFIG["password"]:
    raise RuntimeError("DB_PASSWORD environment variable is required")


connection_pool = MySQLConnectionPool(
    pool_name="attendance_pool",
    pool_size=int(os.getenv("DB_POOL_SIZE", "10")),
    pool_reset_session=True,
    **DB_CONFIG,
)


@contextmanager
def get_db_connection():
    """
    Get a connection from the MySQL connection pool.

    The connection is automatically returned to the pool
    after the operation is completed.
    """
    connection = None

    try:
        connection = connection_pool.get_connection()
        yield connection

    except Error:
        logger.exception("Database connection error")
        raise

    finally:
        if connection and connection.is_connected():
            connection.close()


def init_db():
    """
    Verify database connectivity and create required tables.

    Database creation itself should be handled by MySQL/Docker
    initialization rather than by the Flask application.
    """

    with get_db_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS students (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_students_name (name)
            ) ENGINE=InnoDB
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS attendance (
                id INT AUTO_INCREMENT PRIMARY KEY,
                student_id INT NOT NULL,
                date DATE NOT NULL,
                status ENUM('Present', 'Absent') NOT NULL DEFAULT 'Present',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                PRIMARY KEY (id),

                UNIQUE KEY unique_student_date (student_id, date),

                CONSTRAINT fk_attendance_student
                    FOREIGN KEY (student_id)
                    REFERENCES students(id)
                    ON DELETE CASCADE,

                INDEX idx_attendance_date (date),
                INDEX idx_attendance_status (status)

            ) ENGINE=InnoDB
            """
        )

        conn.commit()
        cursor.close()


def check_database_connection():
    """
    Check whether the application can communicate with MySQL.
    Used by the health-check endpoint.
    """

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            cursor.close()

            return result == (1,)

    except Exception:
        logger.exception("Database health check failed")
        return False