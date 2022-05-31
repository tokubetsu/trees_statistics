from staff_func import *
from collections import Counter
import os
import json
import warnings
warnings.filterwarnings('ignore')


def get_prob(start, matrix, dep):
    if str(dep) not in matrix:
        return False
    cur = matrix[str(dep)]
    prob = 1
    for el in start:
        if str(el) in cur:
            prob *= cur[str(el)] / cur['BOS']
        else:
            prob = 0
    return prob


def get_prob_tree(tree, deprel, matrix, probs=None, begin=True):
    if not probs:
        probs = []
    if begin:
        if len(tree) > 1:
            probs = get_prob_tree(tree[1][1], deprel, matrix, probs, begin=False)
    else:
        cur = [deprel.get(el[0]) for el in tree[1:] if el[0] in deprel]
        prev = ['BOS', *cur]
        if len(prev) > 1:
            prob = get_prob(prev[:-1], matrix, prev[-1])
            if prob is not False:
                probs.append(prob)
            for el in tree[1:]:
                if el != 'root':
                    probs = get_prob_tree(el[1], deprel, matrix, probs, begin=False)
    return probs


def get_width(data, matrix, deprel):
    probs = []
    deprel = {dep: i for i, dep in enumerate(deprel)}
    for sent in data:
        probs = get_prob_tree(sent, deprel, matrix, probs)
    return probs


def get_edge_prob(freq, node, head=None, deprel=None, deprel_c=None, child=None):
    if not head:
        if node != -1:
            return freq[node] / sum(freq.values())
    else:
        if -1 not in (head, deprel, node, deprel_c, child):
            cur_d = freq[head][deprel][node][deprel_c]['-1']
            sum_d = sum([freq[head][deprel][node][el]['-1'] for el in freq[head][deprel][node] if el != '-1'])
            cur_c = freq[head][deprel][node][deprel_c][child]
            sum_c = sum([freq[head][deprel][node][deprel_c][el] for el in freq[head][deprel][node][deprel_c] if el != '-1'])
            return cur_d / sum_d * cur_c / sum_c
    return 0


def get_probs_depth_pos(tree, cell_vers, deprel_vers, three_vers, three_dep_vers,
                        roots, freq, head=None, deprel=None, node=None,
                        vers=1, verses=None):
    if not verses:
        verses = []
    if (not head) and (len(tree) > 1):
        head = three_vers.get((None, None, None), -1)
        deprel = three_dep_vers.get((None, deprel_vers.get(tree[1][0], -1), None), -1)
        tree = tree[1][1]
        node = three_vers.get((None, cell_vers.get(tree[0]['pos'], -1), None), -1)
        try:
            vers *= get_edge_prob(roots, node)
        except KeyError:
            vers = 0
    elif (not head) and (len(tree) <= 1):
        return verses

    if len(tree) > 1:
        lvl = [(None, None)]
        lvl.extend([(deprel_vers.get(el[0], -1), cell_vers.get(el[1][0]['pos'], -1)) for el in tree[1:]])
        lvl.append((None, None))
        for i in range(1, len(lvl) - 1):
            deprel_c = three_dep_vers.get((lvl[i - 1][0], lvl[i][0], lvl[i + 1][0]), -1)
            child = three_vers.get((lvl[i - 1][1], lvl[i][1], lvl[i + 1][1]), -1)
            try:
                vers_new = vers * get_edge_prob(freq, node, head, deprel, deprel_c, child)
            except KeyError:
                vers_new = 0
            verses = get_probs_depth_pos(tree[i][1], cell_vers, deprel_vers,
                                         three_vers, three_dep_vers, roots,
                                         freq, node, deprel_c, child,
                                         vers_new, verses)
    else:
        verses.append(vers)
    return verses


def get_depth_pos(trees, cell_vers, deprel_vers, three_vers, three_dep_vers, roots, freq):
    total = []
    for i, el in enumerate(trees):
        total.extend(get_probs_depth_pos(el, cell_vers, deprel_vers, three_vers,
                                         three_dep_vers, roots, freq))
    return total


