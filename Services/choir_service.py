"""Application services and business rules for choir administration."""

from collections import Counter
from datetime import datetime
from decimal import Decimal

from email_validator import EmailNotValidError, validate_email

from Data.repository import ChoirRepository
from Services.auth_service import AuthService


MONTHS = {1:"jan.",2:"feb.",3:"mar.",4:"apr.",5:"maj",6:"jun.",7:"jul.",8:"avg.",9:"sep.",10:"okt.",11:"nov.",12:"dec."}
STATUS_KEYS = ["present", "late_under", "late_over", "excused", "absent", "unentered"]


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
        now=datetime.now().astimezone()
        attendance=[{**item,"title":item["name"],"kind":item["event_type"],"date":date_label(item["event_date"])} for item in self.repository.member_attendance(member_id)]
        attendance.sort(key=lambda item:self.event_order(item, now))
        return {**row,"name":f'{row["first_name"]} {row["last_name"]}',"initials":self.initials(row["first_name"],row["last_name"]),"birth":date_label(row["birth_date"]) if row["birth_date"] else "—","attendance_rows":attendance,"attendance_totals":{state:sum(item["status"]==state and item["event_date"] < now for item in attendance) for state in STATUS_KEYS}}

    def create_member(self, values, role_names):
        values=self.validate_member(values)
        username=self.auth.next_username(values["first_name"],values["last_name"])
        password_hash=self.auth.hash_password(self.auth.generated_password())
        person_id=self.repository.create_member(values,username,password_hash,role_names,must_change_password=False)
        return person_id,username

    @staticmethod
    def validate_member(values):
        cleaned={key:(value.strip() if isinstance(value,str) else value) for key,value in values.items()}
        if not cleaned.get("first_name") or not cleaned.get("last_name"):
            raise ValueError("Ime in priimek sta obvezna.")
        if cleaned.get("voice") not in {"Sopran","Alt","Tenor","Bas"}:
            raise ValueError("Izberi veljaven glas.")
        try:
            cleaned["email"]=validate_email(cleaned.get("email", ""),check_deliverability=False).normalized.lower()
        except EmailNotValidError as error:
            raise ValueError("Vnesi veljaven e-poštni naslov.") from error
        return cleaned

    def update_member(self, member_id, values):
        self.repository.update_member(member_id,self.validate_member(values))

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

    @staticmethod
    def validate_event(values) -> None:
        try:
            start = datetime.fromisoformat(values["event_date"])
            end = datetime.fromisoformat(values["event_end"])
            valid = end > start
        except (ValueError, TypeError, KeyError):
            valid = False
        if not valid:
            raise ValueError("Konec dogodka mora biti po začetku. Vnesi veljaven datum in uro začetka ter konca.")

    @staticmethod
    def event_time(row):
        start = row["event_date"]
        end = row.get("event_end")
        return start.strftime("%H:%M") + ("–" + end.strftime("%H:%M" if end.date() == start.date() else "%d. %m. %Y %H:%M") if end else "")

    @staticmethod
    def event_order(item, now):
        value=item["event_date"]
        return (value < now, value.timestamp() if value >= now else -value.timestamp())

    def events(self):
        now=datetime.now().astimezone()
        result=[]
        for row in self.repository.list_events():
            value=row["event_date"]
            result.append({**row,"date":date_label(value),"time":self.event_time(row),"kind":row["event_type"],"title":row["name"],"status":"upcoming" if value>=now else "past"})
        return sorted(result,key=lambda item:self.event_order(item, now))

    def event(self, event_id):
        row=self.repository.get_event(event_id)
        if not row:return None
        value=row["event_date"]
        return {**row,"date":date_label(value),"time":self.event_time(row),"kind":row["event_type"],"title":row["name"],"status":"upcoming" if value>=datetime.now().astimezone() else "past"}

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
        now=datetime.now().astimezone()
        events=[{**event,"counts_statistics":event["event_date"] < now} for event in events]
        past_cols=[col for col,event in enumerate(events) if event["counts_statistics"]]
        lookup={(item["person_id"],item["event_id"]):item["status"] for item in records}
        matrix=[[lookup.get((member["id"],event["id"]),"unentered") for event in events] for member in members]
        statistics_matrix=[[row[col] for col in past_cols] for row in matrix]
        member_totals=[{state:row.count(state) for state in STATUS_KEYS} for row in statistics_matrix]
        event_totals=[{state:sum(row[col]==state for row in matrix) if col in past_cols else 0 for state in STATUS_KEYS} for col in range(len(events))]
        entered_count=sum(state != "unentered" for row in statistics_matrix for state in row)
        attended=sum(total[state] for total in member_totals for state in ("present","late_under","late_over"))
        voice_rates={}
        for voice in sorted({member["voice"] for member in members}):
            states=[state for index,member in enumerate(members) if member["voice"]==voice for state in statistics_matrix[index] if state != "unentered"]
            if states:
                voice_rates[voice]=round(100*sum(state in ("present","late_under","late_over") for state in states)/len(states))
        return {"members":members,"events":events,"status_keys":STATUS_KEYS,"matrix":matrix,"member_totals":member_totals,"event_totals":event_totals,"average":round(100*attended/entered_count) if entered_count else None,"event_count":len(past_cols),"best_voice":max(voice_rates,key=voice_rates.get) if voice_rates else "—","best_voice_rate":max(voice_rates.values()) if voice_rates else 0,"school_years":[{"start":year,"label":f"{year}/{str(year+1)[-2:]}"} for year in years],"selected_year":year_start,"selected_type":selected_type or "Vse",
          "chart_data":{"columns":past_cols,"labels":[events[col]["date"].replace(" 2026","") for col in past_cols],"voices":[member["voice"] for member in members],"matrix":statistics_matrix,"statuses":STATUS_KEYS}}

    def treasury(self):
        rows=[]
        for row in self.repository.list_transactions():
            rows.append({"id":row["id"],"date":date_label(row["transaction_date"]),"raw_date":row["transaction_date"],"description":row["description"],"person":row["person_name"],"kind":row["kind"],"amount":float(row["amount"]),"settled":row["settled"]})
        income=sum(item["amount"] for item in rows if item["kind"]=="Prihodek");expenses=sum(item["amount"] for item in rows if item["kind"]=="Odhodek")
        return {"transactions":rows,"income":income,"expenses":expenses,"balance":income-expenses,"unsettled":sum(item["amount"] for item in rows if not item["settled"])}

    def dashboard(self, user):
        members=self.members();songs=self.songs();events=self.events();voices=Counter(member["voice"] for member in members);ranked=sorted((member for member in members if member["attendance"] is not None),key=lambda item:item["attendance"],reverse=True)
        upcoming = [event for event in events if event["status"] == "upcoming"]
        personal_member = self.member(user["person_id"])
        next_event = self.event(upcoming[0]["id"]) if upcoming else None
        treasury = self.treasury() if "Blagajnik" in user["roles"] else None
        return {"personal_member":personal_member,"next_event":next_event,"treasury":treasury,"member_count":len(members),"voices":[{"voice":voice,"count":count} for voice,count in voices.items()],"top_members":ranked[:3],"low_members":list(reversed(ranked[-3:])),"song_count":len(songs),"latest_songs":songs[:3],"forgotten_songs":sorted(songs,key=lambda item:item["last"] or "")[:3],"events":upcoming[:5],"attendance":ranked,"upcoming_count":sum(event["status"]=="upcoming" for event in events),"average_attendance":round(sum(member["attendance"] for member in members if member["attendance"] is not None)/max(sum(member["attendance"] is not None for member in members),1)) if any(member["attendance"] is not None for member in members) else None}
