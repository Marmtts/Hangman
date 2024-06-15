from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
import random

# Aplikacja flask
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'  
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hangman.db' 
db = SQLAlchemy(app)

#Ranking punktów
class HighScore(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # ID
    name = db.Column(db.String(80), nullable=False)  # nazwa gracza
    score = db.Column(db.Integer, nullable=False)  # wynik gracza

    def __repr__(self):
        return f'<HighScore {self.name} - {self.score}>'

#Załadowanie słów z z pliku hangman_words.txt
with open('hangman_words.txt') as f:
    WORDS = f.read().splitlines()

#Funkcja do wyboru losowego słowa z pliku
def choose_word():
    with open('hangman_words.txt') as f:
        words = f.read().split(',')
    return random.choice(words)

#główna strona z rankingiem
@app.route('/')
def index():
    high_scores = HighScore.query.order_by(HighScore.score.desc()).limit(10).all()  # Pobranie 10 najwyższych wyników
    return render_template('index.html', high_scores=high_scores)

#nowa gra
@app.route('/start', methods=['POST'])
def start():
    session['word'] = choose_word()  #Wybór losowego słowa
    session['guesses'] = []  #Inicjalizacja listy zgadniętych liter
    session['wrong_guesses'] = 0  #licznik błędnych zgadywań
    return redirect(url_for('game'))

#funkcja do generowania wyświetlanego słowa z ukrytymi literami
def generate_displayed_word(word, guesses):
    displayed_word = ''
    for char in word:
        if char in guesses:
            displayed_word += char
        else:
            displayed_word += '_'
    return displayed_word

#strona gry, wyświetlająca aktualny stan gry
@app.route('/game')
def game():
    word = session.get('word', '')  #pobranie słowa z sesji
    guesses = session.get('guesses', [])  # pobranie zgadniętych liter z sesji
    wrong_guesses = session.get('wrong_guesses', 0)  # pobranie liczby błędnych zgadywań z sesji
    displayed_word = session.get('displayed_word', '_' * len(word))  # wyświetlane słowo, domyślnie same podkreślniki

    game_over = wrong_guesses >= 6 or set(word) <= set(guesses)  # sprawdzenie, czy gra się skończyła
    won = set(word) <= set(guesses)  # sprawdzenie, czy gracz wygrał

    max_wrong_guesses = 6  #maksymalna liczba błędnych zgadywań
    score = max_wrong_guesses - wrong_guesses  #obliczenie wyniku

    return render_template('game.html', word=displayed_word, guesses=guesses, wrong_guesses=wrong_guesses, game_over=game_over, won=won, score=score)

# Przetwarzanie zgadywania litery
@app.route('/guess', methods=['POST'])
def guess():
    guess = request.form.get('guess').lower()  # pobranie zgadniętej litery z formularza
    if guess:
        if guess not in session['guesses']:  # sprawdzenie, czy litera nie była wcześniej zgadywana
            session['guesses'].append(guess)
            if guess not in session['word']:  #jeśli litera jest błędna, zwiększenie licznika błędów
                session['wrong_guesses'] += 1
            else:
                #aktualizacja wyświetlanego słowa
                word = session['word']
                displayed_word = ''.join([char if char in session['guesses'] else '_' for char in word])
                session['displayed_word'] = displayed_word
    return redirect(url_for('game'))

#zakończenie gry i zapisanie wyniku
@app.route('/end', methods=['POST'])
def end():
    if 'word' in session and set(session['word']) <= set(session['guesses']):  #sprawdzenie, czy gracz wygrał
        max_wrong_guesses = 6
        score = max_wrong_guesses - session['wrong_guesses']  #obliczenie wyniku
        name = request.form.get('name')  #pobranie nazwy gracza z formularza
        new_score = HighScore(name=name, score=score)  #utworzenie nowego rekordu wyniku
        db.session.add(new_score)  #dodanie rekordu do bazy danych
        db.session.commit()  # zapisanie zmian w bazie danych
    session.clear()  
    return redirect(url_for('index'))

#usunięcie wszystkich rekordów wyników
@app.route('/clear_high_scores', methods=['POST'])
def clear_high_scores():
    HighScore.query.delete()  # usunięcie wszystkich rekordów z tabeli HighScore
    db.session.commit()  # Zapisanie zmian w bazie danych
    return redirect(url_for('index'))

# Uruchomienie aplikacji
if __name__ == '__main__':
    with app.app_context():
        db.create_all()  #utworzenie tabeli w bazie danych, jeśli jeszcze nie istnieje
    app.run()  
