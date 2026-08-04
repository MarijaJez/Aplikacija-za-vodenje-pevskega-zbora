INSERT INTO roles (name, description) VALUES
('Predsednik', 'Vodi organizacijske in upravne naloge zbora.'),
('Zborovodja', 'Umetniško vodi zbor in pripravlja program.'),
('Blagajnik', 'Skrbi za finančno poslovanje zbora.'),
('Notar', 'Ureja in razdeljuje notno gradivo.'),
('Beleženje prisotnosti', 'Beleži in ureja prisotnost članov.'),
('Član', 'Redno sodeluje na vajah in dogodkih.');

INSERT INTO people (first_name, last_name, birth_date, email, phone, voice) VALUES
('Ana', 'Kovač', '1998-03-14', 'ana.kovac@zbor.si', '+386 40 123 456', 'Sopran'),
('Maja', 'Zupan', '1995-11-08', 'maja.zupan@zbor.si', '+386 41 222 981', 'Alt'),
('Luka', 'Mlakar', '1992-07-22', 'luka.mlakar@zbor.si', '+386 31 654 123', 'Tenor'),
('Rok', 'Kos', '1989-01-02', 'rok.kos@zbor.si', '+386 51 334 788', 'Bas'),
('Eva', 'Horvat', '2000-05-19', 'eva.horvat@zbor.si', '+386 40 886 421', 'Sopran'),
('Miha', 'Novak', '1997-09-30', 'miha.novak@zbor.si', '+386 31 907 122', 'Tenor');

INSERT INTO users (person_id, username, password_hash, must_change_password)
SELECT id, lower(unaccent_name), crypt(password, gen_salt('bf')), must_change
FROM (
  SELECT p.id,
    CASE p.first_name
      WHEN 'Ana' THEN 'ana.kovac' WHEN 'Maja' THEN 'maja.zupan' WHEN 'Luka' THEN 'luka.mlakar'
      WHEN 'Rok' THEN 'rok.kos' WHEN 'Eva' THEN 'eva.horvat' ELSE 'miha.novak' END AS unaccent_name,
    CASE WHEN p.first_name IN ('Ana','Luka') THEN 'zbor2026' ELSE
      CASE p.first_name WHEN 'Maja' THEN 'maja.zupan' WHEN 'Luka' THEN 'luka.mlakar'
      WHEN 'Rok' THEN 'rok.kos' WHEN 'Eva' THEN 'eva.horvat' ELSE 'miha.novak' END END AS password,
    p.first_name NOT IN ('Ana','Luka') AS must_change
  FROM people p
) seeded_users;

INSERT INTO person_roles (person_id, role_id)
SELECT p.id, r.id FROM people p CROSS JOIN roles r WHERE
(p.first_name = 'Ana' AND r.name IN ('Član','Blagajnik')) OR
(p.first_name = 'Maja' AND r.name IN ('Član','Beleženje prisotnosti')) OR
(p.first_name = 'Luka' AND r.name IN ('Član','Predsednik')) OR
(p.first_name = 'Rok' AND r.name = 'Član') OR
(p.first_name = 'Eva' AND r.name IN ('Član','Notar')) OR
(p.first_name = 'Miha' AND r.name IN ('Član','Zborovodja'));

INSERT INTO categories (name, description) VALUES
('Slovenska','Slovenska zborovska dela'),('Ljudska','Ljudske pesmi'),('Sakralna','Sakralni program'),
('Klasična','Klasična dela'),('Popularna','Popularne priredbe'),('A cappella','Dela brez instrumentalne spremljave'),('Umetna','Umetne pesmi');

INSERT INTO songs (title, author, created_at) VALUES
('Lipa zelenela je','Miroslav Vilhar','2026-07-28'),
('Ave verum corpus','W. A. Mozart','2026-07-20'),
('Africa','David Paich & Jeff Porcaro','2026-07-15'),
('Nocoj pa, oh nocoj','Alojz Srebotnjak','2026-02-02'),
('Shenandoah','James Erb','2026-01-14');

INSERT INTO song_categories (song_id, category_id)
SELECT s.id, c.id FROM songs s JOIN categories c ON
(s.title='Lipa zelenela je' AND c.name IN ('Slovenska','Ljudska')) OR
(s.title='Ave verum corpus' AND c.name IN ('Sakralna','Klasična')) OR
(s.title='Africa' AND c.name IN ('Popularna','A cappella')) OR
(s.title='Nocoj pa, oh nocoj' AND c.name IN ('Slovenska','Umetna')) OR
(s.title='Shenandoah' AND c.name IN ('Ljudska','A cappella'));

