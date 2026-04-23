-- Vstavljanje testnih podatkov za aplikacijo pevskega zbora

-- Vloge
INSERT INTO public.vloge (naziv, opis) VALUES
('admin', 'Skrbnik sistema'),
('pevec', 'Član zbora'),
('skrbnik prisotnosti', 'Upravlja prisotnost na dogodkih');

-- Glasovi (šifrant)
INSERT INTO public.glasovi (naziv_glasu) VALUES
('sopran'),
('alt'),
('tenor'),
('bas');

-- Kategorije pesmi
INSERT INTO public.kategorije (naziv, opis) VALUES
('slovenske ljudske', 'Tradicionalne slovenske ljudske pesmi'),
('filmska glasba', 'Pesmi iz filmov in muziklov'),
('sakralna glasba', 'Cerkevna in duhovna glasba'),
('popularna glasba', 'Popularne pesmi za koncertni program');

-- Pesmi
INSERT INTO public.pesem (naslov, avtor, note) VALUES
('Zdravljica', 'France Prešeren', 'documents/zdravljica.pdf'),
('My Heart Will Go On', 'James Horner', 'documents/my_heart_will_go_on.pdf'),
('Ave Maria', 'Franz Schubert', 'documents/ave_maria.pdf'),
('Galopper', 'Carl Nielsen', 'documents/galopper.pdf'),
('Slovenija, od kod lepote tvoje', 'Slavko Avsenik', 'documents/slovenija_od_kod_lepote_tvoje.pdf');

-- Dogodki
INSERT INTO public.dogodek (datum, vrsta_dogodka, naziv_dogodka) VALUES
('2026-05-03', 'pevska vaja', 'Prva pevska vaja v maju'),
('2026-06-15', 'letni koncert', 'Letni koncert v mestni dvorani'),
('2026-07-10', 'zborov izlet', 'Zborov izlet v Bohinj');

-- Osebe
INSERT INTO public.oseba (ime, priimek, datum_rojstva, eposta, telefonska_stevilka, id_glasu, delitev_na_3, delitev_na_4, id_vloge) VALUES
('Ana', 'Novak', '1990-04-12', 'ana.novak@example.com', '+38640123456', 1, 1, 1, 1),
('Maja', 'Kovač', '1997-11-08', 'maja.kovac@example.com', '+38640123457', 2, 3, 3, 2),
('Luka', 'Zupan', '1988-02-20', 'luka.zupan@example.com', '+38640123458', 3, 1, 2, 2),
('Matej', 'Horvat', '1994-08-30', 'matej.horvat@example.com', '+38640123459', 4, 3, 3, 2),
('Sara', 'Petrič', '1992-01-17', 'sara.petric@example.com', '+38640123460', 1, 2, 2, 3),
('Tomaž', 'Kranjc', '1985-12-05', 'tomaz.kranjc@example.com', '+38640123461', 4, 4, 4, 2);

-- Prisotnost na dogodkih
INSERT INTO public.prisotnost (id_dogodka, id_osebe, prisotnost) VALUES
(1, 1, TRUE),
(1, 2, TRUE),
(1, 3, TRUE),
(1, 4, TRUE),
(1, 5, TRUE),
(1, 6, TRUE),
(2, 1, TRUE),
(2, 2, TRUE),
(2, 3, TRUE),
(2, 4, TRUE),
(2, 5, TRUE),
(2, 6, TRUE),
(3, 1, TRUE),
(3, 2, TRUE),
(3, 3, TRUE),
(3, 4, FALSE),
(3, 5, TRUE),
(3, 6, TRUE);

-- Program za dogodke (pesmi na posameznem dogodku)
INSERT INTO public.program (id_dogodka, id_pesmi, ocena, komentar) VALUES
(1, 1, NULL, 'Začetna vaja: slovenska himna'),
(1, 2, NULL, 'Ogrevalna pesem iz filmske glasbe'),
(2, 1, NULL, 'Otvoritvena pesem letnega koncerta'),
(2, 3, NULL, 'Sakralna točka v drugem delu koncerta'),
(2, 4, NULL, 'Instrumentalna pesem v zaključku koncerta'),
(3, 2, NULL, 'Pesem za pot na izlet'),
(3, 5, NULL, 'Zaključna slovenska pesem na izletu');

-- Povezava pesmi in kategorij
INSERT INTO public.pesem_kategorija (id_pesmi, id_kategorije) VALUES
(1, 1),
(2, 2),
(3, 3),
(4, 4),
(5, 1);

-- Ocene pesmi
INSERT INTO public.ocene_pesmi (id_osebe, id_pesmi, ocena, komentar) VALUES
(2, 1, 5, 'Odlično začetek in močan zborovski učinek'),
(3, 3, 4, 'Lepo zvenenje, a potrebujemo več vaje v dinamiki'),
(4, 2, 3, 'Dobro, vendar melodija ni povsem v cela'),
(5, 4, 5, 'Galopper je imel odličen ritem in energijo');
