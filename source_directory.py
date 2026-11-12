"""Curated navigation links, NOT proof that a country is automatically scanned.

Only entries with connector='feed' can be activated as automated feeds.
Portal entries are research bookmarks; they must never be passed to the RSS scanner.
Every country is represented in the UI, but missing connectors remain transparent.
"""
from catalog import COUNTRIES, EU, STARTER_SOURCES

# Links here are intentionally to official publishing services or EU country
# guides, not guessed RSS endpoints. A legal portal homepage is NOT a finding URL.
EU_CODES = {
 'Austria':'at','Belgium':'be','Bulgaria':'bg','Croatia':'hr','Cyprus':'cy',
 'Czechia':'cz','Denmark':'dk','Estonia':'ee','Finland':'fi','France':'fr',
 'Germany':'de','Greece':'el','Hungary':'hu','Ireland':'ie','Italy':'it',
 'Latvia':'lv','Lithuania':'lt','Luxembourg':'lu','Malta':'mt','Netherlands':'nl',
 'Poland':'pl','Portugal':'pt','Romania':'ro','Slovakia':'sk',
 'Slovenia':'si','Spain':'es','Sweden':'se'
}

# First-party legislation databases, known directory landing URLs. Not feed URLs.
DIRECT_PORTALS = {
 'European Union':[('EUR-Lex: EU law','https://eur-lex.europa.eu/homepage.html','eur-lex.europa.eu')],
 'United Kingdom':[('legislation.gov.uk','https://www.legislation.gov.uk/','legislation.gov.uk')],
 'Norway':[('Lovdata: Norwegian legislation','https://lovdata.no/','lovdata.no')],
 'Finland':[('Finlex: Finnish legislation','https://www.finlex.fi/en','finlex.fi')],
 'Denmark':[('Retsinformation: Danish legislation','https://www.retsinformation.dk/','retsinformation.dk')],
 'Sweden':[('Riksdagen: Swedish legislation','https://www.riksdagen.se/sv/dokument-och-lagar/','riksdagen.se')],
 'Iceland':[('Althingi: Icelandic legislation','https://www.althingi.is/lagasafn/','althingi.is')],
 'Netherlands':[('Official Dutch announcements','https://officielebekendmakingen.nl/','officielebekendmakingen.nl')],
 'Ireland':[('Irish Statute Book','https://www.irishstatutebook.ie/','irishstatutebook.ie')],
 'Switzerland':[('Fedlex: Swiss federal law','https://www.fedlex.admin.ch/en/home','fedlex.admin.ch')],
 'Lithuania':[('Lithuanian legal acts register','https://www.e-tar.lt/','e-tar.lt')],
 'France':[('Légifrance','https://www.legifrance.gouv.fr/','legifrance.gouv.fr')],
 'Germany':[('Gesetze im Internet','https://www.gesetze-im-internet.de/','gesetze-im-internet.de')],
 'Italy':[('Normattiva','https://www.normattiva.it/','normattiva.it')],
 'Spain':[('Boletín Oficial del Estado','https://www.boe.es/','boe.es')],
 'Portugal':[('Diário da República','https://diariodarepublica.pt/','diariodarepublica.pt')],
 'Austria':[('RIS: Austrian legal information','https://www.ris.bka.gv.at/','ris.bka.gv.at')],
 'Poland':[('ISAP: Polish legal acts','https://isap.sejm.gov.pl/','isap.sejm.gov.pl')],
 'Belgium':[('Belgian Official Gazette','https://www.ejustice.just.fgov.be/','ejustice.just.fgov.be')],
 'Estonia':[('Riigi Teataja','https://www.riigiteataja.ee/en/','riigiteataja.ee')],
 'Latvia':[('Latvijas Vēstnesis','https://www.vestnesis.lv/','vestnesis.lv')],
 'Czechia':[('e-Sbírka','https://www.e-sbirka.cz/','e-sbirka.cz')],
 'Slovakia':[('Slov-Lex','https://www.slov-lex.sk/','slov-lex.sk')],
 'Slovenia':[('PISRS: Slovenian law','https://pisrs.si/','pisrs.si')],
 'Croatia':[('Narodne novine','https://narodne-novine.nn.hr/','narodne-novine.nn.hr')],
 'Romania':[('Portal Legislativ','https://legislatie.just.ro/','legislatie.just.ro')],
 'Greece':[('National Printing House','https://www.et.gr/','et.gr')],
 'Türkiye':[('Resmî Gazete','https://www.resmigazete.gov.tr/','resmigazete.gov.tr')],
 'Ukraine':[('Verkhovna Rada legislation','https://zakon.rada.gov.ua/','zakon.rada.gov.ua')],
 'Serbia':[('Pravno-informacioni sistem','https://www.pravno-informacioni-sistem.rs/','pravno-informacioni-sistem.rs')],
}

DIRECTORY = []
for s in STARTER_SOURCES:
    DIRECTORY.append(dict(country=s['country'],name=s['name'],url=s['url'],
        official_domain=s['official_domain'],connector='feed',kind=s['kind'],
        publisher='Official publication feed',description='Automated RSS/Atom connector; requires a successful live scan.'))
for country, portals in DIRECT_PORTALS.items():
    for name,url,domain in portals:
        DIRECTORY.append(dict(country=country,name=name,url=url,official_domain=domain,
            connector='portal',kind=None,publisher='National/EU legislation portal',
            description='Research bookmark only. No automated monitoring until a feed/API connector is developed.'))
# Each EU country also receives an EU-maintained reference guide, even if a
# direct publisher portal has not been curated yet. These guides are NOT feeds.
for country in EU:
    DIRECTORY.append(dict(country=country,name='EU e-Justice: national legislation guide',
        url=f'https://e-justice.europa.eu/topics/legislation-and-case-law/national-legislation/{EU_CODES[country]}_en',
        official_domain='e-justice.europa.eu',connector='portal',kind=None,
        publisher='European e-Justice Portal',
        description='EU directory of national law sources; not a live legislation feed.'))


def directory_for(country):
    return [x.copy() for x in DIRECTORY if x['country']==country]


def directory_counts():
    return {c:len(directory_for(c)) for c in COUNTRIES}
