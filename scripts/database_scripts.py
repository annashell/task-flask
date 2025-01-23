import sqlite3

from flask import render_template


def create_init_sql_query():
    """
    Создает sql запрос для создания БД
    :return:
    """
    query: str = '''CREATE TABLE syntagma_units (
                                    syntagma_id INTEGER PRIMARY KEY,
                                    syntagma_text TEXT NOT NULL);

                                    CREATE TABLE words_units (
                                        word_id INTEGER PRIMARY KEY,
                                        word_text TEXT NOT NULL,
                                        syntagma_index INTEGER,
                                        FOREIGN KEY(syntagma_index) REFERENCES syntagma_units(syntagma_id));

                                        CREATE TABLE syllable_units (
                                        syllable_id INTEGER PRIMARY KEY,
                                        word_index INTEGER NOT NULL,
                                        pos_in_word INTEGER,
                                        syllable_text TEXT NOT NULL,
                                        FOREIGN KEY(word_index) REFERENCES words_units(word_id));'''.strip()

    with open('sqlite_create_tables.sql', "w", encoding="UTF-8") as wh:
        wh.write(query)


def init_database(db_name):
    """
    Создает БД
    :return:
    """
    try:
        sqlite_connection = sqlite3.connect(db_name)
        cursor = sqlite_connection.cursor()
        print("База данных подключена к SQLite")

        create_init_sql_query()

        with open('sqlite_create_tables.sql', 'r') as sqlite_file:
            sql_script = sqlite_file.read()

        cursor.executescript(sql_script)
        sqlite_connection.commit()
        cursor.close()
        print("Скрипт SQLite успешно выполнен")

    except sqlite3.Error as error:
        print("Ошибка при подключении к sqlite", error)
        return render_template("error.html", error_text="Ошибка подключения к базе данных")
    finally:
        if sqlite_connection:
            sqlite_connection.close()
            print("Соединение с SQLite закрыто")


def add_syntagma_to_db(text, db_name):
    """
    Добавляет введенную синтагму в БД
    :return:
    """
    connection = sqlite3.connect(db_name)
    cursor = connection.cursor()
    insert_query = f"""INSERT INTO syntagma_units (syntagma_id, syntagma_text)  VALUES  (?, ?)"""
    get_table_size_query = f"""SELECT COUNT(*) FROM syntagma_units"""

    row_count = cursor.execute(get_table_size_query).fetchone()

    # считаем уже добавленные в базу синтагмы для задания id
    if row_count is not None:
        number_of_syntagmas = row_count[0]
    else:
        number_of_syntagmas = 0

    data = [
        (number_of_syntagmas, text)
    ]

    cursor.executemany(insert_query, data)
    connection.commit()
    cursor.close()
    return number_of_syntagmas


def add_words_to_db(words, db_name, synt_index):
    """
    Добавляет слова введенной синтагмы в БД
    :return:
    """
    connection = sqlite3.connect(db_name)
    cursor = connection.cursor()
    get_table_size_query = f"""SELECT COUNT(*) FROM words_units"""

    row_count = cursor.execute(get_table_size_query).fetchone()

    # считаем уже добавленные в базу слова для задания id
    if row_count is not None:
        number_of_words = row_count[0]
    else:
        number_of_words = 0

    for i, word in enumerate(words):
        insert_query = f"""INSERT INTO words_units (word_id, word_text, syntagma_index)  VALUES  (?, ?, ?)"""

        data = [
            (number_of_words + i, word, synt_index)
        ]

        cursor.executemany(insert_query, data)
        connection.commit()

    cursor.close()


def add_syllables_to_db(words, db_name):
    """
        Добавляет введенные слоги в БД
        :return:
    """
    connection = sqlite3.connect(db_name)
    cursor = connection.cursor()
    get_table_size_query = f"""SELECT COUNT(*) FROM syllable_units"""

    row_count = cursor.execute(get_table_size_query).fetchone()

    # считаем уже добавленные в базу слоги для задания id
    if row_count is not None:
        number_of_syllables = row_count[0]
    else:
        number_of_syllables = 0

    syll_count = 0

    for i, word in enumerate(dict(words).values()):
        word_joined = word.replace("-", "")
        get_word_index_query = f"""SELECT word_id FROM words_units as wu WHERE wu.word_text='{word_joined}'"""
        # находим индекс слова, к которому относится слог, в БД
        word_count = cursor.execute(get_word_index_query).fetchone()[-1]

        insert_query = f"""INSERT INTO syllable_units (syllable_id, word_index, pos_in_word, syllable_text)  VALUES  (?, ?, ?, ?)"""

        syllables = word.split("-")
        for j, syll in enumerate(syllables):
            data = [
                (number_of_syllables + syll_count, word_count, j, syll)
            ]
            syll_count += 1
            cursor.executemany(insert_query, data)
            connection.commit()

    cursor.close()


def find_word_in_db(word, db_name):
    """
        Ищет слово в БД, выводит его разбиение на слоги и соответствующее предложение
        :return:
    """
    words, syllables, sentences = [], [], []

    connection = sqlite3.connect(db_name)
    cursor = connection.cursor()
    get_words_query = f"""SELECT * FROM words_units as wu WHERE wu.word_text='{word}'"""

    words_ = cursor.execute(get_words_query).fetchall()
    if words_ is not None:
        words = words_
        for (word_id, word_text, syntagma_index) in words_:
            get_syntagma_query = f"""SELECT * FROM syntagma_units as su WHERE su.syntagma_id='{syntagma_index}'"""
            get_syllables_query = f"""SELECT * FROM syllable_units as su WHERE su.word_index='{word_id}'"""

            sentence = cursor.execute(get_syntagma_query).fetchone()[1]
            sentences.append(sentence)
            syllables_db = cursor.execute(get_syllables_query).fetchall()

            # объединяем слоги в слова через - для вывода на экран
            new_word = ""
            for (syl_id, w_ind, pos, syl_text) in syllables_db:
                if pos == 0:
                    if len(new_word) > 0:
                        syllables.append(new_word)
                    new_word = syl_text
                else:
                    new_word += "-" + syl_text
            if len(new_word) > 0:
                syllables.append(new_word)

    cursor.close()
    return words, syllables, sentences