def get_probs_depth(tree, cell_vers, deprel_vers, three_vers, roots, freq,
                    head=None, deprel=None, node=None, vers=1, verses=None):
    if not verses:
        verses = []

    if (not head) and (len(tree) > 1):
        head = three_vers.get((None, cell_vers.get(make_cell(tree[0]), -1), None), -1)
        deprel = three_vers.get((None, deprel_vers.get(tree[1][0], -1), None), -1)
        tree = tree[1][1]
        node = three_vers.get((None, cell_vers.get(make_cell(tree[0]), -1), None), -1)

        try:
            vers *= get_edge_prob(roots, node)
        except KeyError:
            vers = 0

    elif (not head) and (len(tree) <= 1):
        return verses

    if len(tree) > 1:

        lvl = [(None, None)]
        lvl.extend([(deprel_vers.get(el[0], -1), cell_vers.get(make_cell(el[1][0]), -1)) for el in tree[1:]])

        lvl.append((None, None))

        for i in range(1, len(lvl) - 1):
            deprel_c = three_vers.get((lvl[i - 1][0], lvl[i][0], lvl[i + 1][0]), -1)
            child = three_vers.get((lvl[i - 1][1], lvl[i][1], lvl[i + 1][1]), -1)
            try:
                vers_new = vers * get_edge_prob(freq, node, head, deprel, deprel_c, child)
            except KeyError:
                vers_new = 0

            verses = get_probs_depth(tree[i][1], cell_vers, deprel_vers, three_vers,
                                     roots, freq, head=node, deprel=deprel_c, node=child,
                        vers=vers, verses=verses)
    else:
        verses.append(vers)
    return verses


def get_depth(trees, cell_vers, deprel_vers, three_vers, roots, freq):
    total = []
    c = 0
    for i, el in enumerate(trees):
        try:
            new = get_probs_depth(el, cell_vers, deprel_vers, three_vers, roots,
                                  freq)
            total.extend(new)
        except Exception:
            c += 1
    return total


def get_edge_prob_new(freq, deprel, deprel_c):
    if -1 not in (deprel, deprel_c):
        cur = freq[deprel]
        sum_cur = sum(cur.values())
        return cur[deprel_c] / sum_cur
    return 0


def get_probs_depth_new(tree, deprel_vers, three_vers, dep_freq, deprel=None, vers=1,
                    verses=None):
    if not verses:
        verses = []

    if (not deprel) and (len(tree) > 1):
        deprel = three_vers.get((None, deprel_vers.get(tree[1][0], -1), None), -1)
        tree = tree[1][1]
    elif (not deprel) and (len(tree) <= 1):
        return verses

    if len(tree) > 1:

        lvl = [None, ]

        lvl.extend([deprel_vers.get(el[0], -1) for el in tree[1:]])
        lvl.append(None)

        for i in range(1, len(lvl) - 1):
            deprel_c = three_vers.get((lvl[i - 1][0], lvl[i][0], lvl[i + 1][0]), -1)
            try:
                vers_new = vers * get_edge_prob_new(dep_freq, deprel, deprel_c)
            except KeyError:
                vers_new = 0

            verses = get_probs_depth_new(tree[i][1], deprel_vers, three_vers, dep_freq,
                        deprel=deprel_c, vers=vers, verses=verses)
    else:
        verses.append(vers)
    return verses


def get_depth_new(trees, deprel_vers, three_vers, dep_freq):
    total = []
    c = 0
    for i, el in enumerate(trees):
        try:
            new = get_probs_depth_new(el, deprel_vers, three_vers, dep_freq)
            total.extend(new)
        except Exception:
            c += 1
    return total


def get_depth_length(tree, amount=0):
    amount += 1
    depth = 0
    for el in tree[1:]:
        new_depth, amount = get_depth_length(el[1], amount)
        if new_depth > depth:
            depth = new_depth
    return depth + 1, amount


def get_size(trees):
    pairs = []
    for el in trees:
        depth, amount = get_depth_length(el)
        pairs.append((depth, amount))
    return pairs


def get_seq_length(tree, length=None):
    if not length:
        length = []
    length.append(len(tree) - 1)
    for el in tree[1:]:
        length = get_seq_length(el[1], length)
    return length


def get_length(trees):
    lengths = []
    for tree in trees:
        lengths = get_seq_length(tree, lengths)
    return lengths


