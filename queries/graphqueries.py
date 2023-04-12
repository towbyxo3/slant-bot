import sqlite3


def barMonthMessages(cursor, months):
    if months is None:
        cursor.execute("""
            SELECT
                (case
                    when substr("Date", 6, 2) = '01' then 'Jan'
                    when substr("Date", 6, 2) = '02' then 'Feb'
                    when substr("Date", 6, 2) = '03' then 'Mar'
                    when substr("Date", 6, 2) = '04' then 'Apr'
                    when substr("Date", 6, 2) = '05' then 'May'
                    when substr("Date", 6, 2) = '06' then 'Jun'
                    when substr("Date", 6, 2) = '07' then 'Jul'
                    when substr("Date", 6, 2) = '08' then 'Aug'
                    when substr("Date", 6, 2) = '09' then 'Sep'
                    when substr("Date", 6, 2) = '10' then 'Oct'
                    when substr("Date", 6, 2) = '11' then 'Nov'
                    when substr("Date", 6, 2) = '12' then 'Dec'
                end) || ' ''' || substr("Date", 3, 2) as "Month Year",
                SUM("Msgs") as "Total Messages"
            FROM serverchat
            GROUP BY "Month Year"
            ORDER BY Date DESC
        """)

    else:
        cursor.execute("""
            SELECT
                (case
                    when substr("Date", 6, 2) = '01' then 'Jan'
                    when substr("Date", 6, 2) = '02' then 'Feb'
                    when substr("Date", 6, 2) = '03' then 'Mar'
                    when substr("Date", 6, 2) = '04' then 'Apr'
                    when substr("Date", 6, 2) = '05' then 'May'
                    when substr("Date", 6, 2) = '06' then 'Jun'
                    when substr("Date", 6, 2) = '07' then 'Jul'
                    when substr("Date", 6, 2) = '08' then 'Aug'
                    when substr("Date", 6, 2) = '09' then 'Sep'
                    when substr("Date", 6, 2) = '10' then 'Oct'
                    when substr("Date", 6, 2) = '11' then 'Nov'
                    when substr("Date", 6, 2) = '12' then 'Dec'
                end) || ' ''' || substr("Date", 3, 2) as "Month Year",
                SUM("Msgs") as "Total Messages"
            FROM serverchat
            GROUP BY "Month Year"
            ORDER BY Date DESC
            LIMIT ?
        """, (int(months) + 1,))
    data = cursor.fetchall()
    return data


def barMonthMessagesUser(cursor, id, year):
    if year is None:

        cursor.execute("""
            SELECT
                (case
                    when substr("Date", 6, 2) = '01' then 'Jan'
                    when substr("Date", 6, 2) = '02' then 'Feb'
                    when substr("Date", 6, 2) = '03' then 'Mar'
                    when substr("Date", 6, 2) = '04' then 'Apr'
                    when substr("Date", 6, 2) = '05' then 'May'
                    when substr("Date", 6, 2) = '06' then 'Jun'
                    when substr("Date", 6, 2) = '07' then 'Jul'
                    when substr("Date", 6, 2) = '08' then 'Aug'
                    when substr("Date", 6, 2) = '09' then 'Sep'
                    when substr("Date", 6, 2) = '10' then 'Oct'
                    when substr("Date", 6, 2) = '11' then 'Nov'
                    when substr("Date", 6, 2) = '12' then 'Dec'
                end) || ' ''' || substr("Date", 3, 2) as "Month Year",
            SUM("Msgs") as "Total Messages"
            FROM userchat
            WHERE ID = ?
            GROUP BY "Month Year"
            ORDER BY Date DESC
        """, (id,))
    else:

        cursor.execute("""
            SELECT
                (case
                    when substr("Date", 6, 2) = '01' then 'Jan'
                    when substr("Date", 6, 2) = '02' then 'Feb'
                    when substr("Date", 6, 2) = '03' then 'Mar'
                    when substr("Date", 6, 2) = '04' then 'Apr'
                    when substr("Date", 6, 2) = '05' then 'May'
                    when substr("Date", 6, 2) = '06' then 'Jun'
                    when substr("Date", 6, 2) = '07' then 'Jul'
                    when substr("Date", 6, 2) = '08' then 'Aug'
                    when substr("Date", 6, 2) = '09' then 'Sep'
                    when substr("Date", 6, 2) = '10' then 'Oct'
                    when substr("Date", 6, 2) = '11' then 'Nov'
                    when substr("Date", 6, 2) = '12' then 'Dec'
                end) || ' ''' || substr("Date", 3, 2) as "Month Year",
            SUM("Msgs") as "Total Messages"
            FROM userchat
            WHERE ID = ? AND STRFTIME('%Y', Date) = ?
            GROUP BY "Month Year"
            ORDER BY Date DESC
    """, (id, str(year)))
    data = cursor.fetchall()
    return data


