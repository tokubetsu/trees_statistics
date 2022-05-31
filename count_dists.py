import numpy as np
from scipy import special
import os
import json
from tqdm import tqdm
import pandas as pd
import warnings
warnings.filterwarnings('ignore')


class Element:
    dp_l = 20
    lg_l = 160

    def __init__(self, cur_dir, lg=40, dp=12):
        self.dp = dp
        self.lg = lg
        lst = os.listdir(cur_dir)
        for el in lst:
            name = el.split('.')[0]
            with open(f'{cur_dir}/{el}', encoding='utf-8') as f:
                if name == 'width_no':
                    pass
                elif name in ['sl_real', 'depth_pos']:
                    self.__update_zeros__(name.split('_')[0], json.load(f))
                elif name == 'width':
                    self.__update_ones__(name, json.load(f))
                else:
                    self.__update_size__(json.load(f))

    def __update_ones__(self, name, data):
        new = np.array(data)
        new = new[new < 1]
        setattr(self, name, data)
        setattr(self, f'{name}_no', new)

    def __update_zeros__(self, name, data):
        new = np.array(data)
        new = new[new > 0]
        setattr(self, name, data)
        setattr(self, f'{name}_no', new)

    def __update_size__(self, data):
        dct = {}
        dp = 0
        lg = 0
        for el in data:
            if el[1] not in dct:
                dct[el[1]] = {}
            if el[0] not in dct[el[1]]:
                dct[el[1]][el[0]] = 0
            dct[el[1]][el[0]] += 1
            if el[1] > lg:
                lg = el[1]
            if el[0] > dp:
                dp = el[0]
        for i in range(lg):
            if i not in dct:
                dct[i] = {}
            for j in range(dp):
                if j not in dct[i]:
                    dct[i][j] = 0
        df = pd.DataFrame(dct)
        df = df.reindex(sorted(df.columns), axis=1)
        df = df.reindex(sorted(df.index), axis=0)
        df = df.fillna(0)
        df = df.to_numpy()
        self.size = df[:self.dp_l, :self.lg_l].flatten()
        self.size_no = df[:self.dp, :self.lg].flatten()


class Metrics:
    def __init__(self, d1, d2, norm=True, bn=100):
        self.d1 = d1
        self.d2 = d2
        self.bn = bn
        if norm:
            self.__norm__()

    @staticmethod
    def __norm_one__(v, mn, mx, bn=100):
        v = np.histogram(v, bins=bn, range=(mn, mx), normed=None, weights=None, density=None)[0]
        s = sum(v)
        v = v / s
        return v

    def __norm__(self):
        mn = min([min(self.d1), min(self.d2)])
        mx = max([max(self.d1), max(self.d2)])
        self.d1 = self.__norm_one__(self.d1, mn, mx, self.bn)
        self.d2 = self.__norm_one__(self.d2, mn, mx, self.bn)

    def kl(self, line):
        kl1 = self.d1
        kl2 = self.d2
        kl1[kl1 <= line] = line
        kl2[kl2 <= line] = line
        kl = special.kl_div(kl1, kl2)
        return sum(kl)

    def mean(self):
        return np.mean(abs(self.d1 - self.d2))


def count_all(tp='foreign'):
    names = ['width', 'width_no', 'depth_pos', 'sl', 'sl_no', 'size', 'size_small']
    lines = [1e-10, 1e-30, 1e-30]
    cur_dir_path = f'stats/{tp}'
    langs = os.listdir(cur_dir_path)
    res = {}
    with tqdm(len(langs) ** 2) as pbar:
        for ref in langs:
            if ref not in res:
                res[ref] = {}
            ref_l = Element(f'{cur_dir_path}/{ref}')
            for lang in langs:
                if lang not in res[ref]:
                    res[ref][lang] = {}
                lang_l = Element(f'{cur_dir_path}/{lang}')
                for name in names:
                    if name not in res[ref][lang]:
                        res[ref][lang][name] = []
                    if 'sl' in name:
                        bn = 20
                    else:
                        bn = 100
                    metr = Metrics(getattr(ref_l, name), getattr(lang_l, name), bn=bn)
                    res[ref][lang][name].append(metr.mean())
                    for line in lines:
                        res[ref][lang][name].append(metr.kl(line=line))
                pbar.update(1)
    return res


def count_one_all(corpus, tp='foreign'):
    names = ['width', 'width_no', 'depth', 'depth_no', 'sl', 'sl_no', 'size', 'size_no']
    lines = [1e-10, 1e-30, 1e-30]
    cur_dir_path = f'stats_ref/{tp}/{corpus}'
    ref_el = Element(f'{cur_dir_path}/{corpus}')
    langs = os.listdir(cur_dir_path)
    res = {}
    for lang in tqdm(langs, total=len(langs)):
        if lang not in res:
            res[lang] = {}
        lang_el = Element(f'{cur_dir_path}/{lang}')
        for name in names:
            if name not in res[lang]:
                res[lang][name] = []
            if 'sl' in name:
                bn = 20
            else:
                bn = 100
            metr = Metrics(getattr(ref_el, name), getattr(lang_el, name), bn=bn)
            res[lang][name].append(metr.mean())
            for line in lines:
                res[lang][name].append(metr.kl(line=line))
    return res


def count_all_all(tp='foreign'):
    langs = os.listdir(f'stats_ref/{tp}')
    for lang in sorted(langs):
        print(lang)
        res = count_one_all(lang, tp=tp)
        with open(f'probs/{tp}/{lang}.json', 'w', encoding='utf-8') as f:
            json.dump(res, f)
        print('\n')


if __name__ == '__main__':
    count_all_all(tp='rus')
