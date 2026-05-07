from Data.repository import Repository
from Data.models import Oseba, Vloga, Glas

class OsebaService:
    def __init__(self):
        self.repo = Repository()

    def seznam_oseb(self):
        return self.repo.dobi_osebe_razsirjeno()

    def dobi_osebo(self, id_osebe: int):
        result = self.repo.dobi_osebo(id_osebe)
        return Oseba.schema().load(result) if result else None

    def seznam_vlog(self):
        result = self.repo.dobi_vloge()
        return [Vloga.schema().load(item) for item in result]

    def seznam_glasov(self):
        result = self.repo.dobi_glasove()
        return [Glas.schema().load(item) for item in result]

    def shrani_osebo(self, oseba_data: dict):
        return self.repo.shrani_osebo(oseba_data)

    def posodobi_osebo(self, id_osebe: int, oseba_data: dict):
        self.repo.posodobi_osebo(id_osebe, oseba_data)
