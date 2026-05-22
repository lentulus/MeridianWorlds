#!/usr/bin/env python3
"""Seed GURPS Spaceships 2–8 ships into world.db and write import log."""

import sqlite3, sys, os, re
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config import WORLDS_DB

LOG_PATH = Path(__file__).parent.parent / 'docs' / 'logs' / 'ss2_8_import.md'
BUREAU = 1

NEW_TYPES = [
    (48,'Star Fighter',1),(49,'Bio-Survey Ship',0),(50,'Deep Space Scout',0),
    (51,'Covert Scout',1),(52,'Sleeper Ship',0),(53,'Colonial Prison Ship',0),
    (54,'Mining Drone',0),(55,'Orbital Factory',0),(56,'Orbital Habitat',0),
    (57,'Catapult Ship',0),(58,'Volatile Miner',0),(59,'Asteroid Mine Station',0),
    (60,'Asteroid Prospector',0),(61,'Interstellar Prospector',0),
    (62,'Gas-Mining Cruiser',0),(63,'Gas-Mining Shuttle',0),(64,'Gas-Mining Platform',0),
    (65,'Planetoid Mine',0),(66,'Age of Sail',0),(67,'Psionic',0),
    (68,'Reality Police',1),(69,'Biosystem',0),(70,'Autonomous Kill Vehicle',1),
    (71,'Deep Space Operations Vehicle',0),(72,'Executive Space Vehicle',0),
    (73,'Transatmospheric Vehicle',0),(74,'Heavy Space Transport',0),
    (75,'Microgravity Assault Vehicle',1),(76,'Orbital Spacecraft',0),
    (77,'Passenger Space Vehicle',0),(78,'Space Control Vehicle',1),
    (79,'Space Defense Platform',1),(80,'Space Dominance Vehicle',1),
    (81,'Unusual Vessel',0),(82,'Utility Space Vehicle',0),
]

EXPECTED_DST = {5:20,6:30,7:50,8:70,9:100,10:150,11:200,12:300,13:500,14:700,15:1000}


def parse_tl(s):
    s = s.strip()
    return int(s.rstrip('^')), (1 if s.endswith('^') else 0)


def parse_hnd(s):
    s = s.strip()
    if s in ('–','-','','–/–','-/-'):
        return None, None
    m = re.match(r'(-?\d+)/(\d+)', s)
    return (int(m.group(1)), int(m.group(2))) if m else (None, None)


def parse_move(s):
    s = s.strip()
    if s in ('–','-','','– (stationary)','–/–','-/-'):
        return None, None, 0, 0, None
    if '(atm only)' in s:
        return None, None, 0, 1, None
    if '(plasma sail)' in s:
        return None, None, 0, 0, 'plasma sail — non-standard propulsion'
    note = None
    if '*' in s:
        note = 'asterisked value — verify against source'
        s = s.replace('*','')
    if '‡' in s:
        note = 'special mark ‡ — verify against source'
        s = s.replace('‡','')
    s = s.replace(',','').strip()
    m = re.match(r'^([\d.]+)\s*mps$', s)
    if m:
        return None, float(m.group(1)), 0, 0, note
    m = re.match(r'^([\d.]+)\s*G\s*/\s*c$', s)
    if m:
        return float(m.group(1)), None, 1, 0, note
    m = re.match(r'^([\d.]+)\s*G\s*/\s*([\d.]+)\s*mps$', s)
    if m:
        return float(m.group(1)), float(m.group(2)), 0, 0, note
    m = re.match(r'^([\d.]+)\s*G$', s)
    if m:
        return float(m.group(1)), None, 0, 0, note
    return None, None, 0, 0, f'unparsed: {s}'


def parse_occ(s):
    s = s.strip()
    if s in ('–','-',''):
        return None, None, 0, 0, None
    if s == '0':
        return 0, 0, 0, 0, None
    agrav = 1 if 'ASV' in s else 0
    short = 1 if 'SV' in s and not agrav else 0
    num = s.replace(',','').replace('ASV','').replace('SV','').strip()
    if '+' in num:
        p = num.split('+')
        try:
            return int(p[0]), int(p[1]), agrav, short, None
        except:
            pass
    try:
        return int(num), 0, agrav, short, None
    except:
        return None, None, 0, 0, f'unparsed: {s}'


def parse_ddr(s):
    s = s.strip()
    if s in ('–','-',''):
        return None, None, None, None
    if s == '0':
        return 0, 0, 0, None
    s = s.replace(',','')
    if '/' in s:
        p = s.split('/')
        if len(p) == 3:
            try:
                return int(p[0]), int(p[1]), int(p[2]), None
            except:
                pass
    try:
        v = int(s)
        return v, v, v, None
    except:
        return None, None, None, f'unparsed: {s}'


