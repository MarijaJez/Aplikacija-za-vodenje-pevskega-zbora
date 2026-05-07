from Data.repository import Repository
from Data.models import Vloga, Glas

class AuthService:
    def __init__(self):
        self.repo = Repository()

    def seznam_vlog(self):
        result = self.repo.dobi_vloge()
        return [Vloga.schema().load(item) for item in result]

    def seznam_glasov(self):
        result = self.repo.dobi_glasove()
        return [Glas.schema().load(item) for item in result]

    def check_role(self, id_vloge: int, allowed_roles: list[int]):
        return id_vloge in allowed_roles
