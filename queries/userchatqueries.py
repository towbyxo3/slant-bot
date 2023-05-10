def top_chatters_week(cursor, year, week):
    # returns top weekly chatters of a particular week in a year
    cursor.execute("""
        SELECT Id, SUM(Msgs) AS Msgs
        FROM userchat
        WHERE strftime('%W', Date) = ? AND strftime('%Y', Date) = ?
        GROUP BY Id
        ORDER BY Msgs DESC
        Limit 10
        """, (week, year))
    rows = cursor.fetchall()
    return rows


def get_user_rank_top_chatters_week(cursor, year, week, id):
    # returns user rank in the weekly chat leaderboard
    cursor.execute("""
        SELECT *
        FROM (SELECT
                RANK() OVER (ORDER BY Sum(Msgs) DESC) AS rank,
                Id,
                SUM(Msgs) AS Msgs
              FROM userchat
              WHERE strftime('%W', Date) = ? AND strftime('%Y', Date) = ?
              GROUP BY Id
              ORDER BY SUM(Msgs) DESC)
        WHERE Id = ?
        """, (week, year, id))
    rows = cursor.fetchall()
    if len(rows) == 0:
        return "-", id, 0
    return rows[0]


def get_distinct_chatters_count_day(cursor, date):
    # returns how many unique chatters in week
    cursor.execute("""
        SELECT COUNT(DISTINCT Id)
        FROM userchat
        WHERE strftime('%Y-%m-%d', Date) = ?;
        """, (date,))
    rows = cursor.fetchall()
    return rows[0][0]


def get_distinct_chatters_count_week(cursor, year, week):
    # returns how many unique chatters in week
    cursor.execute("""
        SELECT COUNT(DISTINCT Id)
        FROM userchat
        WHERE strftime('%Y', Date) = ? AND strftime('%W', Date) = ?;
        """, (year, week))
    rows = cursor.fetchall()
    return rows[0][0]



def top_chatters_month(cursor, year, month):
    # returns top monthly chatters of a particular month in a year
    cursor.execute("""
        SELECT Id, SUM(Msgs) AS Msgs
        FROM userchat
        WHERE strftime('%m', Date) = ? AND strftime('%Y', Date) = ?
        GROUP BY Id
        ORDER BY Msgs DESC
        Limit 10
        """, (month, year))
    rows = cursor.fetchall()
    return rows


def get_user_rank_top_chatters_month(cursor, year, month, id):
    # returns user rank in the monthly chat leaderboard
    cursor.execute("""
        SELECT *
        FROM (SELECT
                RANK() OVER (ORDER BY Sum(Msgs) DESC) AS rank,
                Id,
                SUM(Msgs) AS Msgs
              FROM userchat
              WHERE strftime('%m', Date) = ? AND strftime('%Y', Date) = ?
              GROUP BY Id
              ORDER BY SUM(Msgs) DESC)
        WHERE Id = ?
        """, (month, year, id))
    rows = cursor.fetchall()
    if len(rows) == 0:
        return "-", id, 0
    return rows[0]



def get_distinct_chatters_count_month(cursor, year, month):
    # returns how many unique chatters all month
    cursor.execute("""
        SELECT COUNT(DISTINCT Id)
        FROM userchat
        WHERE strftime('%Y', Date) = ? AND strftime('%m', Date) = ?
        """, (year, month))
    rows = cursor.fetchall()
    return rows[0][0]


def top_chatters_year(cursor, year):
    # returns top yearly chatters of a particular year
    cursor.execute("""
        SELECT Id, SUM(Msgs) AS Msgs
        FROM userchat
        WHERE strftime('%Y', Date) = ?
        GROUP BY Id
        ORDER BY Msgs DESC
        Limit 10
        """, (year,))
    rows = cursor.fetchall()
    return rows


