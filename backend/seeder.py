import sqlite3
import os

print('Establishing connection to databse')
db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'database', 'ragas_test_database.db'))
connection = sqlite3.connect(db_path)
db_cursor = connection.cursor()
print('Connection established')

data_to_fill = [
    {'question': 'Aké sú podmienky súťaže pri odpredaji?', 'ground_truth': 'Podmienky súťaže pozostávajú zo 7 častí:\n1.\ntechnické podmienky - definovaný predmet odpredaja\n2.\npodmienky účasti - informácie o zábezpeke, termíne obhliadky, o kontaktnej osobe pre obhliadky\n3.\npokyny na vypracovanie a predloženie ponuky\n4.\nvýber najvhodnejšieho návrhu - definovaný postup v aukcii, priebeh aukcie\n5.\nzmluva\n6.\ndôvernosť a ochrana osobných údajov\n7.\nprílohy podmienok súťaže - prihláška do aukcie s čestným vyhlásením, špecifikácia predmetu odpredaja, vzor návrhu kúpnej zmluvy a iné\n'},
    {'question': 'Aké sú podmienky účasti súťaže odpredaja?', 'ground_truth': 'Podmienky účasti\nSúťaží sa môžu zúčastniť právnické aj fyzické osoby, ktoré spĺňajú nasledujúce podmienky:\n1.\nvoči účastníkovi nie je vedené konkurzné konanie, nie je v konkurze, v likvidácii a ani nebol proti účastníkovi zamietnutý návrh na vyhlásenie konkurzu pre nedostatok majetku,\n2.\nnavrhovateľ nemá voči vyhlasovateľovi žiadne záväzky po lehote splatnosti\na čestne vyhlasujú:\nvyhlásenie navrhovateľa o pravdivosti a úplnosti všetkých skutočností a údajov uvedených v prihláške a v ponuke,\nvyhlásenie navrhovateľa o tom, že súhlasí s podmienkami uvedenými vpodmienkach súťaže SE,\nže si predložený prvotný návrh kúpnej zmluvy prečítal a akceptuje všetky jeho základné zmluvné podmienky. V prípade neakceptovania návrhu zmluvy navrhovateľom, vyhlasovateľ vylúči navrhovateľa zo súťaže\nže navrhovateľ je riadne oboznámený s technickým stavom, vekom a rozsahom opotrebenia predmetu predaja, mieste aspôsobe uloženia\nže navrhovateľ predkladá iba jednu ponuku\n'},
    {'question': 'Kedy je možné suspendovať kupujúceho?', 'ground_truth': 'Suspendovanie kupujúceho\nKupujúcim, ktorí sú zaradení do zoznamu Suspendovaných kupujúcich nebude umožnená účasť v elektronickej aukcii. Kupujúci bude automaticky vylúčený z procesu odpredaja.\nKupujúci je zaradený do zoznamu Suspendovaných kupujúcich ak:\nkupujúci porušuje Bezpečnostno-technické podmienky plnenia\nkupujúci zavádza svojou účasťou v elektronickej aukcii, resp. svojou činnosťou počas elektronickej aukcie\nkupujúci porušuje podmienky účasti a pravidlá elektronickej aukcie\nkupujúci neopodstatnene / zámerne predlžuje uzatvorenie obchodu\nkupujúci opakovane porušuje záväzky zo zmluvy\nV prípade suspendovania kupujúceho, spoločnosť Slovenské elektrárne, a.s. zašle dotknutému kupujúcemu oznámenie o suspendovaní s uvedením dôvodu suspendovania.\n'},
    {'question': 'Aký je podiel vodných elektrární na ročnej výrobe elektriny?', 'ground_truth': 'Podiel vodných elektrární na ročnej výrobe elektrickej energie Slovenských\nelektrární, a.s., dosahuje v priemere asi 11 %.\n'},
    {'question': 'Aký výkon majú vodné elektrárne na Slovensku?', 'ground_truth': 'Sumárny inštalovaný výkon vodných elektrární v portfóliu Slovenských\nelektrární je 1 653 MW, čo je približne 40 % z celkového inštalovaného\nvýkonu Slovenských elektrární.\n'},
    {'question': 'Aký výkon majú celkovo tepelné elektrárne Slovenských elektrární?', 'ground_truth': 'Celkový inštalovaný výkon tepelných elektrární v portfóliu Slovenských elektrární, a.s., je 220 MW.\n'},
    {'question': 'Z akých častí sa skladá tepelná elektráreň?', 'ground_truth': 'Klasická elektráreň pozostáva z kotolne, medzistrojovne, strojovne, vyvedenia elektrického výkonu a z pomocných prevádzok (zauhľovanie, úprava vody, vodné hospodárstvo, zadný palivový cyklus atď.).\n'},
    {'question': 'Koho mám kontaktovať, keď mám výpadok elektriny v Bratislave?', 'ground_truth': 'Západoslovenská distribučná, a.s. 0800 111 567\n'},
    {'question': 'Ako mám v prípade otázok kontaktovať Slovenské elektrárne a kedy tak môžem urobiť? Som zákazník.', 'ground_truth': 'V prípade akýchkoľvek otázok či nejasností vám kolegovia v Slovenské elektrárne – energetické služby, s.r.o., radi poskytnú všetky informácie. 0850 555 999 Po - Pi od 8:30 do 16:00 doma@seas.sk\n'},
    {'question': 'Koľko majú na Slovensku Slovenské elektrárne reaktorových blokov a kde sa tieto bloky nachádzajú?', 'ground_truth': 'Päť reaktorových blokov – dva v AE Bohunice a ďalšie tri v AE Mochovce, dodáva takmer dve tretiny elektriny spotrebovanej na Slovensku.\n'}
]

sql = '''INSERT INTO questions(text,ground_truth) VALUES(?,?)'''

print('Inerting data into the database')
for dict in data_to_fill:
    entry = (dict['question'], dict['ground_truth'])
    db_cursor.execute(sql, entry)
    connection.commit()

print('Data successfully inserted.\nClosing the connection')
connection.close()
print('Connection closed')