def parse_cost(s):
    s = s.strip().replace(',','')
    if s in ('–','-',''):
        return None
    s = s.lstrip('$')
    if s.endswith('B'):
        return float(s[:-1]) * 1e9
    if s.endswith('M'):
        return float(s[:-1]) * 1e6
    if s.endswith('K'):
        return float(s[:-1]) * 1e3
    try:
        return float(s)
    except:
        return None


# Each tuple: (book, type_name, class_name, tl_str, sm, dst_hp,
#              hnd_str, ht_str, move_str, occ_str, ddr_str, cost_str)
SHIPS_RAW = [
    # SS2
    ('SS2','Tramp Freighter','Pioneer-Class','9',7,50,'-2/5','13','0.5G/4.32mps','8ASV','5/5/5','$4.05M'),
    ('SS2','Tramp Freighter','Outlander-Class','10',9,100,'-3/5','13','–','32ASV','–','$46.2M'),
    ('SS2','Tramp Freighter','Kiev-Class','10^',9,100,'-1/5','13','1.5G/20 mps','36ASV','7/7/7','$139.7M'),
    ('SS2','Tramp Freighter','Anthem-Class','10^',8,70,'-1/5','13','2G/c','20ASV','3/3/3','$25.9M'),
    ('SS2','Tramp Freighter','Dark Horse-Class','11^',8,70,'1/5','13','100G/c','20ASV','5/5/5','$94.3M'),
    ('SS2','Freight Liner','Titan-Class','10',10,150,'-5/5','13','0.005G/180 mps','10ASV','10/10/10','$157.4M'),
    ('SS2','Freight Liner','Prosperity-Class','10',11,200,'-2/5','13','0.5G/30 mps','–','–','–'),
    ('SS2','Freight Liner','Ricardo-Class','10^',10,150,'-2/5','13','–','36ASV','–','–'),
    ('SS2','Freight Liner','Betelgeuse-Class','11^',12,300,'-2/5','13','1G/c','–','20/20/20','$2,204.55M'),
    ('SS2','Freight Liner','Regulus-Class','10^',10,150,'-2/5','13','50G/c','28ASV','7/7/7','$889.4M'),
    ('SS2','Passenger Liner','Endymion-Class','9',8,70,'-3/5','13','0.01G/3.2 mps','42ASV','7/7/7','–'),
    ('SS2','Passenger Liner','Prospero-Class','10',9,100,'-3/5','13','–','–','–','–'),
    ('SS2','Passenger Liner','Empress-Class','10^',10,150,'-2/5','13','1.5G/20 mps','576ASV','–','–'),
    ('SS2','Passenger Liner','Xanadu-Class','11^',11,200,'0/5','13','50G/c','–','–','–'),
    ('SS2','Sunjammer','Icarus-Class','9',9,100,'-4/5','–','–','–','10/0/0','$515.9M'),
    ('SS2','Yacht','Kaufman-Class','9',7,50,'-4/5','13','0.001G/15 mps','4ASV','5/5/5','$6.65M'),
    ('SS2','Yacht','Vega-Class','9',8,70,'-4/5','13','0.04G/48 mps','14ASV','–','$29.4M'),
    ('SS2','Yacht','Taj Mahal-Class','11^',9,100,'-1/5','13','4G/c','36ASV','–','$80.6M'),
    ('SS2','Yacht','Ulysses-Class','11^',7,50,'-1/5','14','2G/c','8ASV','7/7/7','$24.13M'),
    ('SS2','Yacht','Zeta Reticuli-Class','12^',8,70,'–','–','–','14ASV','–','$65.7M'),
    ('SS2','Yacht','Baikonur First Stage','7',6,70,'-1/5','13','6G/2.52 mps','–','2/0/0','$7.6M'),
    ('SS2','Launch Vehicle','Conestoga-Class','9',8,70,'-1/5','13','4G/9.1 mps','2SV','–','$13.1M'),
    ('SS2','Launch Vehicle','Condor Spaceplane','9',6,30,'–','–','–','2+6SV','3/3/3','$9.17M'),
    ('SS2','Shuttle/Lighter','Thunderbird','10^',9,100,'-1/5','12','3G/7.5 mps','2ASV','7/7/7','$119.8M'),
    ('SS2','Shuttle/Lighter','Alpha Shuttlecraft','11^',5,20,'0/4','12','4G/c','2+6SV','3/2/2','$743K'),
    ('SS2','Shuttle/Lighter','Hermes-Class','10',8,70,'-3/5','13','0.02G/432mps','10ASV','10/0/7','$49.2M'),
    ('SS2','Courier/Speedster','Dart-Class','11^',8,70,'0/5','13','150G/c','8ASV','15/15/15','$101M'),
    ('SS2','Orbital Transfer','Aurora OTV','8',5,20,'0/4','12','3G/0.45 mps','1+8SV','1/1/1','$808K'),
    ('SS2','Orbital Transfer','Copernicus Ferry','9',6,30,'-1/4','12','0.5G/2.75 mps','2+30SV','3/3/3','$1.18M'),
    # SS3
    ('SS3','Battleship','Ragnarok-class','8',11,200,'-3/4','13','2G/12 mps','156ASV','45/15/60','$1.57B'),
    ('SS3','Battleship','Admiral-class','10^',11,200,'-2/5','13','1G/45mps','–','–','–'),
    ('SS3','Battleship','Fenris-class','11^',13,500,'-1/5','13','100G/c','–','0','–'),
    ('SS3','Battleship','Empire-class','11^',14,700,'-1/5','13','100G/c','4,600ASV','10','–'),
    ('SS3','Heavy Cruiser','Trinity-class','9',10,150,'-2/5','13','4G/20 mps','84ASV','–','$576.35M'),
    ('SS3','Heavy Cruiser','Sword-class','11^',11,200,'0/5','13','100G/c','–','–','$8,188M'),
    ('SS3','Space Cruiser','Victory-class','10',10,150,'-3/5','13','0.1G/50 mps','80ASV','–','$828.1M'),
    ('SS3','Strike Cruiser','Tsunami-class','10^',10,150,'-2/5','13','1G/45 mps','94ASV','–','–'),
    ('SS3','Battle Cruiser','Eclipse-class','12^',11,200,'–','–','–','–','–','$9.951B'),
    ('SS3','Frontier Cruiser','Intrepid-class','12^',12,300,'–','–','–','640ASV','–','$37,312M'),
    ('SS3','Space Patrol','Anson-class','9^',7,50,'-1/5','13','4G/18 mps','10ASV','5','$8.93M'),
    ('SS3','Frigate','Deimos-class','10',8,70,'-2/5','13','0.15G/40 mps','12ASV','–','$77.8M'),
    ('SS3','Frigate','Battle-class','10^',9,100,'-1/5','13','1G/30 mps','24ASV','–','$387M'),
    ('SS3','Frigate','Tiger-class','11^',9,100,'1/5','13','150G/c','20ASV','–','$825.6M'),
    ('SS3','Frigate','Seraphim-class','12^',8,70,'–','–','–','10ASV','–','$350M'),
    ('SS3','Patrol Ship','Cossack-class','10^',7,50,'-1/5','13','1.5G/45 mps','4ASV','10','$46.6M'),
    ('SS3','Patrol Ship','Vixen-class','11^',7,50,'1/5','13','100G/c','4ASV','–','$69.15M'),
    ('SS3','Corsair','Loki-class','10^',10,150,'-3/5','13','0.5G/30 mps','10ASV','20','$444.5M'),
    ('SS3','Corsair','Renegade-class','11^',8,70,'1/5','13','100G/c','24ASV','–','$65.7M'),
    ('SS3','Battle Station','Sentinel-class','9',6,30,'0/4','12','3G/0.15 mps','–','20/15/10','$5.73M'),
    ('SS3','Battle Station','Gibraltar-class','10',14,700,'-5/5','13','0.05G/0.8 mps','2,000ASV','–','–'),
    # SS4
    ('SS4','Fighter','Red Arrow','9',6,30,'0/4','–','–','2SV','5/3/3','$7.27M'),
    ('SS4','Fighter','Meteor','9^',5,20,'0/4','12','4G/7.5 mps*','1SV','6/4/4','$2.65M'),
    ('SS4','Fighter','Shrike','10',6,30,'0/4','12','2G/6.48 mps','2SV','14/7/7','$8.13M'),
    ('SS4','Fighter','Dragon','10^',6,30,'0/4','12','1G/c','2SV','–','$17.05M'),
    ('SS4','Fighter','Nova','9',6,30,'0/4','12','4G/4.2 mps','2SV','14/7/7','$5.31M'),
    ('SS4','Fighter','Panther','10',6,30,'-1/4','12','0.6G/5.4 mps','2SV','40/30/20','$9.49M'),
    ('SS4','Fighter','Lancer','10^',6,30,'0/4','12','3G/15 mps','2SV','–','$17.39M'),
    ('SS4','Assault Carrier','Overlord-class','10',13,500,'-5/5','14','0.01G/180 mps','3,320ASV','100','$58.692B'),
    ('SS4','Assault Carrier','Warrior-class','10^',11,200,'-2/5','13','1G/45 mps','1,860ASV','50','$2.769B'),
    ('SS4','Assault Corvette','Ranger-class','10^',9,100,'-1/5','13','2G/15 mps','128ASV','40/40/20','$331M'),
    ('SS4','Fighter','Starhawk','11^',5,20,'–','–','–','1SV','–','$9.115M'),
    ('SS4','Fighter','Wyvern','11^',6,30,'–','–','–','2ASV','–','$23.36M'),
    ('SS4','Fighter','Hornet','11^',5,20,'–','–','–','–','0','$7.63M'),
    ('SS4','Drop Ship','Valkyrie-class','9',7,50,'-1/5','16','–','3SV','7/5/5','$13.76M'),
    ('SS4','Drop Ship','Alexander-class','10^',8,70,'-1/5','–','–','–','–','$67.2M'),
    ('SS4','Drop Ship','Banshee-class','11^',6,30,'–','–','–','2+12SV','–','$12.16M'),
    ('SS4','Drop Ship','Tungusku','12^',5,20,'–','–','–','1+12SV','–','$7.28M'),
    ('SS4','Fleet Carrier','Alliance-class','10^',13,500,'-3/5','–','–','3,600ASV','150/100/100','$31.126B'),
    ('SS4','Fleet Carrier','Thor-class','10^',12,300,'-2/5','20','–','1,220ASV','200','$11.6B'),
    ('SS4','Super Carrier','God of War-class','11^',14,700,'-1/5','13','100G/c','–','–','–'),
    ('SS4','Boarding Ship','Ahab-class','9',5,20,'0/4','–','–','1+8SV','12/6/9','$0.953M'),
    ('SS4','Assault Boat','Corvus','11^',6,30,'0/4','12','2G/c*','2+42SV','21/7/14','$3.92M'),
    ('SS4','Grappler Ship','Samson-class','9',6,30,'0/4','12','2G/2 mps','2SV','14','$6.48M'),
    ('SS4','Grappler Ship','Beowulf-class','10^',8,70,'-1/5','13','1G/30 mps','8ASV','30/15/15','$132.1M'),
    ('SS4','Light Carrier','Mithra-class','9',8,70,'-4/5','13','0.003G','26ASV','10/10/10','$56.8M'),
    ('SS4','Light Carrier','Nebula-class','10^',9,100,'-1/5','13','2G/22.5 mps','48ASV','30/15/15','$723.2M'),
    ('SS4','Light Carrier','Tarot-class','11^',11,200,'0/5','14','100G/c','200ASV','–','$5.512B'),
    ('SS4','Strike Carrier','Inferno-class','10',10,150,'-4/5','13','0.01G/240 mps','120ASV','60/30/30','$588M'),
    ('SS4','Mecha','Spartan','9',5,20,'0/4','12','3G/0.3 mps','1SV','20/10/10','$2.45M'),
    ('SS4','Mecha','Black Knight','10^',6,30,'0/4','12','3G/10 mps','1SV','–','$18.76M'),
    ('SS4','Mecha','Ariel','10^',5,20,'0/4','12','4G/22.5 mps*','1SV','–','$10.04M'),
    ('SS4','Assault Pod','Hades','9^',6,30,'0/4','12','2G/2.5 mps','1SV','–','$10.48M'),
    ('SS4','Star Fighter','Galaxy Striker','12^',7,50,'–','–','–','2SV','–','$160.25M'),
    # SS5
    ('SS5','Space Probe','Icarus-class','8',5,20,'-4/3','12','0.001G/21.6 mps','–','2','$1,227K'),
    ('SS5','Deep Space Probe','Comet-class','9',7,50,'-3/5','12','0.01G/192 mps','–','7/5/5','$22.07M'),
    ('SS5','Launch Vehicle','Polaris Booster','11',10,150,'-5/5','12','0.005G/11,200 mps','–','0','$68.6M'),
    ('SS5','Launch Vehicle','Nova I','7',7,100,'-2/4','12','3G/3.12 mps','–','0','$2.8M'),
    ('SS5','Deep Space Scout','Phobos-class','8',6,30,'-1/3','12','3G/4.05 mps','4ASV','0','$1.15M'),
    ('SS5','Exploration Ship','Constellation-class','9^',9,100,'-3/5','13','0.03G/20 mps','32ASV','15','$165.9M'),
    ('SS5','Exploration Ship','Odyssey-class','9',9,100,'-3/5','–','–','16ASV','15/10/10','$88.5M'),
    ('SS5','Exploration Ship','Einstein-class','11',10,150,'-5/5','13','–','40ASV','50','$1,532M'),
    ('SS5','Exploration Ship','Dirac-class','12^',11,200,'-3/5','–','–','–','–','$2.91275B'),
    ('SS5','Exploration Ship','Palomar-class','12^',13,500,'0/5','13','1,000G/c','1,680ASV','–','$82.785B'),
    ('SS5','Armored Scout','Kilroy-class','10^',8,70,'-1/5','13','2G/15 mps','12ASV','14/14/7','$101.5M'),
    ('SS5','Lander','Artemis-class','8',5,20,'-1/3','12','3G/1.89 mps','1+6SV','2','$291K'),
    ('SS5','Lander','Lowell Lander','8',5,30,'–','–','–','1+4SV','1/0/0','$285K'),
    ('SS5','Lander','Lowell Ascent','8',5,20,'-1/3','12','3G/3.12 mps','–','30','–'),
    ('SS5','Lander','Helldiver-class','9',6,30,'0/4','12','2G/5.67 mps','2+6SV','5','$12.31M'),
    ('SS5','Lander','Komarov-class','10',5,20,'0/4','13','0.6G/5.76 mps','1+6SV','3/2/2','$890K'),
    ('SS5','Lander','Grissom-class','11^',5,20,'0/4','12','6G/c','1+6SV','10/5/5','$2,055K'),
    ('SS5','Bio-Survey Ship','Orpheus-class','10',9,100,'-3/5','13','0.02G/216 mps','10ASV','15','$146M'),
    ('SS5','Bio-Survey Ship','Darwin-class','10^',8,70,'-1/5','13','1.5G/10 mps','60ASV','7','$62.6M'),
    ('SS5','Survey Ship','Serengeti-class','10^',7,50,'-2/5','13','0.5G/c','–','10','$28.2M'),
    ('SS5','Covert Scout','Columbia-class','11^',8,70,'-1/5','13','1G/c','66ASV','10','$56.6M'),
    ('SS5','Covert Scout','Roswell-class','11^',7,50,'0/5','13','50G/c','16ASV','–','$52M'),
    ('SS5','Colony Ship','Star Hunter-class','12^',8,70,'–','–','–','6ASV','–','$444.5M'),
    ('SS5','Colony Ship','Genesis-class','10^',11,200,'-2/5','13','0.5G/30 mps','4,900ASV','–','–'),
    ('SS5','Generation Ship','Exodus-class','11^',12,300,'-2/5','13','2G/c','17,750ASV','15','$4,280M'),
    ('SS5','Generation Ship','Universe-class','10',14,700,'-5/5','21','–','6,000ASV','15','$78.51B'),
    ('SS5','Factory Ship','Endeavor-class','11',13,500,'-6/5','–','–','–','–','–'),
    ('SS5','Sleeper Ship','Star Seed-class','11',6,30,'-3/4','–','–','–','30/10/10','$30.32M'),
    ('SS5','Space Station','Charon-class','10',8,70,'-3/5','13','0.01G/3.78 mps','6ASV','5/0/5','$18.1M'),
    ('SS5','Colonial Prison Ship','Alcatraz-class','10^',9,100,'-2/5','13','0.5G/c','356ASV','–','$124.3M'),
    # SS6
    ('SS6','Mining Drone','Kobold','9',5,20,'0/4','12','1.5G/0.75 mps','1+2SV','–','$1.095M'),
    ('SS6','Orbital Factory','Planetoid-class','9',7,50,'-1/5','13','1G/2.25 mps','4ASV','10/5/5','$11.91M'),
    ('SS6','Orbital Habitat','Panama-class','8',6,30,'-1/3','13','3G/2.31 mps','–','2','$860K'),
    ('SS6','Tug','Quarterhorse-class','9',9,100,'-3/5','13','0.03G/30 mps','20ASV','7','$107.6M'),
    ('SS6','Tug','Kinshasa-class','10^',12,300,'-2/5','13','1G/60 mps','40ASV','20','–'),
    ('SS6','Tug','Termagant-class','10^',6,100,'–','–','–','2SV','4','$1.8M'),
    ('SS6','Catapult Ship','Nomad-class','9',10,150,'-4/5','13','0.02G/3.78 mps','20ASV','–','$236.2M'),
    ('SS6','Volatile Miner','Mosquito-class','9',9,100,'-3/5','13','0.03G/28mps','–','7','$88.6M'),
    ('SS6','Asteroid Mine Station','Vredefort-class','9',12,300,'-4/5*','13','0.01G/1.2 mps*','–','14/14/7','$1.9541B'),
    ('SS6','Asteroid Prospector','Wildcat-class','10',6,30,'-2/4','13','0.01G/300 mps','2ASV','3','$5.93M'),
    ('SS6','Mining Ship','Klondike-class','10^',8,70,'-2/5','13','0.5G/45 mps','6ASV','7','$69.7M'),
    ('SS6','Planetoid Mine','Rock Snake','10',14,700,'-6/5','–','–','20,000ASV','–','$94.42B'),
    ('SS6','Interstellar Prospector','Nugget-class','11^',7,50,'0/5','13','50G/c','4ASV','–','$20.03M'),
    ('SS6','Gas-Mining Cruiser','Tempest-class','9',7,50,'-1/5*','13','1G/0 mps*','6ASV','5','–'),
    ('SS6','Gas-Mining Shuttle','Storm Bird-class','9',6,30,'0/4*','12','1G/12.15 mps*','2SV','–','$6.28M'),
    ('SS6','Gas-Mining Platform','Titanic-class','10^',13,500,'-4/5','13','0.5G/c','900ASV','–','$19.51105B'),
    ('SS6','Tanker','Jupiter-class','10',11,200,'-5/5','–','–','6ASV','15/0/15','$596.6M'),
    ('SS6','Tanker','Aquarius-class','11^',13,500,'-3/5','13','4G/c','14ASV','20','–'),
    # SS7
    ('SS7','Age of Sail','Star Galleon','4^',7,50,'-3/4','13','0.2G/c','–','2','$5.59M'),
    ('SS7','Age of Sail','Soul Slaver','3^',7,50,'-3/4','13','0.3G/c','82ASV','–','$6.15M'),
    ('SS7','Psionic','Psi-Jammer','11^',12,300,'1/5','13','1,500 mps‡','500ASV','–','$7.982B'),
    ('SS7','Reality Police','Operator-class','12^',9,100,'–','–','–','20ASV','70','$20.982B'),
    ('SS7','Biosystem','Tree Ship','10^',13,500,'-4/5','14','0.1G/c','–','–','$41.585B'),
    # SS8
    ('SS8','Autonomous Kill Vehicle','Kupu-Kupu-class AKV','9',7,50,'-1/5','12','1G/0.55 mps','0','28','$10.31M'),
    ('SS8','Autonomous Kill Vehicle','Rajasi-class AKV','10',6,30,'-1/4','12','0.2G/72 mps','0','28/7/7','$8.13M'),
    ('SS8','Autonomous Kill Vehicle','SIM-7 Predator-class AKV','10',6,30,'-1/4','12','0.3G/20 mps','0','50/20/30','$14.22M'),
    ('SS8','Autonomous Kill Vehicle','Zhengyang-class AKV','10',6,30,'-1/4','12','0.3G/20 mps','0','28/14/21','$7.82M'),
    ('SS8','Deep Space Operations Vehicle','Shepard-class DSOV','10',10,150,'-4/5','13','0.05G/84 mps','24ASV','15','$357.65M'),
    ('SS8','Deep Space Operations Vehicle','Thule-class DSOV','9',11,200,'-5/4','13','0.015G/16 mps','80ASV','15/6/3','$735M'),
    ('SS8','Executive Space Vehicle','Mojave-class ESV','10',8,70,'-2/5','12','0.2G/96 mps','8ASV','20/10/0','$57.25M'),
    ('SS8','Executive Space Vehicle','Sunlance-class ESV','10',8,70,'-3/4','12','0.3G/154 mps','2ASV','20/0/0','$69.135M'),
    ('SS8','Transatmospheric Vehicle','Chronos-class TAV','10',7,50,'-2/5','12','0.47G/2.4 mps','2+60SV','10/0/0','$5.91M'),
    ('SS8','Transatmospheric Vehicle','Diaoche-class TCAV','10',7,50,'-1/5','12','3G/1.08 mps','1SV','10/5/5','$14.69M'),
    ('SS8','Transatmospheric Vehicle','Eurofighter Tempest TCAV','9',7,50,'–/–','12','–/– (atm only)','0','5','$21.95M'),
    ('SS8','Heavy Space Transport','Mercury-class HLV','10',9,100,'-2/4','12','6G/6.3 mps','1+800SV','7/7/14','$32.85M'),
    ('SS8','Transatmospheric Vehicle','Molniya-class Ballistic Ramjet TAV','9',9,100,'–/–','–','–/– (atm only)','2+460SV','0','$211.2M'),
    ('SS8','Transatmospheric Vehicle','Pegasus-class TAV','10',8,70,'–/–','12','–/– (atm only)','2SV','–','$18.9M'),
    ('SS8','Transatmospheric Vehicle','SATV','10',6,30,'0/4','12','1.3G/24 mps','0','10/10/50','$8.9M'),
    ('SS8','Heavy Space Transport','Lewis-class HSTV','9',10,150,'-5/4','12','0.015G/83.2 mps','0','15','$182.2M'),
    ('SS8','Heavy Space Transport','Parus-class HSTV','9',10,150,'–/–','12','–/– (plasma sail)','12ASV','20','$185.16M'),
    ('SS8','Heavy Space Transport','Spokane-class HSTV','10',10,150,'-4/5','13','0.05G/84 mps','10ASV','30/30/0','$461.8M'),
    ('SS8','Heavy Space Transport','Zhongguang-class HSTV','11',11,200,'-5/4','13','0.05G/84 mps','0','60/30/30','$18.47M'),
    ('SS8','Microgravity Assault Vehicle','AC-425 Seminole-class MAV','10',5,20,'0/4','12','3G/0.75 mps','0+16SV','9/3/0','$0.52M'),
    ('SS8','Microgravity Assault Vehicle','MAV-IIB Puma','9',5,20,'-1/3','12','9G/0.6 mps','1SV','6','$0.57M'),
    ('SS8','Orbital Spacecraft','Bumblebee Work Pod','9',5,20,'0/4','12','1.5G/1.44 mps','1SV','6','$0.57M'),
    ('SS8','Orbital Spacecraft','Kagoshima-class OTV','9',7,50,'-1/5','12','1.5G/1.44 mps','3+40SV','5/5/0','$3.43M'),
    ('SS8','Orbital Spacecraft','Schaffer-class OTV','9',7,50,'-3/5','–','–','20ASV','7','$6.43M'),
    ('SS8','Orbital Spacecraft','Steptoe-class DRV','9',8,70,'-2/5','13','0.17G/14.4 mps','3SV','7/7/5','–'),
    ('SS8','Orbital Spacecraft','Tahmas-class ITP','10',5,20,'-1/4','12','0.5G/1.8 mps','1+18SV','3','$0.43M'),
    ('SS8','Orbital Spacecraft','Usagi-class Hopper LTV','9',5,20,'0/4','12','1G/0.2 mps','–','2','$278K'),
    ('SS8','Passenger Space Vehicle','Meizi-class PSV','10',10,150,'-4/5','13','0.05G/126 mps','32ASV','20','$219.6M'),
    ('SS8','Passenger Space Vehicle','Mochi-class PSV','11',11,200,'-4/5','13','0.05G/208 mps','220ASV','–','$200.2M'),
    ('SS8','Space Control Vehicle','DCS-4 Grizzly-class SCV','10',11,200,'-5/4','13','0.05G/96 mps','220ASV','300/200/100','$4,699.75M'),
    ('SS8','Space Control Vehicle','Gang Lung-class SCV','10',11,200,'-4/5','13','0.05G/72 mps','96ASV','150/100/50','$1,283.25M'),
    ('SS8','Space Control Vehicle','Shengzi-class SCV','9',11,200,'-4/5','13','0.015G/33.6 mps','100ASV','45/15/0','$1,288.95M'),
    ('SS8','Space Defense Platform','Avskermar SDP','9',7,50,'-1/5','12','1G/0.1 mps','0','35','$9.06M'),
    ('SS8','Space Defense Platform','Barricade-class SDP','9',5,20,'0/4','12','3G/0.3 mps','0','15/9/6','$1.49M'),
    ('SS8','Space Defense Platform','Shanzi-class SDP','9',12,300,'-6/4','13','0.005G/1.3 mps','300ASV','80','$2.92B'),
    ('SS8','Space Dominance Vehicle','DFS-3C Archangel-class SDV','10',11,200,'-4/4','13','0.1G/151.2 mps','36ASV','140/70/70','$2,767.85M'),
    ('SS8','Space Dominance Vehicle','LSDV-5 Hermann Oberth-class SDV','10',9,100,'-2/5','12','0.2G/43.2 mps','20ASV','–','$207.5M'),
    ('SS8','Space Dominance Vehicle','Konigsberg-class SDV','10',10,150,'-4/4','13','0.2G/57.6 mps','–','–','$980.6M'),
    ('SS8','Space Dominance Vehicle','Riguang-class SDV','10',10,150,'-5/4','13','0.05G/100.8 mps','–','–','–'),
    ('SS8','Space Dominance Vehicle','Salahudin Samboja-class SDV','10',10,150,'-4/5','13','0.05G/40 mps','24ASV','90/60/30','$673.5M'),
    ('SS8','Space Dominance Vehicle','SDV-90 Resolution/Gram-class','10',10,150,'-3/5','13','0.1G/40 mps','–','–','$747.25M'),
    ('SS8','Space Dominance Vehicle','Xingzhai-class SDV','10',11,200,'-4/4','13','0.05G/96 mps','32ASV','90/30/30','$1,348.35M'),
    ('SS8','Space Station','Asteroid Base','9',13,500,'–','12','–','200ASV','40/30/40','$6,149.79M'),
    ('SS8','Space Station','Cynosure-class Station','10',10,150,'–','13','–','200ASV','13','$382.5M'),
    ('SS8','Space Station','Omnistar-class Space Platform','9',8,70,'–','–','–','–','–','$21.8M'),
    ('SS8','Space Station','Von Braun-class Station','10',13,500,'–','14','–','1,400ASV','30','$65.5325B'),
    ('SS8','Space Station','Vulcan-class Station','9',12,300,'–','14','–','660ASV','20','$6.606B'),
    ('SS8','Unusual Vessel','Ernst Opik-class','10',9,100,'-5/4','12','0.0017G/540 mps','4ASV','–','$52.1M'),
    ('SS8','Unusual Vessel','Nadezhda Bioship','10',9,100,'-3/5','13','0.01G/5.04 mps','8ASV','10','$120.45M'),
    ('SS8','Unusual Vessel','SEM-23B Peregrine RSV','10',6,30,'-1/4','12','0.1G/126 mps','0','15/5/5','$9.22M'),
    ('SS8','Unusual Vessel','Solaris','10',10,150,'-5/5','–','– (stationary)','0','–','$1,043.5M'),
    ('SS8','Unusual Vessel','X-92 AKV','10',6,30,'0/4','12','4G/2.5 mps','0','50/20/30','$11.85M'),
    ('SS8','Utility Space Vehicle','Golub-class USV','9',10,150,'-5/4','13','0.01G/6.72 mps','8ASV','15/0/0','$84.85M'),
    ('SS8','Utility Space Vehicle','Mudlark-class USV','10',7,50,'-3/5','12','0.015G/56 mps','10ASV','3/0/0','$5.34M'),
    ('SS8','Utility Space Vehicle','Sudbury-class USV','10',10,150,'-4/5','13','0.05G/84 mps','26ASV','15/15/0','$169.15M'),
]