def serverMessagesByWeek(cursor, months):
    if months is None:
        cursor.execute("""
            SELECT
              CASE strftime('%w', "Date")
                WHEN '0' THEN 'Sunday'
                WHEN '1' THEN 'Monday'
                WHEN '2' THEN 'Tuesday'
                WHEN '3' THEN 'Wednesday'
                WHEN '4' THEN 'Thursday'
                WHEN '5' THEN 'Friday'
                WHEN '6' THEN 'Saturday'
              END as day_of_week,
              SUM("Msgs") as total_msgs
            FROM serverchat
            GROUP BY day_of_week
            ORDER BY
              CASE day_of_week
                WHEN 'Sunday' THEN 7
                WHEN 'Monday' THEN 1
                WHEN 'Tuesday' THEN 2
                WHEN 'Wednesday' THEN 3
                WHEN 'Thursday' THEN 4
                WHEN 'Friday' THEN 5
                WHEN 'Saturday' THEN 6
              END ASC;
        """)
    else:
        cursor.execute("""
            SELECT
              CASE strftime('%w', "Date")
                WHEN '0' THEN 'Sunday'
                WHEN '1' THEN 'Monday'
                WHEN '2' THEN 'Tuesday'
                WHEN '3' THEN 'Wednesday'
                WHEN '4' THEN 'Thursday'
                WHEN '5' THEN 'Friday'
                WHEN '6' THEN 'Saturday'
              END as day_of_week,
              SUM("Msgs") as total_msgs
            FROM serverchat
            WHERE "Date" BETWEEN date('now', 'start of month', ?) AND date('now')
            GROUP BY day_of_week
            ORDER BY
              CASE day_of_week
                WHEN 'Sunday' THEN 7
                WHEN 'Monday' THEN 1
                WHEN 'Tuesday' THEN 2
                WHEN 'Wednesday' THEN 3
                WHEN 'Thursday' THEN 4
                WHEN 'Friday' THEN 5
                WHEN 'Saturday' THEN 6
              END ASC;
        """, (f'-{months} months',))

    data = cursor.fetchall()
    return data


def serverMessagesUserByWeek(cursor, id, year):
    if year is None:
        cursor.execute("""
            SELECT
              CASE strftime('%w', "Date")
                WHEN '0' THEN 'Sunday'
                WHEN '1' THEN 'Monday'
                WHEN '2' THEN 'Tuesday'
                WHEN '3' THEN 'Wednesday'
                WHEN '4' THEN 'Thursday'
                WHEN '5' THEN 'Friday'
                WHEN '6' THEN 'Saturday'
              END as day_of_week,
              SUM("Msgs") as total_msgs
            FROM userchat
            WHERE id = ?
            GROUP BY day_of_week
            ORDER BY
              CASE day_of_week
                WHEN 'Sunday' THEN 7
                WHEN 'Monday' THEN 1
                WHEN 'Tuesday' THEN 2
                WHEN 'Wednesday' THEN 3
                WHEN 'Thursday' THEN 4
                WHEN 'Friday' THEN 5
                WHEN 'Saturday' THEN 6
              END ASC;
        """, (id,))
    else:
        cursor.execute("""
            SELECT
              CASE strftime('%w', "Date")
                WHEN '0' THEN 'Sunday'
                WHEN '1' THEN 'Monday'
                WHEN '2' THEN 'Tuesday'
                WHEN '3' THEN 'Wednesday'
                WHEN '4' THEN 'Thursday'
                WHEN '5' THEN 'Friday'
                WHEN '6' THEN 'Saturday'
              END as day_of_week,
              SUM("Msgs") as total_msgs
            FROM userchat
            WHERE id = ? AND STRFTIME('%Y', Date) = ?
            GROUP BY day_of_week
            ORDER BY
              CASE day_of_week
                WHEN 'Sunday' THEN 7
                WHEN 'Monday' THEN 1
                WHEN 'Tuesday' THEN 2
                WHEN 'Wednesday' THEN 3
                WHEN 'Thursday' THEN 4
                WHEN 'Friday' THEN 5
                WHEN 'Saturday' THEN 6
              END ASC
        """, (id, str(year)))

    data = cursor.fetchall()
    return data


def messagesPerMonth(cursor):
    cursor.execute("""
        SELECT strftime('%Y-%m', "Date") as "Year-Month", SUM("Msgs") as "Total Messages"
        FROM serverchat
        GROUP BY "Year-Month"
    """)
    data = cursor.fetchall()
    return data


def dailyServerMessages(cursor, date):
    """
    Returns daily messages of a server
    """
    cursor.execute("""
        SELECT SUM(Msgs),
               SUM(Chars)
        FROM serverchat
        WHERE Date = ?
        """, (date,))
    rows = cursor.fetchall()
    if len(rows) == 0:
        return 0
    return rows[0][0]


def userDailyMessages(cursor, date, id):
    """
    returns daily messages of a user
    """
    cursor.execute("""
        SELECT Date, Msgs
        FROM userchat
        WHERE Date = ? and Id = ?
        GROUP BY Id
        """, (date, id))
    rows = cursor.fetchall()
    if len(rows) == 0:
        return ((date, 0),)
    return rows