class ReferenceData:
    def __init__(self, cur_dir):
        names = ['matrix', 'freq', 'roots', 'deprel_freq', 'cell', 'deprel',
                 'three', 'new_freq', 'new_cell', 'new_three', 'new_roots']
        for name in names:
            with open(f'{cur_dir}/{name}.json', encoding='utf-8') as f:
                setattr(self, name, json.load(f))
        self.cell_vers = {make_cell(el): i for i, el in enumerate(self.cell)}
        self.deprel_vers = {el: i for i, el in enumerate(self.deprel)}
        self.three_vers = {tuple(el): str(i) for i, el in enumerate(self.three)}
        self.new_cell_vers = {el: i for i, el in enumerate(self.new_cell)}
        self.new_three_vers = {tuple(el): str(i) for i, el in enumerate(self.new_three)}


class ReferenceMetrics:
    def __init__(self, ref, trees):
        self.width = get_width(trees, ref.matrix, ref.deprel)
        # self.depth = get_depth(trees, ref.cell_vers,
        #                            ref.deprel_vers, ref.three_vers,
        #                         ref.roots, ref.freq)
        # self.depth_new = get_depth_new(trees, ref.deprel_vers, ref.three_vers,
        #                         ref.deprel_freq)
        self.depth_pos = get_depth_pos(trees, ref.new_cell_vers,
                                   ref.deprel_vers, ref.new_three_vers, ref.three_vers,
                                   ref.new_roots, ref.new_freq)
        self.size = get_size(trees)
        self.sl_real = get_length(trees)
        del trees

    def add(self, other):
        self.width.extend(other.width)
        # self.depth.extend(other.depth)
        # self.depth_new.extend(other.depth_new)
        self.depth_pos.extend(other.depth_pos)
        self.size.extend(other.size)
        self.sl_real.extend(other.sl_real)

    def save(self, cur_dir):
        # names = ['width', 'depth', 'depth_new', 'depth_pos', 'size', 'sl_real']
        names = ['width', 'depth_pos', 'size', 'sl_real']
        try:
            os.mkdir(cur_dir)
        except FileExistsError:
            pass
        for name in names:
            filename = f'{cur_dir}/{name}.json'
            data = getattr(self, name)
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f)


def count_all(tp='foreign'):
    lst_files = os.listdir(f'trees_data/{tp}')
    # for lang_file in tqdm(lst_files, total=len(lst_files)):
    for lang_file in lst_files:
        lang = lang_file.split('.')[0]
        d_dir = f'data/{tp}/{lang}'
        r_dir = f'trees_data/{tp}/{lang_file}'
        ref_data = ReferenceData(d_dir)
        with open(r_dir, encoding='utf-8') as f:
            cur_data = json.load(f)
        ref_metr = ReferenceMetrics(ref_data, cur_data)
        print(lang, Counter(ref_metr.depth_pos).most_common(10), end='\n\n', sep='\n')
        cur_dir = f'stats/{tp}/{lang}'
        ref_metr.save(cur_dir)


def count_one(corpus, tp='foreign'):
    lst_files = os.listdir(f'data/{tp}')
    cur_dir = f'trees_data/{tp}/{corpus}.json'
    if corpus != 'German_HDT':
        with open(cur_dir, encoding='utf-8') as f:
            cur_data = json.load(f)
        for ref_lang in lst_files:
            d_dir = f'data/{tp}/{ref_lang}'
            ref_data = ReferenceData(d_dir)
            ref_metr = ReferenceMetrics(ref_data, cur_data)
            print(ref_lang, Counter(ref_metr.depth_pos).most_common(5), end='\n\n', sep='\n')
            r_dir = f'stats_ref/{tp}/{ref_lang}/{corpus}'
            try:
                os.mkdir(f'stats_ref/{tp}/{ref_lang}')
            except FileExistsError:
                pass
            finally:
                try:
                    os.mkdir(f'stats_ref/{tp}/{ref_lang}/{corpus}')
                except FileExistsError:
                    pass
            ref_metr.save(r_dir)


def count_all_all(tp='foreign'):
    lst_files = sorted(os.listdir(f'data/{tp}'))
    for corpus in lst_files:
        print(corpus, '*'*100, sep='\n')
        count_one(corpus, tp=tp)
        print('\n\n')


if __name__ == '__main__':
    count_all_all(tp='rus')

# Chech_PDT, German_HDT, Russian_SynTagRus