def main():
    conn = sqlite3.connect(WORLDS_DB)
    conn.execute("PRAGMA foreign_keys = ON")

    conn.executemany("INSERT OR IGNORE INTO ship_types VALUES (?,?,?)", NEW_TYPES)
    conn.commit()

    type_map = {name: tid for tid, name, _ in
                conn.execute("SELECT type_id, name, military FROM ship_types").fetchall()}

    log_lines = ['# SS2–8 Import Log\n',
                 'Generated by `scripts/seed_ss2_8.py`.\n',
                 '⚠ = needs review; ✓ = inserted without exceptions.\n']

    current_book = None
    book_ok = book_warn = 0
    total_ok = total_warn = 0

    for row in SHIPS_RAW:
        book, type_name, class_name, tl_str, sm, dst_hp, \
            hnd_str, ht_str, move_str, occ_str, ddr_str, cost_str = row

        if book != current_book:
            if current_book is not None:
                log_lines.append(f'\n*{book_ok} OK, {book_warn} REVIEW*\n')
                total_ok += book_ok
                total_warn += book_warn
            current_book = book
            book_ok = book_warn = 0
            log_lines.append(f'\n## {book}\n')
            log_lines.append('| Ship | Status | Notes |')
            log_lines.append('|------|--------|-------|')

        issues = []

        tl, is_sup = parse_tl(tl_str)

        if sm in EXPECTED_DST and dst_hp != EXPECTED_DST[sm]:
            issues.append(f'dST/HP={dst_hp} expected {EXPECTED_DST[sm]} for SM+{sm}')

        handling, sr = parse_hnd(hnd_str)

        ht = None
        ht_s = ht_str.strip()
        if ht_s not in ('–', '-', ''):
            try:
                ht = int(ht_s)
            except ValueError:
                issues.append(f'unparsed HT: {ht_str}')

        accel, dv, is_ftl, atm_only, move_note = parse_move(move_str)
        if move_note:
            issues.append(f'Move: {move_note}')

        crew, pax, agrav, short_v, occ_note = parse_occ(occ_str)
        if occ_note:
            issues.append(f'Occ: {occ_note}')

        ddr_f, ddr_c, ddr_r, ddr_note = parse_ddr(ddr_str)
        if ddr_note:
            issues.append(f'dDR: {ddr_note}')

        cost = parse_cost(cost_str)

        if book == 'SS8':
            issues.append('auto-extracted — verify against source')

        type_id = type_map.get(type_name)
        if type_id is None:
            issues.append(f'unknown type: {type_name}')

        try:
            conn.execute("""
                INSERT INTO ships
                (hull_number,name,class_name,type_id,bureau_id,parent_ship_id,
                 tl,is_superscience,sm,is_streamlined,dst_hp,handling,stability_rating,ht,
                 move_accel_g,move_delta_v_mps,move_is_ftl,move_atm_only,
                 lwt_tons,load_tons,occ_crew,occ_passengers,occ_has_artificial_grav,occ_is_short_voyage,
                 ddr_front,ddr_central,ddr_rear,range_ftl,cost_dollars,
                 date_laid_down,date_commissioned,date_removed,fate_id,notes)
                VALUES
                (NULL,NULL,?,?,?,NULL,?,?,?,0,?,?,?,?,?,?,?,?,NULL,NULL,?,?,?,?,?,?,?,NULL,?,0,0,NULL,NULL,NULL)
            """, (class_name, type_id, BUREAU, tl, is_sup, sm, dst_hp,
                  handling, sr, ht, accel, dv, is_ftl, atm_only,
                  crew, pax, agrav, short_v,
                  ddr_f, ddr_c, ddr_r, cost))
        except Exception as e:
            issues.append(f'INSERT ERROR: {e}')

        if issues:
            book_warn += 1
            log_lines.append(f'| {class_name} | ⚠ REVIEW | {"; ".join(issues)} |')
        else:
            book_ok += 1
            log_lines.append(f'| {class_name} | ✓ OK | |')

    log_lines.append(f'\n*{book_ok} OK, {book_warn} REVIEW*\n')
    total_ok += book_ok
    total_warn += book_warn
    log_lines.append(f'\n---\n\n**Total: {total_ok + total_warn} ships — {total_ok} OK, {total_warn} REVIEW**\n')

    conn.commit()

    total_ships = conn.execute("SELECT COUNT(*) FROM ships").fetchone()[0]
    types_count = conn.execute("SELECT COUNT(*) FROM ship_types").fetchone()[0]
    print(f"ship_types: {types_count} rows")
    print(f"ships:      {total_ships} rows (including SS1)")

    conn.close()

    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    LOG_PATH.write_text('\n'.join(log_lines) + '\n')
    print(f"Log:        {LOG_PATH}")


if __name__ == '__main__':
    main()
