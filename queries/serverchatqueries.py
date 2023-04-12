import sqlite3



def dailyServerMessages(cursor, date):
    # returns weekly messages in a particular year and week
    cursor.execute("""
        SELECT SUM(Msgs),
               SUM(Chars)
        FROM serverchat
        WHERE Date = ?
        """,(date,))
    rows = cursor.fetchall()
    return rows [0]



def weeklyServerMessages(cursor, year, week):
    # returns weekly messages in a particular year and week
    cursor.execute("""
        SELECT SUM(Msgs),
               SUM(Chars)
        FROM serverchat
        WHERE strftime('%Y', Date) = ? AND strftime('%W', Date) = ?
        """,(year,week))
    rows = cursor.fetchall()
    return rows [0]



### monthly




def monthlyServerMessages(cursor, year, month):
    # returns monthly messages in a particular year
    cursor.execute("""
        SELECT SUM(Msgs),
               SUM(Chars)
        FROM serverchat
        WHERE strftime('%Y', Date) = ? AND strftime('%m', Date) = ?
        """, (year, month))
    rows = cursor.fetchall()
    return rows[0]

### yearly




def yearlyServerMessages(cursor, year):
    # returns yearly messages in a particular year
    cursor.execute("""
        SELECT SUM(Msgs),
               SUM(Chars)
        FROM serverchat
        WHERE strftime('%Y', Date) = ?
        """, (year,))
    rows = cursor.fetchall()
    return rows[0]


### ALL TIME





def ServerMessages(cursor):
    # returns alltime messages
    cursor.execute("""
        SELECT SUM(Msgs),
               SUM(Chars)
        FROM serverchat
        """)
    rows = cursor.fetchall()
    return rows[0]


## how many days, weeks, months, years


def dayEntries(cursor):
    cursor.execute("""
        SELECT COUNT(Date)
        FROM serverchat 
        """)
    rows = cursor.fetchall()
    return rows[0][0]

def weekEntries(cursor):
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


def monthEntries(cursor):
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


def yearEntries(cursor):
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


def dailyMessagesYearCounter(cursor, year):
    cursor.execute("""
        SELECT COUNT(date)
        FROM serverchat
        WHERE strftime('%Y', Date) = ?
        """,(year,))
    rows = cursor.fetchall()
    return rows[0][0]


def yearlyMessagesPeakMonth(cursor, year):
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

def yearlyMessagesPeak(cursor, year):
    # returns the peak of a year by a user
    cursor.execute("""
        SELECT Date, Msgs
        FROM serverchat
        WHERE STRFTIME('%Y', Date) = ?
        ORDER BY Msgs DESC
        """, (year,))
    data = cursor.fetchall()
    return data[0]


def YearServerMessagesRank(cursor, year):
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
