# Tu definiramo razrede
# ZGLED:
#
# @dataclass_json
# @dataclass
# class razred:
#     atribut : tip = field(default="Neki tega tipa") #imena atributov naj bodo enaka imenom stolpcev, ker bo potem mapiranje enostavnejše
#
# a = razred(atribut="Neki tega tipa")

from dataclasses import dataclass, field
from dataclasses_json import dataclass_json

@dataclass_json
@dataclass
class Oseba:
    id_osebe: int = field(default=0)
    ime: str = field(default="")
    priimek: str = field(default="")
    datum_rojstva: str = field(default="")
    eposta: str = field(default="")
    telefonska_stevilka: str = field(default="")
    id_glasu: int = field(default=0)
    delitev_na_3: int = field(default=0)
    delitev_na_4: int = field(default=0)
    id_vloge: int = field(default=0)

@dataclass_json
@dataclass
class Dogodek:
    id_dogodka: int = field(default=0)
    datum: str = field(default="")
    vrsta_dogodka: str = field(default="")
    naziv_dogodka: str = field(default="")

@dataclass_json
@dataclass
class Vloga:
    id_vloge: int = field(default=0)
    naziv: str = field(default="")
    opis: str = field(default="")

@dataclass_json
@dataclass
class Glas:
    id_glasu: int = field(default=0)
    naziv_glasu: str = field(default="")

@dataclass_json
@dataclass
class Pesem:
    id_pesmi: int = field(default=0)
    naslov: str = field(default="")
    avtor: str = field(default="")
    note: str = field(default="")

@dataclass_json
@dataclass
class Kategorija:
    id_kategorije: int = field(default=0)
    naziv: str = field(default="")
    opis: str = field(default="")

@dataclass_json
@dataclass
class PesemKategorija:
    id_pesmi: int = field(default=0)
    id_kategorije: int = field(default=0)

@dataclass_json
@dataclass
class Prisotnost:
    id_dogodka: int = field(default=0)
    id_osebe: int = field(default=0)
    prisotnost: bool = field(default=False)

@dataclass_json
@dataclass
class Program:
    id_dogodka: int = field(default=0)
    id_pesmi: int = field(default=0)
    ocena: int = field(default=0)
    komentar: str = field(default="")

@dataclass_json
@dataclass
class OcenaPesmi:
    id_osebe: int = field(default=0)
    id_pesmi: int = field(default=0)
    ocena: int = field(default=0)
    komentar: str = field(default="")
