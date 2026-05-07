from Data.repository import Repository
from Data.models import Dogodek, Prisotnost, Program, OcenaPesmi

class DogodekService:
    def __init__(self):
        self.repo = Repository()

    def seznam_dogodkov(self):
        result = self.repo.dobi_dogodke()
        return [Dogodek.schema().load(item) for item in result]

    def dobi_dogodek(self, id_dogodka: int):
        return self.repo.dobi_dogodek(id_dogodka)

    def dobi_prisotnost(self, id_dogodka: int = None):
        if id_dogodka is None:
            result = self.repo.dobi_prisotnost()
            return [Prisotnost.schema().load(item) for item in result]
        return self.repo.dobi_prisotnost_dogodka(id_dogodka)

    def dobi_program(self, id_dogodka: int = None):
        if id_dogodka is None:
            result = self.repo.dobi_program()
            return [Program.schema().load(item) for item in result]
        return self.repo.dobi_program_dogodka(id_dogodka)

    def dobi_ocene(self, id_pesmi: int = None):
        result = self.repo.dobi_ocene(id_pesmi)
        return [OcenaPesmi.schema().load(item) for item in result]

    def shrani_prisotnost(self, id_dogodka: int, id_osebe: int, prisotnost: bool):
        self.repo.shrani_prisotnost(id_dogodka, id_osebe, prisotnost)
