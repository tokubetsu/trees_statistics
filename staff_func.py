# import conllu
from staff_classes import Cell, Feat
from random import randint
import json


data_dir = 'data/'
res_dir = 'results/'


def parse_conllu(text):
    """
    Разбор conllu
    :param text: список с предложениями в формате conllu
    :return: list
    """
    info = conllu.parse(text)
    return info


def make_cell(item):
    """
    Создает ячейки из элемента conllu
    :param item: элемент, распарсенный из conllu
    :return: Cell
    """
    if item is not None:
        if 'upos' not in item:
            pos = item['pos']
        else:
            pos = item['upos']
        if item['feats']:
            feats = frozenset([Feat(name, item['feats'][name]) for name in sorted(item['feats'].keys())])
        else:
            feats = None
        res = Cell(pos, feats)
    else:
        res = Cell()
    return res


def save_json(filename, tree, cur_dir=data_dir, lst=False, mode='a'):
    """
    Сохраняет данные в формате jsonl
    :param filename: имя файла
    :param tree: список или элемент, который возможно сохранить в json
    :param cur_dir: текущая папка
    :param lst: список или одиночный элемент
    :param mode: тип открытия файла
    :return: None
    """
    with open(cur_dir + filename, mode, encoding='utf-8') as f:
        if lst:
            for el in tree:
                s = json.dumps(el)
                f.write(s + '\n')
        else:
            s = json.dumps(tree)
            f.write(s + '\n')


def file_read(filename):
    """
    Читает файл
    :param filename: имя файла
    :return: str
    """
    with open(filename, encoding='utf-8') as f:
        text = f.read()
    return text


def read_json(name, lst=False, cur_dir=data_dir, line=60000):
    """
    Читает данные в формате json из папки с датой
    :return: list
    """
    res = []
    if lst:
        with open(cur_dir + name, encoding='utf-8') as f:
            data = f.read().splitlines()
        for el in data[:line]:
            res.append(json.loads(el))
    else:
        for el in name:
            s = cur_dir + el
            if not s.endswith('.json'):
                s += '.json'
            with open(s, 'r', encoding='utf-8') as f:
                res.append(json.load(f))
    return res


def get_tree(sent, cur=0, cur_el=None, get_num=False):
    """
    Получает дерево в польской записи из conllu формата
    :param sent: предложение в conllu
    :param cur: номер текущей вершины
    :param cur_el: значение текущей вершины
    :param get_num: нужно ли сохранять позиции в деревьях
    :return: list
    """
    tree = []

    if cur == 0:  # если это первый элемент в предлодении, то превращаем предложение в формат {head: dependents}
        new_sent = {}
        for i in sent:
            if (i['head'] is not None) and (i['upos'] not in ['_', 'PUNCT']):
                if i['head'] not in new_sent:
                    new_sent[i['head']] = []
                new_sent[i['head']].append(i)
        sent = new_sent

    if get_num:  # разное сохранение в зависимости от параметра
        tree.append((make_cell(cur_el), cur))
    else:
        tree.append(make_cell(cur_el))

    cur_child = sent.get(cur, [])
    for el in cur_child:  # для каждого элемента из потомков выполняем функцию рекурсивно
        connect = el['deprel']
        new_tree = get_tree(sent, el['id'], el, get_num=get_num)
        tree.append([connect, new_tree])
    return tree


def count_sum(lst):
    """
    Считает сумму частот на уровне для выбора случайного элемента
    :param lst: список элементов, где каждый имеет вид (элемент, частота)
    :return: int
    """
    s = 0
    for el in lst:
        s += el[1]
    return s


def find_sum(lst, n):
    """
    Ищет в упорядоченном списке элемент, чья частота первой делает сумму частот эелментов больше n
    :param lst: упорядоченный список
    :param n: сумма
    :return: tuple
    """
    cur = 0
    for el in lst:
        cur += el[1]
        if cur >= n:
            return el


def get_random(lst, prep=True, first=False, child=False, three_id=None):
    """
    Выбирает случайный элемент из списка, исходя из частот
    :param lst: список или словарь с элементами
    :param prep: является ли список предобработанным специльно для функции
    :param first: нужны ли только первые эелемнты цепочек
    :param child: тип хранения частот ('-1' или по ключу элемента)
    :param three_id: список с кодировками троек
    :return: tuple
    """
    if not prep:
        if first:
            lst = [(key, lst[key]['-1']) for key in lst if key != '-1' and three_id[int(key)][0] is None]
        else:
            if child:
                lst = [(key, lst[key]) for key in lst if key != '-1']
            else:
                lst = [(key, lst[key]['-1']) for key in lst if key != '-1']

    lst = sorted(lst, key=lambda x: x[1], reverse=True)

    s = count_sum(lst)
    n = randint(0, s)
    el = find_sum(lst, n)
    return el
