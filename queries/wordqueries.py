import wordcloud


def get_top_words_server(cursor):
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


def get_top_words_user(cursor, id):

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


def get_word_sample_size_user(cursor, id):
    cursor.execute("""
            SELECT COUNT(id)
            FROM words
            WHERE ID = ?
            """, (id,))
    word_count = cursor.fetchall()[0][0]
    return word_count


def get_distinct_words_count_user(cursor, id):
    cursor.execute("""
        SELECT COUNT(DISTINCT Word)
        FROM words
        WHERE Id = ?
        """, (id,))
    distinct_words = cursor.fetchall()[0][0]
    return distinct_words


def get_word_sample_size_server(cursor):

    cursor.execute("""
            SELECT COUNT(id)
            FROM words
            """)
    word_count = cursor.fetchall()[0][0]
    return word_count


def get_distinct_words_count_server(cursor):
    cursor.execute("""
        SELECT COUNT(DISTINCT Word)
        FROM words
        """)
    distinct_words = cursor.fetchall()[0][0]
    return distinct_words


def get_vocab_user(cursor, word):
    print(word)
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


def get_word_frequency_server(cursor, word):
    cursor.execute("""
            SELECT COUNT(id)
            FROM words
            WHERE word = ?
            """, (word.upper(), ))
    count = cursor.fetchall()[0][0]
    return count


def get_word_frequency_user(cursor, id, word):
    cursor.execute("""
        SELECT COUNT(word)
        FROM words
        WHERE id = ? AND word = ?
        """, (id, word.upper()))
    count = cursor.fetchall()[0][0]
    return count
