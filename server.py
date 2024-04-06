# -*- coding: utf-8 -*-
import random
from collections import defaultdict

from flask import Flask, render_template, redirect
from flask import request


app = Flask(__name__, template_folder='templates', static_folder='static')
HOST = '0.0.0.0'
PORT = 5100


class CitiesGameException(Exception):
    def __init__(self, msg):
        self.msg = msg


class Game(object):
    UNKNOWN_CITY = [
        "Такого города не существует! Предложи другой:",
        "Не знаю такой город, назови другой:",
        "Такого города нет в моём списке. Предложи другой:"
    ]
    USED_CITY = [
        "Этот город уже был! Давай вспомним какой-нибудь другой:",
        "Этот город уже был в игре, назови другой:"
    ]
    BYE_PHRASES = [
        "стоп",
        "конец",
        "хватит",
        "устал",
        "надоело",
        "отстань",
        "пока-пока",
        "всё"
    ]

    def __init__(self):
        self.__allowed_cities = defaultdict(list)
        self.__guessed_cities = set()
        self.__previous_city = None
        self.__status = "init"

        with open("resources/ru_cities.txt", "r", encoding='utf-8') as f:
            for city in f:
                city = city.strip()
                if city:
                    self.__allowed_cities[city[0]].append(city)

    def init_game(self):
        self.__previous_city = None
        self.__status = "init"

    @staticmethod
    def get_city_name(city):
        if '-' in city:
            return "-".join([w.title() for w in city.split("-")])
        elif ' ' in city:
            return " ".join([w.title() for w in city.split()])
        else:
            return city.title()

    @staticmethod
    def __has_except_endings(word):
        return word in 'ъыь'

    def __is_cities_exausted(self, letter):
        return self.__allowed_cities[letter] == []

    def is_all_cities_exausted(self):
        return not self.__allowed_cities

    def __find_index_of_right_letter(self, previous_city):
        ind = -1
        last_letter = previous_city[ind]
        while self.__has_except_endings(last_letter) or self.__is_cities_exausted(last_letter):
            ind -= 1
            last_letter = previous_city[ind]
        return ind

    def __get_last_city(self):
        return self.__previous_city
    
    def __get_right_letter_by_rules(self, city):
        return city[self.__find_index_of_right_letter(city)]

    def __check_rules(self, word):
        if self.__previous_city:
            return self.__get_right_letter_by_rules(self.__previous_city) == word[0]
        return True

    def __make_city_used(self, city):
        self.__previous_city = city
        self.__guessed_cities.add(city)
        self.__allowed_cities[city[0]].remove(city)
        if len(self.__allowed_cities[city[0]]) == 0:
            del self.__allowed_cities[city[0]]

    def check_city_correctness(self, city):
        if city in self.__guessed_cities:
            raise CitiesGameException(random.choice(self.USED_CITY))
        elif city[0] not in self.__allowed_cities or city not in self.__allowed_cities[city[0]]:
            raise CitiesGameException(random.choice(self.UNKNOWN_CITY))
        elif not self.__check_rules(city):
            letter = self.__get_right_letter_by_rules(self.__get_last_city()).upper()
            raise CitiesGameException(f"Твой город должен начинаться с буквы \'{letter}\'!")
        else:
            self.__make_city_used(city)

    def move(self):
        last_letter = self.__get_right_letter_by_rules(self.__get_last_city())
        city = random.choice(self.__allowed_cities[last_letter])
        self.__make_city_used(city)
        return self.get_city_name(city)

    def is_over(self):
        return self.__status == "over"

    def set_status(self, value):
        self.__status = value

    def get_status(self):
        return self.__status

    def clean(self):
        for city in self.__guessed_cities:
            self.__allowed_cities[city[0]].append(city)
        self.__guessed_cities.clear()


@app.route("/game", methods=['POST', 'GET'])
def game():
    if request.method == 'POST':
        city = request.form['city'].strip().lower()
        try:
            if city in city_game.BYE_PHRASES:
                city_game.set_status("over")
                # TODO redirect to home page with another text
                # greeting = 'Пока-пока! Хочешь сыграть ещё раз?'

                city_game.clean()
                return redirect('/')
            else:
                city_game.check_city_correctness(city)
                game_status = 'over' if city_game.is_all_cities_exausted() else 'proceed'
                city_game.set_status(game_status)
                text = city_game.move()
                cls = 'n'
        except Exception as e:
            text = e
            cls = 'e'
        return render_template('game.html', data={'value': text, 'cls': cls})
    else:
        cls = 'n'
        return render_template('game.html', data={'value': 'Начинай игру первым и вводи город:', 'cls': cls})


@app.route("/")
def index():
    city_game.init_game()
    greeting = 'Приветствую!'
    return render_template('index.html', data={'greeting': greeting})


if __name__ == '__main__':
    city_game = Game()
    app.run(host=HOST, port=PORT)
