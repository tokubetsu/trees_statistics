from dataclasses import dataclass


@dataclass(frozen=True)
class Feat:
    name: str = None
    value: str = None


@dataclass(frozen=True)
class Cell:  # ячейка
    pos: str = None
    feats: frozenset = None

    def to_dict(self):  # превращение в словарь для сохранения в json
        dc = {'pos': self.pos, 'feats': None}
        if self.feats:
            dc['feats'] = {i.name: i.value for i in self.feats}
        return dc