def get_user_rank_top_chatters_year(cursor, year, id):
    # returns user rank in the yearly chat leaderboard
    cursor.execute("""
        SELECT *
        FROM (SELECT RANK() OVER (ORDER BY Sum(Msgs) DESC) AS rank,
            Id,
            SUM(Msgs) AS Msgs
              FROM userchat
              WHERE strftime('%Y', Date) = ?
              GROUP BY Id
              ORDER BY SUM(Msgs) DESC)
        WHERE Id = ?
        """, (year, id))
    rows = cursor.fetchall()
    if len(rows) == 0:
        return "-", id, 0
    return rows[0]


def get_distinct_chatters_count_year(cursor, year):
    # returns how many unique chatters in year
    cursor.execute("""
        SELECT COUNT(DISTINCT Id)
        FROM userchat
        WHERE strftime('%Y', Date) = ?
        """, (year,))
    rows = cursor.fetchall()
    return rows[0][0]


def top_chatters_alltime(cursor):
    # returns top yearly chatters of a particular year
    cursor.execute("""
        SELECT ID, SUM(Msgs) AS Msgs
        FROM userchat
        GROUP BY ID
        ORDER BY SUM(Msgs) DESC
        LIMIT 10
        """)
    rows = cursor.fetchall()
    return rows


def get_user_rank_top_chatters_alltime(cursor, id):
    # returns user rank in the yearly chat leaderboard
    cursor.execute("""
        SELECT *
        FROM (SELECT
                RANK() OVER (ORDER BY SUM(Msgs) DESC) AS rank,
                Id,
                SUM(Msgs) AS Msgs
              FROM userchat
              GROUP BY Id
              ORDER BY SUM(Msgs) DESC)
        WHERE Id = ?
        """, (id,))
    rows = cursor.fetchall()
    return rows[0]


def get_distinct_chatters_count_alltime(cursor):
    # returns how many unique chatters all time
    cursor.execute("""
        SELECT COUNT(DISTINCT Id)
        FROM userchat;
        """)
    rows = cursor.fetchall()
    return rows[0][0]


def get_user_msgs_count_year(cursor, id, year):
    # returns how many messages a user sent in a year
    cursor.execute("""
        SELECT SUM(Msgs)
        FROM userchat
        WHERE Id = ? AND STRFTIME('%Y', Date) = ?
        """, (id, year))
    data = cursor.fetchall()
    return data[0][0]


def get_user_active_days_count_in_year(cursor, id, year):
    # returns how many messages a user sent in a year
    cursor.execute("""
        SELECT COUNT(Msgs)
        FROM userchat
        WHERE Id = ? AND STRFTIME('%Y', Date) = ?
        """, (id, year))
    data = cursor.fetchall()
    return data[0][0]

def get_user_daily_msg_peaks_in_year(cursor, id, year):
    # returns the peak of a year by a user
    cursor.execute("""
        SELECT Date, Msgs
        FROM userchat
        WHERE Id = ? AND STRFTIME('%Y', Date) = ?
        ORDER BY Msgs DESC
        LIMIT 1
        """, (id, year))
    data = cursor.fetchall()
    return data[0]


def get_user_monthly_msg_peaks_in_year(cursor, id, year):
    # returns the monthly messages peak in a year by a user
    cursor.execute("""
        SELECT strftime('%Y-%m', Date) as Month, SUM(Msgs) as total_msgs
        FROM userchat
        WHERE Id = ? AND STRFTIME('%Y', Date) = ?
        GROUP BY Month
        ORDER BY total_msgs DESC
        LIMIT 1
        """, (id, year))
    data = cursor.fetchall()
    return data[0]


def get_user_rank_top_chatters_year_rewind(cursor, id, year):
    cursor.execute("""
        SELECT rank
        FROM (SELECT
                RANK() OVER(ORDER BY SUM(Msgs) DESC) as rank,
                STRFTIME('%Y', Date) AS year,
                SUM(Msgs) as year_msgs
              FROM userchat
              WHERE Id = ?
              GROUP BY year)
        WHERE year = ?
        """, (id, year))
    data = cursor.fetchall()
    return data[0][0]
