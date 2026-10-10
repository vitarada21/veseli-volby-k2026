"""
Refresh election results embedded in ../index.html.

Fetches per-district (okrsek) 2022 and 2026 results for Veseli nad Luznici
(obec 553271) from seznamzpravy.cz, re-aggregates them, and re-injects the
`const DATA = {...}` block in index.html.

Usage:
    python scripts/update_data.py

Safe to re-run any time during/after the 2026 count finishes - districts
that are not yet final are simply left as "pending" (editable in the UI).
"""
import json
import re
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OBEC = "553271"
TOWN = "veseli-nad-luznici"

PARTY_ID = {
    'VESELÁCI A SPORT PRO MĚSTO': 'vspm',
    'ANO 2011': 'ano',
    'ŽENY PRO MĚSTO': 'zeny',
    'KDU-ČSL': 'kdu',
    'Veselí pro Veseláky': 'vpv',
    'Nestraníci pro Veselí nad Lužnicí': 'nestr',
    'TOP 09': 'top09',
    'Občanská demokratická strana': 'ods',
    'Naše Česko': 'nc',
}
PARTY_META = {
    'vspm':  {'label': 'Veseláci a sport pro město', 'color': '--p-vspm'},
    'ano':   {'label': 'ANO 2011', 'color': '--p-ano'},
    'zeny':  {'label': 'Ženy pro město', 'color': '--p-zeny'},
    'kdu':   {'label': 'KDU-ČSL', 'color': '--p-kdu'},
    'vpv':   {'label': 'Veselí pro Veseláky', 'color': '--p-vpv'},
    'nestr': {'label': 'Nestraníci pro Veselí n. L.', 'color': '--p-nestr'},
    'top09': {'label': 'TOP 09', 'color': '--p-top09'},
    'ods':   {'label': 'ODS', 'color': '--p-ods'},
    'nc':    {'label': 'Naše Česko', 'color': '--p-nc'},
}
DISTRICTS_META = {
    '1': {'group': 'I', 'place': 'MŠ III, Pod Markem č.p. 532',
          'streets': ['adresy mimo ulici', 'K Zastávce', 'Na Slepičáku', 'P. Voka', 'Pod Markem', 'U Lužnice']},
    '2': {'group': 'I', 'place': 'MŠ III, Pod Markem č.p. 532',
          'streets': ['adresy mimo ulici', '5. května', 'A. Jiráska', 'Ak. Bydžovského', 'Budějovická', 'Hřbitovní', 'Pod Markem', 'Podskalí']},
    '3': {'group': 'I', 'place': 'MŠ I, Blatské sídliště č.p. 570',
          'streets': ['adresa mimo ulici', 'Blatská', 'Blatské sídliště', 'Budějovická', 'Hlinice', 'Krátká', 'Na Kapradí',
                      'Na Potoce', 'Na Skalce', 'Na Strážkách', 'Nad Chmelnicí', 'náměstí T. G. Masaryka', 'Nová',
                      'Pod Vodojemem', 'Podhájek', 'Polní', 'Průběžná', 'Sokolská', 'Svinenská', 'Třída Čs. armády (Veselí I)',
                      'V. Filípka', 'Větrná', 'Weisova', 'Zahradní']},
    '4': {'group': 'I', 'place': 'MěÚ, náměstí T. G. Masaryka č.p. 26',
          'streets': ['adresy mimo ulici', 'Blatské sídliště', 'náměstí T. G. Masaryka', 'Hamerská', 'Štěpnice']},
    '5': {'group': 'II', 'place': 'Dům s pečovatelskou službou, Třída Čs. armády č.p. 835',
          'streets': ['Alešovo nábřeží', 'F. Líbala', 'Foglarovo nábřeží', 'Hlobilova', 'Husova', 'J. Lady', 'Jateční',
                      'Jindřichohradecká', 'Jungmannova', 'K Trati', 'Karla IV.', 'Krkavec', 'Malé náměstí', 'Mánesova',
                      'Maredova', 'Na Pískách', 'P. Brandla', 'Pod Dehetníkem', 'Roháčova', 'Říční', 'Smetanova',
                      'Třída Čs. armády (Veselí II)', 'U Družstva', 'U Vodárny', 'V. Slukova', 'Za Slabých', 'Žižkova']},
    '6': {'group': 'II', 'place': 'MŠ II, Třída Čs. armády č.p. 308',
          'streets': ['adresy mimo ulici', 'B. Jablonského', 'Čtvrť J. Hybeše', 'Erbenova', 'Havlíčkova', 'Hrubínova',
                      'J. K. Tyla', 'J. V. Sládka', 'K. Čapka', 'K. H. Máchy', 'Klobasná', 'Krále Jiřího', 'Kubatova',
                      'Maredova', 'M. Krškové', 'Na Pasekách', 'Nádražní', 'Nerudova', 'Pod Rafandou', 'Průmyslová',
                      'Riegrova', 'S. Čecha', 'Samota', 'Svojsíkova', 'Třída Čs. armády (Veselí II)', 'U Přejezdu',
                      'Vrchlického', 'Zlukovská']},
    '7': {'group': 'Horusice', 'place': 'MŠ Horusice č.p. 58', 'streets': ['Horusice (celá místní část)']},
}


