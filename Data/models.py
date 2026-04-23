# Tu definiramo razrede

@dataclass_json
@dataclass
class razred:
    atribut : tip = field(default="Neki tega tipa") #imena atributov naj bodo enaka imenom stolpcev, ker bo potem mapiranje enostavnejše

a = razred(atribut="Neki tega tipa")