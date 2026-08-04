"""Application services and business rules for choir administration."""

from collections import Counter
from datetime import datetime
from decimal import Decimal

from Data.repository import ChoirRepository
from Services.auth_service import AuthService


MONTHS = {1:"jan.",2:"feb.",3:"mar.",4:"apr.",5:"maj",6:"jun.",7:"jul.",8:"avg.",9:"sep.",10:"okt.",11:"nov.",12:"dec."}
STATUS_KEYS = ["present", "late_under", "late_over", "excused", "absent"]


def date_label(value, include_year=True):
    if not value:
        return "Še ni izvedena"
    suffix = f" {value.year}" if include_year else ""
    return f"{value.day}. {MONTHS[value.month]}{suffix}"


class ChoirService:
    def __init__(self, repository: ChoirRepository | None = None):
        self.repository = repository or ChoirRepository()
        self.auth = AuthService(self.repository)

    @staticmethod
    def initials(first_name, last_name):
        return f"{first_name[:1]}{last_name[:1]}".upper()

    def members(self):
        result=[]
        for row in self.repository.list_members():
            result.append({**row,"name":f'{row["first_name"]} {row["last_name"]}',"initials":self.initials(row["first_name"],row["last_name"]),"birth":date_label(row["birth_date"]) if row["birth_date"] else "—"})
        return result

    def member(self, member_id):
        row=self.repository.get_member(member_id)
        if not row:return None
        attendance=[{**item,"title":item["name"],"kind":item["event_type"],"date":date_label(item["event_date"])} for item in self.repository.member_attendance(member_id)]
        return {**row,"name":f'{row["first_name"]} {row["last_name"]}',"initials":self.initials(row["first_name"],row["last_name"]),"birth":date_label(row["birth_date"]) if row["birth_date"] else "—","attendance_rows":attendance,"attendance_totals":{state:sum(item["status"]==state for item in attendance) for state in STATUS_KEYS}}

    def create_member(self, values, role_names):
        username=self.auth.next_username(values["first_name"],values["last_name"])
        person_id=self.repository.create_member(values,username,self.auth.hash_password(username),role_names)
        return person_id,username

    def songs(self):
        result=[]
        for row in self.repository.list_songs():
            result.append({**row,"added":date_label(row["created_at"]),"last":date_label(row["last_performed"]),"rating":float(row["rating"] or 0)})
        return result

    def song(self, song_id):
        row=self.repository.get_song(song_id)
        if not row:return None
        row["added"]=date_label(row["created_at"]);row["last"]=date_label(row["last_performed"]);row["rating"]=float(row["rating"] or 0)
        row["performances"]=[{**performance,"title":performance["name"],"kind":performance["event_type"],"date":date_label(performance["event_date"])} for performance in row["performances"]]
        return row

    def events(self):
        now=datetime.now().astimezone()
        result=[]
        for row in self.repository.list_events():
            value=row["event_date"]
            result.append({**row,"date":date_label(value),"time":value.strftime("%H:%M"),"kind":row["event_type"],"title":row["name"],"status":"upcoming" if value>=now else "past"})
        return sorted(result,key=lambda item:(item["status"]=="past",item["event_date"] if item["status"]=="upcoming" else -item["event_date"].timestamp()))

    def event(self, event_id):
        row=self.repository.get_event(event_id)
        if not row:return None
        value=row["event_date"]
        return {**row,"date":date_label(value),"time":value.strftime("%H:%M"),"kind":row["event_type"],"title":row["name"],"status":"upcoming" if value>=datetime.now().astimezone() else "past"}

    def roles(self):
        return self.repository.list_roles()

    @staticmethod
    def school_year_start(value):
        return value.year if value.month >= 9 else value.year - 1

    @staticmethod
    def event_group(event_type):
        lowered=event_type.lower()
        if "vaja" in lowered:return "Vaje"
        if "koncert" in lowered:return "Koncerti"
        return "Ostalo"

    def attendance(self, selected_year=None, selected_type="Vse"):
        members=self.members();all_events=self.events();records=self.repository.list_attendance()
        years=sorted({self.school_year_start(event["event_date"]) for event in all_events},reverse=True)
        current_start=self.school_year_start(datetime.now().astimezone())
        try: year_start=int(selected_year) if selected_year is not None else current_start
        except ValueError: year_start=current_start
        if years and year_start not in years: year_start=years[0]
        events=[event for event in all_events if self.school_year_start(event["event_date"])==year_start and (selected_type in (None,"","Vse") or self.event_group(event["event_type"])==selected_type)]
        lookup={(item["person_id"],item["event_id"]):item["status"] for item in records}
        matrix=[[lookup.get((member["id"],event["id"]),"absent") for event in events] for member in members]
        member_totals=[{state:row.count(state) for state in STATUS_KEYS} for row in matrix]
        event_totals=[{state:sum(row[col]==state for row in matrix) for state in STATUS_KEYS} for col in range(len(events))]
        total_records=max(len(members)*len(events),1); attended=sum(total[state] for total in member_totals for state in ("present","late_under","late_over")); voice_rates={voice:round(100*sum(sum(matrix[index][col] in ("present","late_under","late_over") for col in range(len(events))) for index,member in enumerate(members) if member["voice"]==voice)/max(sum(member["voice"]==voice for member in members)*len(events),1)) for voice in {member["voice"] for member in members}}
        return {"members":members,"events":events,"status_keys":STATUS_KEYS,"matrix":matrix,"member_totals":member_totals,"event_totals":event_totals,"average":round(100*attended/total_records),"event_count":len(events),"best_voice":max(voice_rates,key=voice_rates.get) if voice_rates else "—","best_voice_rate":max(voice_rates.values()) if voice_rates else 0,"school_years":[{"start":year,"label":f"{year}/{str(year+1)[-2:]}"} for year in years],"selected_year":year_start,"selected_type":selected_type or "Vse",
          "chart_data":{"labels":[event["date"].replace(" 2026","") for event in events],"voices":[member["voice"] for member in members],"matrix":matrix,"statuses":STATUS_KEYS}}

    def treasury(self):
        rows=[]
        for row in self.repository.list_transactions():
            rows.append({"id":row["id"],"date":date_label(row["transaction_date"]),"raw_date":row["transaction_date"],"description":row["description"],"person":row["person_name"],"kind":row["kind"],"amount":float(row["amount"]),"settled":row["settled"]})
        income=sum(item["amount"] for item in rows if item["kind"]=="Prihodek");expenses=sum(item["amount"] for item in rows if item["kind"]=="Odhodek")
        return {"transactions":rows,"income":income,"expenses":expenses,"balance":income-expenses,"unsettled":sum(item["amount"] for item in rows if not item["settled"])}

    def dashboard(self):
        members=self.members();songs=self.songs();events=self.events();voices=Counter(member["voice"] for member in members);ranked=sorted(members,key=lambda item:item["attendance"],reverse=True)
        return {"member_count":len(members),"voices":dict(voices),"top_members":ranked[:3],"low_members":list(reversed(ranked[-3:])),"song_count":len(songs),"latest_songs":songs[:3],"forgotten_songs":sorted(songs,key=lambda item:item["last"] or "")[:3],"events":events,"attendance":ranked,"upcoming_count":sum(event["status"]=="upcoming" for event in events),"average_attendance":round(sum(member["attendance"] for member in members)/max(len(members),1))}
