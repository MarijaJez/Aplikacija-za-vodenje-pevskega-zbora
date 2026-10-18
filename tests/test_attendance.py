import io
import json
import os
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import Mock, patch
from bottle import template

with patch.dict(os.environ, {'COOKIE_SECRET':'attendance-test-only'}), patch('Data.repository.Database'):
    import Presentation.app as web
from Services.choir_service import ChoirService
from Services.push_notifications import PushNotificationService
from tests.test_push_notifications import FakeDatabase

VIEWS = str(Path(__file__).resolve().parents[1] / 'Presentation' / 'views')

class AttendanceTests(unittest.TestCase):
    def setUp(self):
        self.user = dict(id=4, person_id=7, roles=['Član'], must_change_password=False)
        self.event = dict(id=2, event_date=datetime.now(timezone.utc)+timedelta(days=1))

    def call(self, payload, user=None, event=None, origin=None):
        body=json.dumps(payload).encode()
        env={'REQUEST_METHOD':'POST','PATH_INFO':'/api/prisotnost','SERVER_NAME':'localhost','SERVER_PORT':'80','SERVER_PROTOCOL':'HTTP/1.1','wsgi.url_scheme':'http','wsgi.input':io.BytesIO(body),'wsgi.errors':io.StringIO(),'wsgi.version':(1,0),'wsgi.multithread':False,'wsgi.multiprocess':False,'wsgi.run_once':False,'CONTENT_TYPE':'application/json','CONTENT_LENGTH':str(len(body))}
        if origin:env['HTTP_ORIGIN']=origin
        result={}
        def start(status,headers,exc_info=None):result['status']=int(status.split()[0])
        with patch.object(web,'current_user',return_value=self.user if user is None else user), patch.object(web,'repository') as repo:
            repo.get_event.return_value=self.event if event is None else event
            repo.get_member.return_value={'id':7}
            output=b''.join(web.app(env,start))
            return result['status'],repo.upsert_attendance.call_args,output

    def test_server_self_future_and_denials(self):
        self.assertEqual(self.call({'event_id':2,'status':'present'})[0],200)
        status,args,_=self.call({'event_id':2,'status':'absent'})
        self.assertEqual(args.args,(2,7,'absent',4))
        self.assertEqual(self.call({'event_id':2,'person_id':8,'status':'present'})[0],403)
        past=dict(self.event,event_date=datetime.now(timezone.utc)-timedelta(days=1))
        self.assertEqual(self.call({'event_id':2,'status':'present'},event=past)[0],403)
        for role in ['Predsednik','Zborovodja','Beleženje prisotnosti']:
            with self.subTest(role=role):
                self.assertEqual(self.call({'event_id':2,'person_id':8,'status':'absent'},user=dict(self.user,roles=[role]),event=past)[0],200)
        for role in ['Notar','Blagajnik']:
            self.assertEqual(self.call({'event_id':2,'person_id':8,'status':'present'},user=dict(self.user,roles=[role]))[0],403)

    def test_login_and_cross_origin_required(self):
        self.assertEqual(self.call({'event_id':2,'status':'present'},user=False)[0],303)
        self.assertEqual(self.call({'event_id':2,'status':'present'},origin='https://evil.invalid')[0],403)

    def test_invalid_payload_and_missing_event(self):
        for payload in [[], {'event_id':'bad','status':'present'}, {'status':'present'}, {'event_id':2,'status':'unentered'}]:
            self.assertEqual(self.call(payload)[0],400)
        self.assertEqual(self.call({'event_id':2,'status':'present'},event=False)[0],404)

    def test_unentered_matrix_totals_statistics_and_template(self):
        service=ChoirService(Mock())
        members=[dict(id=i,name=f'Član {i}',initials='Č',voice='Alt') for i in (7,8)]
        events=[dict(self.event, event_date=datetime.now(timezone.utc)-timedelta(days=1), status='past',title='Vaja',date='1. jan. 2030',event_type='Vaja')]
        service.members=Mock(return_value=members);service.events=Mock(return_value=events)
        service.repository.list_attendance.return_value=[dict(person_id=7,event_id=2,status='present')]
        data=service.attendance(service.school_year_start(self.event['event_date']))
        self.assertEqual(data['matrix'],[['present'],['unentered']])
        self.assertEqual(data['event_totals'][0]['absent'],0)
        self.assertEqual(data['event_totals'][0]['unentered'],1)
        self.assertEqual(data['average'],100)
        html=template('attendance.tpl',template_lookup=[VIEWS],data=data,json=json,current_user=self.user,can_edit_attendance=web.can_edit_attendance,avatar=web.avatar)
        self.assertIn('Še ni vneseno',html)
        self.assertIn('data-person-id="8"',html)
        self.assertIn('disabled',html)
        service.repository.list_attendance.return_value=[]
        self.assertIsNone(service.attendance()['average'])

    def test_future_answers_do_not_change_statistics(self):
        service=ChoirService(Mock())
        service.members=Mock(return_value=[dict(id=7,voice='Alt')])
        now=datetime.now(timezone.utc)
        service.events=Mock(return_value=[dict(id=1,event_date=now+timedelta(minutes=10),event_type='Vaja',date='Prihodnji'),dict(id=2,event_date=now-timedelta(minutes=10),event_type='Vaja',date='Pretekli')])
        service.repository.list_attendance.return_value=[dict(person_id=7,event_id=1,status='present'),dict(person_id=7,event_id=2,status='absent')]
        data=service.attendance(service.school_year_start(now))
        self.assertEqual(data['matrix'],[['present','absent']])
        self.assertEqual(data['average'],0)
        self.assertEqual(data['member_totals'][0]['present'],0)
        self.assertEqual(data['member_totals'][0]['absent'],1)
        self.assertEqual(data['event_count'],1)
        self.assertEqual(data['chart_data']['columns'],[1])
        self.assertEqual(data['chart_data']['matrix'],[['absent']])
        service.events.return_value=service.events.return_value[:1]
        data=service.attendance(service.school_year_start(now))
        self.assertIsNone(data['average'])
        self.assertEqual(data['event_count'],0)
        self.assertEqual(data['chart_data']['labels'],[])

    def test_event_template_offers_own_choices_only_when_allowed(self):
        event=dict(self.event,program=[],songs=0,status='upcoming',date='1. jan. 2030',event_type='Vaja',name='Vaja',kind='Vaja',title='Vaja',time='18:00',place='Dom')
        for past in [False,True]:
            if past:event['event_date']=datetime.now(timezone.utc)-timedelta(days=1)
            html=template('event_detail.tpl',template_lookup=[VIEWS],event=event,json=json,current_user=self.user,can_edit_attendance=web.can_edit_attendance,own_attendance='unentered',permissions={'self'},conductor=False,songs=[],categories=[],event_types=[],members=[])
            self.assertEqual('data-own-attendance-choice="present"' in html,not past)
            self.assertIn('Še ni vneseno',html)

    def test_push_choices_are_personalized_without_delivery(self):
        rows=[dict(endpoint='https://fcm.googleapis.com/a',p256dh='x',auth='y',attendance_status=None,event_date=self.event['event_date']),dict(endpoint='https://fcm.googleapis.com/b',p256dh='x',auth='y',attendance_status='absent',event_date=self.event['event_date'])]
        push=PushNotificationService(type('Repo',(),{'db':FakeDatabase(rows)})())
        push.private_key_file=__file__
        with patch('Services.push_notifications.webpush') as send:
            push._deliver(json.dumps(dict(title='Vaja',body='Vaja',url='/dogodki/2',event_id=2)))
        payloads=[json.loads(call.kwargs['data']) for call in send.call_args_list]
        self.assertEqual([a['action'] for a in payloads[0]['actions']],['present','absent'])
        self.assertNotIn('actions',payloads[1])
        rows[0]['event_date']=datetime.now(timezone.utc)-timedelta(days=1)
        with patch('Services.push_notifications.webpush') as send:
            push._deliver(json.dumps(dict(title='Vaja',body='Vaja',url='/dogodki/2',event_id=2)))
        self.assertNotIn('actions',json.loads(send.call_args_list[0].kwargs['data']))

if __name__=='__main__':unittest.main()

