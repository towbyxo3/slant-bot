def get_top_user_msgs_day(cursor):
    """
    Returns the top user peaks, where members sent the most messages in a day.
    For example member xyz sent 1200 messages in a day on 25. Dec 2022
    """
    cursor.execute("""
        SELECT Date, Id, Msgs
        FROM userchat
        ORDER BY Msgs DESC
        LIMIT 10
        """)
    rows = cursor.fetchall()
    return rows


def get_user_day_peak_rank(cursor, id):
    """
    Returns a users own best personal peak and it's rank on the leaderboard.
    """
    cursor.execute("""
        SELECT *
        FROM(SELECT RANK() OVER (ORDER BY Msgs DESC) AS rank, Date, Id, Msgs
             FROM userchat
             ORDER BY Msgs DESC)
        WHERE Id = ?
        LIMIT 1
        """, (id,))
    rows = cursor.fetchall()
    return rows[0]


def get_top_user_msgs_week(cursor):
    # returns chat peaks by users in a week
    cursor.execute("""
        SELECT strftime('%Y-%W', "Date") AS week, Id, sum(Msgs) AS Msgs
        FROM userchat
        GROUP BY week, Id
        ORDER BY Msgs Desc
        LIMIT 10
        """)
    rows = cursor.fetchall()
    return rows


def get_user_week_peak_rank(cursor, id):
    # returns users own personal peak and ranking in week peak leaderboard
    cursor.execute("""
        SELECT *
        FROM(
            SELECT
                   row_number() OVER (ORDER BY Msgs DESC) AS rank, *
            FROM (
                SELECT strftime('%Y-%W', "Date") AS week, Id, sum(Msgs) AS Msgs
                FROM userchat
                GROUP BY week, Id
                ORDER BY Msgs DESC
                )
            )
        WHERE ID = ?
        LIMIT 1
        """, (id,))
    rows = cursor.fetchall()
    return rows[0]


def get_top_user_msgs_month(cursor):
    # returns chat peaks by users in a month
    cursor.execute("""
        SELECT strftime('%Y-%m', "Date") AS month, Id, sum(Msgs) AS Msgs
        FROM userchat
        GROUP BY month, Id
        ORDER BY Msgs Desc
        LIMIT 10
        """)
    rows = cursor.fetchall()
    return rows



def get_user_month_peak_rank(cursor, id):
    # returns users own personal peak and ranking in month peak leaderboard
    cursor.execute("""
        SELECT *
        FROM(
            SELECT
                   row_number() OVER (ORDER BY Msgs DESC) AS rank, *
            FROM (
                SELECT
                    strftime('%Y-%m', "Date") AS month,
                    Id,
                    sum(Msgs) AS Msgs
                FROM userchat
                GROUP BY month, Id
                ORDER BY Msgs DESC
                )
            )
        WHERE ID = ?
        LIMIT 1
        """, (id,))
    rows = cursor.fetchall()
    return rows[0]


def get_top_user_msgs_year(cursor):
    # returns chat peaks by users in a year
    cursor.execute("""
        SELECT strftime('%Y', "Date") AS year, Id, sum(Msgs) AS Msgs
        FROM userchat
        GROUP BY year, Id
        ORDER BY Msgs Desc
        LIMIT 10
        """)
    rows = cursor.fetchall()
    return rows


def get_user_year_peak_rank(cursor, id):
    # returns users own personal peak and ranking in year peak leaderboard
    cursor.execute("""
        SELECT *
        FROM(
            SELECT
                   row_number() OVER (ORDER BY Msgs DESC) AS rank, *
            FROM (
                SELECT strftime('%Y', "Date") AS year, Id, sum(Msgs) AS Msgs
                FROM userchat
                GROUP BY year, Id
                ORDER BY Msgs DESC
                )
            )
        WHERE ID = ?
        LIMIT 1
        """, (id,))
    rows = cursor.fetchall()
    return rows[0]
