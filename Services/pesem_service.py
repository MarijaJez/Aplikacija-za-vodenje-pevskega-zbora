from Data.repository import Repository
from Data.models import Pesem, Kategorija, PesemKategorija, OcenaPesmi

class PesemService:
    def __init__(self):
        self.repo = Repository()

    def seznam_pesmi(self, kategorija_id: int = None):
        if kategorija_id is None:
            return self.repo.dobi_pesmi_z_kategorijami()
        return self.repo.dobi_pesmi_po_kategoriji(kategorija_id)

    def dobi_pesem(self, id_pesmi: int):
        return self.repo.dobi_pesem(id_pesmi)

    def seznam_kategorij(self):
        result = self.repo.dobi_kategorije()
        return [Kategorija.schema().load(item) for item in result]

    def seznam_ocen(self, id_pesmi: int = None):
        result = self.repo.dobi_ocene(id_pesmi)
        return [OcenaPesmi.schema().load(item) for item in result]

    def shrani_oceno(self, id_osebe: int, id_pesmi: int, ocena: int, komentar: str):
        self.repo.shrani_oceno_pesmi(id_osebe, id_pesmi, ocena, komentar)

    def seznam_pesem_kategorij(self):
        # Povezovalna tabela ni posebej podprta v repository, zato uporabimo kategorije in pesmi.
        result = self.repo.dobi_kategorije()
        return [Kategorija.schema().load(item) for item in result]
