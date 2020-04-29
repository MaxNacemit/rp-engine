import threading
import time
import json


class ManaCounter:
    def __init__(self):
        self.mages = dict()
        self.sources = dict()
        self.locations = dict()
        self.regenerator = threading.Thread(None, self.time_regenerate)
        self.regenerator.start()

    def add_player(self, player_name, player_const, player_mana, player_regeneration):
        self.mages[player_name] = {'mana_const': player_const, 'current_mana': player_mana, 'max_mana': player_mana,
                                   'regeneration': player_regeneration, 'lifetime_cast': 0}
        self.sources[player_name] = None
        self.locations[author] = None

    def attune_player(self, player_name, location_id):
        self.sources[player_name] = location_id

    def modify_parameter(self, player_name, parameter, modify_expression):
        expression = modify_expression.lstrip.split()
        if not expression[1].isdigit():
            return "Некорректное выражение!"
        else:
            if expression[0] == "+":
                self.mages[player_name][parameter] += float(expression[1])
            elif expression[0] == '-':
                self.mages[player_name][parameter] -= float(expression[1])
            elif expression[0] == '*':
                self.mages[player_name][parameter] *= float(expression[1])
            elif expression[0] == '/':
                self.mages[player_name][parameter] = self.mages[player_name][parameter] / float(expression[1])
            else:
                return "Некорректный знак действия!"
        return "Параметр изменен успешно!"

    def cast_spell(self, player, spell_dependencies, spell_params, base_cost):
        # :param: spell_dependencies - словарь вида {'название параметра': 'тип зависимости'}
        # :param: spell_params - аналогично прошлому пункту, но значение словаря - значение данного параметра
        cost = base_cost
        for param in spell_dependencies.keys():
            if spell_dependencies[param] == 'lin':
                cost = cost * float(spell_params[param])
            elif spell_dependencies[param] == 'div':
                cost = cost / float(spell_params[param])
            elif spell_dependencies[param] == 'sqr':
                cost = cost * (float(spell_params[param]) ** 2)
            elif spell_dependencies[param] == 'dsq':
                cost = cost / (float(spell_params[param]) ** 2)
            elif spell_dependencies[param] == 'exp':
                cost = cost ** float(spell_params[param])
        self.mages[player]['current_mana'] -= int(cost)
        self.mages[player]['lifetime_cast'] += int(cost)

    def regenerate(self, player):
        if not self.locations[player] == self.sources[player]:
            self.mages[player]['current_mana'] += 5 * self.mages[player][
                'regeneration']  # 5 - потому что в 1 посте 5 секунд; эта штука выполняется при оставлении поста игроком
        else:
            self.mages[player]['current_mana'] += 10 * self.mages[player]['regeneration']

    def time_regenerate(self):
        # функция восстанавливает ману всем на максимум раз в трое суток
        players = self.mages.keys()
        for player in players:
            self.mages[player]['current_mana'] = self.mages[player]['max_mana']
        time.sleep(259200)
        time_regenerate()

    def compute_post(self, location, author, content, spells_json, database): #да, в эту штуку надо будет передавать объект БД как параметр
        spell_dict = json.loads(spells_json)
        for spell_data in spell_dict:
            spell_id = int(spell_data['spell'])
            dependency_dict = dict()
            for param in spell_data['params'].keys():
                database.cursor.execute('SELECT * FROM spell_reqs WHERE req_title=%s AND spell=%s', (param, spell_id))
                param_tuple = database.cursor.fetchone()
                dependency_dict[param_tuple[1]] = param_tuple[3]
            base_cost = database.get_spell_dict(spell_id)
            self.cast_spell(author, dependency_dict, spell_data['params'], int(base_cost))
        self.locations[author] = location
        database.make_post(location, author, content, spell_dict)
        self.regenerate(author)