INSERT INTO song_reviews (person_id, song_id, rating, comment, updated_at)
SELECT p.id, s.id, v.rating, v.comment, NOW() - (v.days || ' days')::interval
FROM (VALUES
('Maja','Lipa zelenela je',5,'Čudovita skladba, posebej mi je všeč dinamika v zadnjem delu.',1),
('Luka','Lipa zelenela je',4,'Tenorski del je zahteven, ampak zelo hvaležen za petje.',6),
('Rok','Lipa zelenela je',5,'Ena mojih najljubših v našem programu.',10),
('Ana','Ave verum corpus',5,'Odlično zveni v našem prostoru.',8),
('Eva','Africa',4,'Zabavna in ritmično zanimiva priredba.',12)
) AS v(first_name,title,rating,comment,days)
JOIN people p ON p.first_name=v.first_name JOIN songs s ON s.title=v.title;

INSERT INTO events (event_date, event_type, name, place) VALUES
('2026-08-08 19:00+02','Vaja','Sekcijska vaja','Glasbena učilnica'),
('2026-08-14 18:30+02','Vaja','Skupna vaja','Kulturni dom'),
('2026-08-22 20:00+02','Koncert','Poletni večer pesmi','Grajsko dvorišče'),
('2026-07-29 18:30+02','Vaja','Generalna vaja','Kulturni dom'),
('2026-06-12 19:30+02','Nastop','Zaključni koncert','Mestna dvorana');

INSERT INTO event_program (event_id, song_id, performance_rating, comment, position)
SELECT e.id, s.id, CASE WHEN e.name='Zaključni koncert' THEN 5 ELSE NULL END, '', row_number() OVER (PARTITION BY e.id ORDER BY s.id)
FROM events e CROSS JOIN songs s WHERE
(e.name='Sekcijska vaja' AND s.id <= 4) OR (e.name='Skupna vaja') OR (e.name='Poletni večer pesmi') OR
(e.name='Generalna vaja') OR (e.name='Zaključni koncert');

WITH statuses(person_name, event_name, status) AS (VALUES
('Ana','Sekcijska vaja','present'),('Ana','Skupna vaja','present'),('Ana','Poletni večer pesmi','late_under'),('Ana','Generalna vaja','present'),('Ana','Zaključni koncert','present'),
('Maja','Sekcijska vaja','present'),('Maja','Skupna vaja','excused'),('Maja','Poletni večer pesmi','present'),('Maja','Generalna vaja','present'),('Maja','Zaključni koncert','late_under'),
('Luka','Sekcijska vaja','late_over'),('Luka','Skupna vaja','present'),('Luka','Poletni večer pesmi','present'),('Luka','Generalna vaja','absent'),('Luka','Zaključni koncert','present'),
('Rok','Sekcijska vaja','present'),('Rok','Skupna vaja','late_under'),('Rok','Poletni večer pesmi','excused'),('Rok','Generalna vaja','present'),('Rok','Zaključni koncert','present'),
('Eva','Sekcijska vaja','excused'),('Eva','Skupna vaja','present'),('Eva','Poletni večer pesmi','present'),('Eva','Generalna vaja','late_over'),('Eva','Zaključni koncert','absent'),
('Miha','Sekcijska vaja','absent'),('Miha','Skupna vaja','late_over'),('Miha','Poletni večer pesmi','present'),('Miha','Generalna vaja','present'),('Miha','Zaključni koncert','excused'))
INSERT INTO attendance(event_id, person_id, status, updated_by)
SELECT e.id,p.id,s.status,(SELECT id FROM users WHERE username='luka.mlakar')
FROM statuses s JOIN people p ON p.first_name=s.person_name JOIN events e ON e.name=s.event_name;

INSERT INTO transactions (transaction_date, description, person_name, kind, amount, settled, created_by) VALUES
('2026-08-01','Članarine za avgust','Ana Kovač','Prihodek',570.00,TRUE,(SELECT id FROM users WHERE username='ana.kovac')),
('2026-07-28','Najem grajskega dvorišča','Luka Mlakar','Odhodek',320.00,TRUE,(SELECT id FROM users WHERE username='ana.kovac')),
('2026-07-24','Tisk koncertnih programov','Eva Horvat','Odhodek',86.40,FALSE,(SELECT id FROM users WHERE username='ana.kovac')),
('2026-07-18','Donacija Občine','Občina','Prihodek',750.00,TRUE,(SELECT id FROM users WHERE username='ana.kovac')),
('2026-07-12','Pogostitev po koncertu','Maja Zupan','Odhodek',142.80,FALSE,(SELECT id FROM users WHERE username='ana.kovac')),
('2026-07-05','Prodaja vstopnic','Ana Kovač','Prihodek',460.00,TRUE,(SELECT id FROM users WHERE username='ana.kovac'));
