def get_top_server_msgs_day(cursor):
    cursor.execute("""
        SELECT Date, Msgs
        FROM serverchat
        ORDER BY Msgs DESC
        LIMIT 10
        """)
    rows = cursor.fetchall()
    return rows


def get_top_server_msgs_week(cursor):
    cursor.execute("""
        SELECT strftime('%Y-%W', "Date") as week, SUM("Msgs") as total_msgs
        FROM serverchat
        GROUP BY week
        ORDER BY total_msgs DESC
        LIMIT 10
        """)
    rows = cursor.fetchall()
    return rows


def get_top_server_msgs_month(cursor):
    cursor.execute("""
    SELECT strftime('%Y-%m', "Date") as month, SUM("Msgs") as total_msgs
    FROM serverchat
    GROUP BY month
    ORDER BY total_msgs DESC
    LIMIT 10
        """)
    rows = cursor.fetchall()
    return rows


def get_top_server_msgs_year(cursor):
    cursor.execute("""
        SELECT strftime('%Y', "Date") as year, SUM("Msgs") as total_msgs
        FROM serverchat
        GROUP BY year
        ORDER BY total_msgs DESC
        LIMIT 10
        """)
    rows = cursor.fetchall()
    return rows
