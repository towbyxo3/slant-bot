import sqlite3
import wordcloud


def getTopWords(cursor):
    # Connect to the database

    # Get the list of stopwords from the wordcloud library
    stopwords = wordcloud.STOPWORDS

    # Convert the stopwords to a list of strings
    stopwords = [str(stopword) for stopword in stopwords]

    # Fetch the top 500 words from the words table, excluding the stopwords
    cursor.execute('''
        SELECT word, COUNT(word)
        FROM words
        WHERE LENGTH(word) > 2 AND LOWER(word) NOT IN ({})
        GROUP BY word
        ORDER BY COUNT(word) DESC
        LIMIT 20
    '''.format(','.join('?' * len(stopwords))), stopwords)

    # Convert the results to a list of tuples
    top_words = [(row[0], row[1]) for row in cursor]

    return top_words


def getTopWordsUser(cursor, id):

    # Get the list of stopwords from the wordcloud library
    stopwords = wordcloud.STOPWORDS

    # Convert the stopwords to a list of strings
    stopwords = [str(stopword) for stopword in stopwords]

    # Fetch the top 500 words from the words table, excluding the stopwords
    cursor.execute('''
        SELECT word, COUNT(word)
        FROM words
        WHERE ID = {} AND LENGTH(word) > 2 AND LOWER(word) NOT IN ({})
        GROUP BY word
        ORDER BY COUNT(word) DESC
        LIMIT 20
    '''.format(id, ','.join('?' * len(stopwords))), stopwords)

    # Convert the results to a list of tuples
    top_words = [(row[0], row[1]) for row in cursor]

    return top_words


def getTotalWordCountUser(cursor, id):
    cursor.execute("""
            SELECT COUNT(id)
            FROM words
            WHERE ID = ?
            """, (id,))
    word_count = cursor.fetchall()[0][0]
    return word_count


def getUserDistinctWords(cursor, id):
    cursor.execute("""
        SELECT COUNT(DISTINCT Word)
        FROM words
        WHERE Id = ?
        """, (id,))
    distinct_words = cursor.fetchall()[0][0]
    return distinct_words


def getTotalWordCountServer(cursor):

    cursor.execute("""
            SELECT COUNT(id)
            FROM words
            """)
    word_count = cursor.fetchall()[0][0]
    return word_count


"""
rank = 1
for word, count in getTopWordsUser():
    print(rank, word, count)
    rank+=1
"""


def getServerDistinctWords(cursor):
    cursor.execute("""
        SELECT COUNT(DISTINCT Word)
        FROM words
        """)
    distinct_words = cursor.fetchall()[0][0]
    return distinct_words


def getWordUserFrequency(cursor, id, word):
    cursor.execute("""
            SELECT COUNT(id)
            FROM words
            WHERE ID = ? AND word = ?
            """, (id, word.upper()))
    word_count = cursor.fetchall()[0][0]
    return word_count


def getWordLeaderboardUser(cursor, word):
    cursor.execute("""
            SELECT id, COUNT(id)
            FROM words
            WHERE word = ?
            GROUP BY id
            ORDER BY COUNT(id) DESC
            LIMIT 10
            """, (word.upper(), ))
    rows = cursor.fetchall()
    return rows


def getWordCount(cursor, word):
    cursor.execute("""
            SELECT COUNT(id)
            FROM words
            WHERE word = ?
            """, (word.upper(), ))
    count = cursor.fetchall()[0][0]
    return count


def getFrequencyWordOfUser(cursor, id, word):
    cursor.execute("""
        SELECT COUNT(word)
        FROM words
        WHERE id = ? AND word = ?
        """, (id, word.upper()))
    count = cursor.fetchall()[0][0]
    return count
