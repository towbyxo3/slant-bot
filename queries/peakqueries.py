import sqlite3 


def TopChatUserPeaks(cursor):
    # returns chat peaks by users in a day
    cursor.execute("""
        SELECT Date, Id, Msgs
        FROM userchat
        ORDER BY Msgs DESC
        LIMIT 10
        """)
    rows = cursor.fetchall()
    return rows


def TopChatUserPeaksRank(cursor, id):
    # returns users own personal peak and ranking in day peak leaderboard
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


def TopChatUserPeaksWeek(cursor):
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


def TopChatUserPeaksWeekRank(cursor, id):
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


def TopChatUserPeaksMonth(cursor):
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



def TopChatUserPeaksMonthRank(cursor, id):
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


def TopChatUserPeaksYear(cursor):
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


def TopChatUserPeaksYearRank(cursor, id):
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