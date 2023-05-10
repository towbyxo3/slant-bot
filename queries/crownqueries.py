def get_crowns_history(cursor):
    """
    Retrieves most recent crowns.
    """
    cursor.execute("""
        SELECT *
        FROM(
            SELECT DISTINCT uc.Date, uc.Id, uc.Msgs
            FROM userchat AS uc
            JOIN (
              SELECT Date, MAX(Msgs) AS MaxMsgs
              FROM userchat
              GROUP BY Date
            ) AS sub
            ON uc.Date = sub.Date AND uc.Msgs = sub.MaxMsgs
            )
        ORDER BY Date Desc
        """)
    rows = cursor.fetchall()
    return rows


def get_user_crown_history(cursor, id):
    """
    Retrieves most recent crowns by a user
    """
    cursor.execute("""
        SELECT * FROM(
                SELECT DISTINCT uc.Date, uc.Id, uc.Msgs
                FROM userchat AS uc
                JOIN (
                  SELECT Date, MAX(Msgs) AS MaxMsgs
                  FROM userchat
                  GROUP BY Date
                ) AS sub
                ON uc.Date = sub.Date AND uc.Msgs = sub.MaxMsgs
                )
        WHERE ID = ?
        ORDER BY Date Desc
        """, (id,))
    rows = cursor.fetchall()
    return rows


def top_10_crowns(cursor):
    ###
    cursor.execute("""
        SELECT sub.Id, COUNT(*) AS Frequency
        FROM (
          SELECT DISTINCT uc.Date, uc.Id, uc.Msgs
          FROM userchat AS uc
          JOIN (
            SELECT Date, MAX(Msgs) AS MaxMsgs
            FROM userchat
            WHERE Msgs > 5
            GROUP BY Date
          ) AS sub
          ON uc.Date = sub.Date AND uc.Msgs = sub.MaxMsgs
        ) AS sub
        GROUP BY sub.Id
        ORDER BY Frequency DESC
        LIMIT 10
        """)
    rows = cursor.fetchall()
    return rows


def get_user_crown_rank(cursor, id):
    cursor.execute("""
        SELECT *
        FROM (
          SELECT sub.Id, COUNT(*) AS Frequency, RANK() OVER (ORDER BY COUNT(*) DESC) AS Rank
          FROM (
            SELECT DISTINCT uc.Date, uc.Id, uc.Msgs
            FROM userchat AS uc
            JOIN (
              SELECT Date, MAX(Msgs) AS MaxMsgs
              FROM userchat
              WHERE Msgs > 5
              GROUP BY Date
            ) AS sub
            ON uc.Date = sub.Date AND uc.Msgs = sub.MaxMsgs
          ) AS sub
          GROUP BY sub.Id
          ORDER BY Frequency DESC
        ) AS sub
        WHERE Id = ?
        """, (id,))
    rows = cursor.fetchall()
    if len(rows) == 0:
        return id, 0, "unranked"
    return rows[0]
