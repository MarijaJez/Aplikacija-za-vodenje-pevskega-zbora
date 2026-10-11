# Produkcijska objava

- URL: https://mpz-homec.algorhythmo.com
- GitHub: https://github.com/MarijaJez/Aplikacija-za-vodenje-pevskega-zbora.git
- Produkcijska veja: `main`.
- SSH: `mpz@algorhythmo.com`, vrata `22022`, obstoječi SSH ključ.
- Mapa na strežniku: `/home/mpz/www`.
- Storitev: `mpz-app.service`.
- Okolje: `/home/mpz/.config/mpz-app.env`; skrivnosti ne sodijo v Git.

## Trajno dovoljenje

Vse nove funkcionalnosti, ki jih uporabnica zahteva, po uspešnem testiranju samodejno pushaj in objavi na produkcijo. Dodatna potrditev ni potrebna. Če testi ne uspejo, najprej popravi napake. Če dostop ali preverjanje ni mogoče, sporoči oviro in ne trdi, da je objava uspela.

## Postopek

1. Pridobi najnovejši `origin/main` in spremembo pripravi v ločenem checkoutu na tej različici. Osnovna lokalna mapa je lahko starejša in vsebuje nepovezano delo drugih chatov. Ohrani novejše produkcijske funkcije.
2. Preglej diff, zaženi ustrezne teste in preverjanje Python sintakse. Spremembe baze zahtevajo združljivo migracijo brez ponastavljanja baze ali začetnih podatkov.
3. Commitaj samo datoteke svoje spremembe in uporabi `git push origin HEAD:main`. Če je veja medtem napredovala, pridobi nove spremembe, jih vključi in ponovi ustrezne teste. Ne uporabljaj force push.
4. Preveri, da je Git status na strežniku čist, zabeleži prejšnji commit in objavi:

```powershell
ssh -4 -o BatchMode=yes -p 22022 mpz@algorhythmo.com 'cd /home/mpz/www && git pull --ff-only origin main && sudo -n systemctl restart mpz-app.service && sudo -n systemctl is-active mpz-app.service'
```

5. Preveri produkcijski commit, prijavno stran in prizadete funkcije. Za testne zapise onemogoči zunanja obvestila in Google sinhronizacijo ter zapise počisti. Integracijskih testov, ki spreminjajo podatke, ne izvajaj nenadzorovano na produkciji.
6. Ob težavi preveri dnevnik storitve in pripravi povrnitev z Git revert. Ohrani produkcijske podatke, uploads in nastavitve okolja.

Čas konca dogodka: aplikacija ob inicializaciji povezave doda nullable `event_end` s preverjanjem `event_end > event_date`. Stari dogodki ostanejo brez znanega konca; koledarski izvoz pri njih ohrani dosedanjo predpostavko dveh ur.

## Jutranji opomniki dogodkov

`deploy/mpz-event-reminders.timer` uporablja systemd `OnCalendar=*-*-* 08:00:00 Europe/Ljubljana` in `Persistent=true`. Časovni pas samodejno upošteva poletni/zimski čas. Zamujen zagon se izvede po vklopu strežnika; delavec pred 08:00 ne pošilja, po 08:00 pa izbere samo še nezačete dogodke današnjega lokalnega dne. Vsi prejemniki in osebne nastavitve se določijo v obstoječem push sistemu. Člani brez odgovora dobijo gumba Prisoten/Odsoten in povezavo na dogodek.

Namestitev (enkrat in ob spremembi enot):
```sh
sudo install -m 644 deploy/mpz-event-reminders.service deploy/mpz-event-reminders.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now mpz-event-reminders.timer
```

Delavec uporablja isti EnvironmentFile in virtualno okolje kot aplikacija. Ne potrebuje novih skrivnosti. Status: `systemctl list-timers mpz-event-reminders.timer`; dnevniki: `journalctl -u mpz-event-reminders.service`. Varno preverjanje brez pošiljanja ali zapisov deduplikacije: z naloženim produkcijskim okoljem `.venv/bin/python -m Services.event_reminders --dry-run`. Nikoli ročno ne zaganjaj storitve za testna obvestila članom.

Združljiva migracija ustvari `event_reminder_deliveries`; unikatni ključ (dogodek, lokalni dan, endpoint) se atomarno in trajno rezervira **pred** zunanjim pošiljanjem. Ponovni zagon ali vzporedni delavci ne ponovijo poskusa. Dostava je best-effort / at-most-once: ob prekinitvi procesa po rezervaciji ali napaki ponudnika je opomnik lahko izpuščen. Web Push ne ponuja transakcijskega exactly-once pošiljanja, zato neuspelih rezerviranih dostav ne ponavljamo. Ne briši evidence med rednimi objavami. Potekli endpointi se odstranijo po obstoječem postopku. TTL opomnika je omejen tudi s časom do začetka dogodka.