def fetch(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read().decode('utf-8', errors='replace')


def strip_text(html):
    data2 = re.sub(r'<script.*?</script>', ' ', html, flags=re.S)
    data2 = re.sub(r'<style.*?</style>', ' ', data2, flags=re.S)
    text = re.sub(r'<[^>]+>', '|', data2)
    text = text.replace('\xa0', ' ')
    text = re.sub(r'\|+', '|', text)
    text = re.sub(r'[ \t]+', ' ', text)
    return text


def is_num(t):
    return bool(re.match(r'^[\d ]+$', t.strip()))


def num(tok):
    return int(tok.replace(' ', ''))


def parse_district(html, year_label):
    text = strip_text(html)
    m = re.search(r'účast\|([\d, ]+) ?%', text)
    turnout = float(m.group(1).strip().replace(' ', '').replace(',', '.')) if m else None

    start = text.find('Tabulka zobrazuje')
    end = text.find('Vyberte lokalitu')
    seg = text[start:end] if start != -1 and end != -1 else ''
    header = f'|Strana/koalice|Strana/koalice|Hlasy {year_label}|Hlasy |'
    seg = seg.split(header, 1)
    seg = seg[1] if len(seg) > 1 else ''
    seg = re.sub(r'^\d{4}\|', '', seg)
    tokens = [t for t in seg.split('|') if t != '']

    parties = []
    i = 0
    while i < len(tokens):
        abbrev = tokens[i]
        if i + 1 >= len(tokens):
            break
        fullname = tokens[i + 1]
        if i + 2 < len(tokens) and is_num(tokens[i + 2]):
            votes = num(tokens[i + 2])
            pct_tok = tokens[i + 3] if i + 3 < len(tokens) else ''
            pctm = re.search(r'([\d,]+) ?%', pct_tok)
            pct = float(pctm.group(1).replace(',', '.')) if pctm else None
            pid = PARTY_ID.get(fullname)
            parties.append({'id': pid, 'votes': votes, 'pct': pct})
            i += 4
            if i < len(tokens) and is_num(tokens[i]):
                i += 2
        else:
            i += 1
    parties.sort(key=lambda p: -p['votes'])
    return turnout, parties


def fetch_year(year):
    out = {}
    for n in map(str, range(1, 8)):
        url = f'https://www.seznamzpravy.cz/p/vysledky-voleb/{year}/komunalni-volby/okrsek/{OBEC}-{TOWN}-{n}?noredirect=1'
        html = fetch(url)
        turnout, parties = parse_district(html, year)
        out[n] = {'turnout': turnout, 'final': bool(parties), 'parties': parties}
        print(f'  {year} okrsek {n}: final={bool(parties)} turnout={turnout}')
    return out


def fetch_official_town_2026():
    """Authoritative town-wide aggregate (and, once final, candidate-level
    preferential votes) from the Czech Statistical Office."""
    url = f'https://volby.gov.cz/appdata/kv2026/20261009/odata/zastup/vysledky_obec_{OBEC}.xml'
    try:
        xml = fetch(url)
    except Exception as e:
        print('  (could not reach CSU XML, falling back to district sum):', e)
        return None

    import xml.etree.ElementTree as ET
    ns = {'k': 'http://www.volby.cz/kv/'}
    root = ET.fromstring(xml)
    obec = root.find('k:OBEC', ns)
    vysl = obec.find('k:VYSLEDEK', ns)
    ucast = vysl.find('k:UCAST', ns)

    je_spocteno = obec.get('JE_SPOCTENO') == '1'
    party_votes = {}
    elected = []
    for strana in vysl.findall('k:VOLEBNI_STRANA', ns):
        sname = strana.get('NAZEV_STRANY')
        party_votes[sname] = int(strana.get('HLASY'))
        for z in strana.findall('k:ZASTUPITEL', ns):
            elected.append({
                'partyId': PARTY_ID.get(sname),
                'order': int(z.get('PORADOVE_CISLO')),
                'titlePre': z.get('TITULPRED') or '',
                'first': z.get('JMENO'),
                'last': z.get('PRIJMENI'),
                'titlePost': z.get('TITULZA') or '',
                'votes': int(z.get('HLASY')),
                'pct': float(z.get('HLASY_PROC')),
            })
    elected.sort(key=lambda m: -m['votes'])

    return {
        'turnout': float(ucast.get('UCAST_PROC')),
        'okrskyZprac': int(ucast.get('OKRSKY_ZPRAC')),
        'final': je_spocteno,
        'partyVotes': party_votes,  # town-wide totals, for deriving a missing district by subtraction
        'elected': elected,
    }


def derive_missing_district(districts, official):
    """If exactly one district's per-okrsek page never went final but the town
    total is final/complete, back it out as (town total - sum of the other 6).
    This happens when CSU finishes a town before the district-level mirror
    (seznamzpravy) catches up on that one last okrsek."""
    if not official or not official.get('partyVotes'):
        return
    missing = [n for n in districts if not districts[n]['y2026']['final']]
    if len(missing) != 1:
        return
    target = missing[0]
    others_sum = {}
    for n, d in districts.items():
        if n == target:
            continue
        for p in d['y2026']['parties']:
            others_sum[p['id']] = others_sum.get(p['id'], 0) + p['votes']

    derived = []
    for name, total in official['partyVotes'].items():
        pid = PARTY_ID.get(name)
        votes = total - others_sum.get(pid, 0)
        if votes > 0:
            derived.append({'id': pid, 'votes': votes})
    grand_total = sum(p['votes'] for p in derived) or 1
    for p in derived:
        p['pct'] = round(p['votes'] / grand_total * 100, 2)
    derived.sort(key=lambda p: -p['votes'])

    districts[target]['y2026'] = {'turnout': None, 'final': True, 'derived': True, 'parties': derived}
    print(f'  Derived okrsek {target} by subtraction ({grand_total} votes) — '
          f'not published separately by CSU yet.')


def main():
    print('Fetching 2022 (historical, final)...')
    y2022 = fetch_year(2022)
    print('Fetching 2026 (live)...')
    y2026 = fetch_year(2026)

    districts = {}
    for n in map(str, range(1, 8)):
        meta = DISTRICTS_META[n]
        districts[n] = {
            'group': meta['group'], 'place': meta['place'], 'streets': meta['streets'],
            'y2022': {'turnout': y2022[n]['turnout'], 'final': True, 'parties': y2022[n]['parties']},
            'y2026': {'turnout': y2026[n]['turnout'], 'final': y2026[n]['final'], 'parties': y2026[n]['parties']},
        }

    official = fetch_official_town_2026()
    if official and not all(districts[n]['y2026']['final'] for n in districts):
        derive_missing_district(districts, official)

    counted2026 = sum(1 for n in districts if districts[n]['y2026']['final'])
    town_final = bool(official and official['final'] and counted2026 == 7)
    town2026 = {'turnout': official['turnout'] if official else None, 'final': town_final}
    if official:
        town2026['okrskyZprac'] = official['okrskyZprac']

    data = {
        'meta': {'town': 'Veselí nad Lužnicí', 'counted2026': counted2026, 'total': 7},
        'town': {'y2022': {'turnout': 43.09, 'final': True}, 'y2026': town2026},
        'partyMeta': PARTY_META,
        'districts': districts,
        'elected': official['elected'] if (official and town_final) else [],
    }

    index_path = ROOT / 'index.html'
    html = index_path.read_text(encoding='utf-8')
    data_js = json.dumps(data, ensure_ascii=False)
    new_html, n = re.subn(r'const DATA = \{.*?\};\n', 'const DATA = ' + data_js + ';\n', html, count=1, flags=re.S)
    if n != 1:
        raise SystemExit('Could not find "const DATA = {...};" block in index.html')
    index_path.write_text(new_html, encoding='utf-8')
    print(f'\nUpdated {index_path} — {counted2026}/7 okrsky final for 2026'
          + (f', CSU reports {official["okrskyZprac"]}/7, town final={town_final}' if official else ''))


if __name__ == '__main__':
    main()
