import sqlite3


def get_daily_server_msgs(cursor, date):
    # returns weekly messages in a particular year and week
    cursor.execute("""
        SELECT SUM(Msgs),
               SUM(Chars)
        FROM serverchat
        WHERE Date = ?
        """, (date,))
    rows = cursor.fetchall()
    return rows[0]


def get_weekly_server_msgs(cursor, year, week):
    # returns weekly messages in a particular year and week
    cursor.execute("""
        SELECT SUM(Msgs),
               SUM(Chars)
        FROM serverchat
        WHERE strftime('%Y', Date) = ? AND strftime('%W', Date) = ?
        """, (year, week))
    rows = cursor.fetchall()
    return rows[0]


def get_monthly_server_msgs(cursor, year, month):
    # returns monthly messages in a particular year
    cursor.execute("""
        SELECT SUM(Msgs),
               SUM(Chars)
        FROM serverchat
        WHERE strftime('%Y', Date) = ? AND strftime('%m', Date) = ?
        """, (year, month))
    rows = cursor.fetchall()
    return rows[0]


def get_yearly_server_msgs(cursor, year):
    # returns yearly messages in a particular year
    cursor.execute("""
        SELECT SUM(Msgs),
               SUM(Chars)
        FROM serverchat
        WHERE strftime('%Y', Date) = ?
        """, (year,))
    rows = cursor.fetchall()
    return rows[0]


def get_alltime_server_msgs(cursor):
    # returns alltime messages
    cursor.execute("""
        SELECT SUM(Msgs),
               SUM(Chars)
        FROM serverchat
        """)
    rows = cursor.fetchall()
    return rows[0]


def get_day_chat_entries_count(cursor):
    cursor.execute("""
        SELECT COUNT(Date)
        FROM serverchat
        """)
    rows = cursor.fetchall()
    return rows[0][0]


def get_week_chat_entries_count(cursor):
    cursor.execute("""
        SELECT COUNT(*) AS row_count
        FROM (
          SELECT strftime('%Y-%W', Date) AS week
          FROM serverchat
          GROUP BY week
        ) AS weeks;
        """)
    rows = cursor.fetchall()
    return rows[0][0]


def get_month_chat_entries_count(cursor):
    cursor.execute("""
        SELECT COUNT(*) AS row_count
        FROM (
          SELECT strftime('%Y-%m', Date) AS month
          FROM serverchat
          GROUP BY month
        ) AS weeks;
        """)
    rows = cursor.fetchall()
    return rows[0][0]


def get_year_chat_entries_count(cursor):
    cursor.execute("""
        SELECT COUNT(*) AS row_count
        FROM (
          SELECT strftime('%Y', Date) AS year
          FROM serverchat
          GROUP BY year
        ) AS weeks
        """)
    rows = cursor.fetchall()
    return rows[0][0]


def get_chat_active_days_count_in_year(cursor, year):
    cursor.execute("""
        SELECT COUNT(date)
        FROM serverchat
        WHERE strftime('%Y', Date) = ?
        """, (year,))
    rows = cursor.fetchall()
    return rows[0][0]


def get_server_month_peak_in_year(cursor, year):
    # returns the monthly messages peak in a year by a user
    cursor.execute("""
        SELECT strftime('%Y-%m', Date) as Month, SUM(Msgs) as total_msgs
        FROM serverchat
        WHERE STRFTIME('%Y', Date) = ?
        GROUP BY Month
        ORDER BY total_msgs DESC
        LIMIT 1
        """, (year,))
    data = cursor.fetchall()
    return data[0]


def get_server_day_peak_in_year(cursor, year):
    # returns the peak of a year by a user
    cursor.execute("""
        SELECT Date, Msgs
        FROM serverchat
        WHERE STRFTIME('%Y', Date) = ?
        ORDER BY Msgs DESC
        """, (year,))
    data = cursor.fetchall()
    return data[0]


def get_server_year_peak_rank(cursor, year):
    cursor.execute("""
        SELECT rank
        FROM (SELECT
                RANK() OVER(ORDER BY SUM(Msgs) DESC) as rank,
                STRFTIME('%Y', Date) AS year,
                SUM(Msgs) as year_msgs
              FROM serverchat
              GROUP BY year)
        WHERE year = ?
        """, (year,))
    data = cursor.fetchall()
    return data[0][0]
