import os
import re

from flask import *

from scripts.database_scripts import init_database, add_syntagma_to_db, add_words_to_db, add_syllables_to_db, \
    find_word_in_db

app = Flask(__name__)

UPLOAD_FOLDER = './static/uploads'
ALLOWED_EXTENSIONS = {'seg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


@app.route('/')
def main():
    return render_template("index.html")


def allowed_file(filename: str):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/add_syntagma', methods=['POST'])
def add_syntagma():
    if request.method == 'POST':
        text = request.values['text']
        if len(text.strip()) > 0:
            db_name = "synt_syllab.db"
            if not os.path.exists(db_name):
                init_database(db_name)
            synt_index = add_syntagma_to_db(text, db_name)
            cleaned_string = re.sub(r'[^A-Za-zА-Яа-яЁё\s]', '', text)
            words = cleaned_string.split()
            add_words_to_db(words, db_name, synt_index)
            return render_template("enter_syllables.html", words=words)
        else:
            return render_template("error.html", error_text="Текст неверного формата")


@app.route('/add_syllables', methods=['POST'])
def add_syllables():
    if request.method == 'POST':
        values = request.values
        if len(values) > 0:
            db_name = "synt_syllab.db"
            if not os.path.exists(db_name):
                return render_template("error.html", error_text="Не было введено ни одного предложения!")
            add_syllables_to_db(values, db_name)
            return render_template("index.html")
        else:
            return render_template("error.html", error_text="Слоги не были введены!")


@app.route('/find_word', methods=['POST'])
def find_word():
    if request.method == 'POST':
        word = request.values['word']
        if len(word.strip().split()) == 1:
            db_name = "synt_syllab.db"
            if not os.path.exists(db_name):
                return render_template("error.html", error_text="Не было введено ни одного предложения!")
            words, syllables, sentences = find_word_in_db(word.strip(), db_name)
            if len(words) == 0:
                return render_template("error.html", error_text="Слово не найдено в базе данных")
            return render_template("found_word.html", word=word, sentences=sentences, syllables=syllables)
        else:
            return render_template("error.html", error_text="Введите только одно слово!")


if __name__ == '__main__':
    app.run(debug=False)
