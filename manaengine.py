import threading


class ManaCounter():
    def __init__(self):
        self.mages = dict()
        self.regenerator = threading.Thread(None, self.time_regenerate)
        self.regenerator.start()

    def add_player(self, player_name, player_const, player_mana, player_regeneration):
        self.mages[player_name] = {'mana_const': player_const, 'current_mana': player_mana, 'max_mana': player_mana, 'regeneration': player_regeneration, 'lifetime_cast': 0}

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
                cost = cost * spell_params[param]
            elif spell_dependencies[param] == 'div':
                cost = cost / spell_params[param]
            elif spell_dependencies[param] == 'sqr':
                cost = cost * (spell_params[param] ** 2)
            elif spell_dependencies[param] == 'dsq':
                cost = cost / (spell_params[param] ** 2)
            elif spell_dependencies[param] == 'exp':
                cost = cost ** spell_params[param]
        self.mages[player]['current_mana'] -= int(cost)
        self.mages[player]['lifetime_cast'] += int(cost)

    def regenerate(self, player):
        self.mages[player]['current_mana'] += 5 * self.mages[player]['regeneration'] #5 - потому что в 1 посте 5 секунд; эта штука выполняется при оставлении поста игроком

    def time_regenerate(self):
        # функция восстанавливает ману всем на максимум раз в трое суток
        players = self.mages.keys()
        for player in players:
            self.mages[player]['current_mana'] = self.mages[player]['max_mana']
        time.sleep(259200)

