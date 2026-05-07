import os
from bottle import Bottle, TEMPLATE_PATH, template, static_file, request, redirect
from Services.oseba_service import OsebaService
from Services.dogodek_service import DogodekService
from Services.pesem_service import PesemService

this_dir = os.path.dirname(__file__)
TEMPLATE_PATH.insert(0, os.path.join(this_dir, 'views'))

app = Bottle()
oseba_service = OsebaService()
dogodek_service = DogodekService()
pesem_service = PesemService()

@app.route('/static/<filename:path>')
def serve_static(filename):
    return static_file(filename, root=os.path.join(this_dir, 'static'))

@app.route('/')
def index():
    clani_count = len(oseba_service.seznam_oseb())
    dogodki_count = len(dogodek_service.seznam_dogodkov())
    pesmi_count = len(pesem_service.seznam_pesmi())
    body = template('index', clani_count=clani_count, dogodki_count=dogodki_count, pesmi_count=pesmi_count)
    return template('layout', title='Domov', body=body)

@app.route('/clani')
def clani():
    seznam = oseba_service.seznam_oseb()
    body = template('clani', osebe=seznam)
    return template('layout', title='Člani', body=body)

@app.route('/dogodki')
def dogodki():
    seznam = dogodek_service.seznam_dogodkov()
    body = template('dogodki', dogodki=seznam)
    return template('layout', title='Dogodki', body=body)

@app.route('/dogodek/<id_dogodka:int>')
def dogodek(id_dogodka):
    dogodek = dogodek_service.dobi_dogodek(id_dogodka)
    program = dogodek_service.dobi_program(id_dogodka)
    prisotnost = dogodek_service.dobi_prisotnost(id_dogodka)
    body = template('dogodek', dogodek=dogodek, program=program, prisotnost=prisotnost)
    return template('layout', title=f"Dogodek: {dogodek.naziv_dogodka}", body=body)

@app.route('/pesmi')
def pesmi():
    kategorija_id = request.query.kategorija
    if kategorija_id:
        kategorija_id = int(kategorija_id)
        seznam = pesem_service.seznam_pesmi(kategorija_id)
    else:
        kategorija_id = None
        seznam = pesem_service.seznam_pesmi()
    kategorije = pesem_service.seznam_kategorij()
    body = template('pesmi', pesmi=seznam, kategorije=kategorije, izbrana=kategorija_id)
    return template('layout', title='Pesmi', body=body)

@app.route('/pesem/<id_pesmi:int>', method=['GET', 'POST'])
def pesem(id_pesmi):
    if request.method == 'POST':
        id_osebe = int(request.forms.get('id_osebe'))
        ocena = int(request.forms.get('ocena'))
        komentar = request.forms.get('komentar', '').strip()
        pesem_service.shrani_oceno(id_osebe, id_pesmi, ocena, komentar)
        return redirect(f'/pesem/{id_pesmi}')

    pesem = pesem_service.dobi_pesem(id_pesmi)
    ocene = pesem_service.seznam_ocen(id_pesmi)
    osebe = oseba_service.seznam_oseb()
    body = template('pesem', pesem=pesem, ocene=ocene, osebe=osebe, rating_values=list(range(1, 6)))
    return template('layout', title=f"Pesem: {pesem.naslov}", body=body)

@app.route('/kategorije')
def kategorije():
    kategorije = pesem_service.seznam_kategorij()
    body = template('kategorije', kategorije=kategorije)
    return template('layout', title='Kategorije pesmi', body=body)

@app.route('/prisotnost/<id_dogodka:int>', method=['GET', 'POST'])
def prisotnost(id_dogodka):
    if request.method == 'POST':
        for key, value in request.forms.items():
            if key.startswith('prisotnost_'):
                oseba_id = int(key.split('_', 1)[1])
                prisotno = value == 'on'
                dogodek_service.shrani_prisotnost(id_dogodka, oseba_id, prisotno)
        return redirect(f'/prisotnost/{id_dogodka}')

    dogodek = dogodek_service.dobi_dogodek(id_dogodka)
    prisotnost = dogodek_service.dobi_prisotnost(id_dogodka)
    body = template('prisotnost', dogodek=dogodek, prisotnost=prisotnost)
    return template('layout', title=f"Prisotnost: {dogodek.naziv_dogodka}", body=body)
