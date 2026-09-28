from app.database import get_connection


with get_connection() as connection:
    with connection.cursor() as cursor:
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]

        print("PostgreSQL connection successful!")
        print(version)