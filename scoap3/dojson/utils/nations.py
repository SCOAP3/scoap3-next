# -*- coding: utf-8 -*-

import re
from collections import OrderedDict

# VARIABLES
NATIONS_DEFAULT_MAP = OrderedDict()

NATIONS_DEFAULT_MAP['INFN'] = 'Italy'
NATIONS_DEFAULT_MAP["Democratic People's Republic of Korea"] = "North Korea"
NATIONS_DEFAULT_MAP["DPR Korea"] = "North Korea"
NATIONS_DEFAULT_MAP["CERN"] = "CERN"
NATIONS_DEFAULT_MAP["Cern"] = "CERN"
NATIONS_DEFAULT_MAP["European Organization for Nuclear Research"] = "CERN"
NATIONS_DEFAULT_MAP["Northern Cyprus"] = "Turkey"
NATIONS_DEFAULT_MAP["North Cyprus"] = "Turkey"
NATIONS_DEFAULT_MAP["New Mexico"] = "USA"
NATIONS_DEFAULT_MAP["Hong Kong China"] = "Hong Kong"
NATIONS_DEFAULT_MAP["Hong-Kong China"] = "Hong Kong"
NATIONS_DEFAULT_MAP["Algeria"] = "Algeria"
NATIONS_DEFAULT_MAP["Argentina"] = "Argentina"
NATIONS_DEFAULT_MAP["Armenia"] = "Armenia"
NATIONS_DEFAULT_MAP["Australia"] = "Australia"
NATIONS_DEFAULT_MAP["Austria"] = "Austria"
NATIONS_DEFAULT_MAP["Azerbaijan"] = "Azerbaijan"
NATIONS_DEFAULT_MAP["Belarus"] = "Belarus"
NATIONS_DEFAULT_MAP["Belgium"] = "Belgium"
NATIONS_DEFAULT_MAP["Belgique"] = "Belgium"
NATIONS_DEFAULT_MAP["Bangladesh"] = "Bangladesh"
NATIONS_DEFAULT_MAP["Brazil"] = "Brazil"
NATIONS_DEFAULT_MAP["Brasil"] = "Brazil"
NATIONS_DEFAULT_MAP["Benin"] = "Republic of Benin"
NATIONS_DEFAULT_MAP["Bénin"] = "Republic of Benin"
NATIONS_DEFAULT_MAP["Bulgaria"] = "Bulgaria"
NATIONS_DEFAULT_MAP["Bosnia and Herzegovina"] = "Bosnia and Herzegovina"
NATIONS_DEFAULT_MAP["Canada"] = "Canada"
NATIONS_DEFAULT_MAP["Chile"] = "Chile"
NATIONS_DEFAULT_MAP["China (PRC)"] = "China"
NATIONS_DEFAULT_MAP["PR China"] = "China"
NATIONS_DEFAULT_MAP["China"] = "China"
NATIONS_DEFAULT_MAP["People's Republic of China"] = "China"
NATIONS_DEFAULT_MAP["Colombia"] = "Colombia"
NATIONS_DEFAULT_MAP["Costa Rica"] = "Costa Rica"
NATIONS_DEFAULT_MAP["Cuba"] = "Cuba"
NATIONS_DEFAULT_MAP["Croatia"] = "Croatia"
NATIONS_DEFAULT_MAP["Cyprus"] = "Cyprus"
NATIONS_DEFAULT_MAP["Czech Republic"] = "Czech Republic"
NATIONS_DEFAULT_MAP["Czech"] = "Czech Republic"
NATIONS_DEFAULT_MAP["Czechia"] = "Czech Republic"
NATIONS_DEFAULT_MAP["Denmark"] = "Denmark"
NATIONS_DEFAULT_MAP["Egypt"] = "Egypt"
NATIONS_DEFAULT_MAP["Estonia"] = "Estonia"
NATIONS_DEFAULT_MAP["Ecuador"] = "Ecuador"
NATIONS_DEFAULT_MAP["Finland"] = "Finland"
NATIONS_DEFAULT_MAP["France"] = "France"
NATIONS_DEFAULT_MAP["Georgia"] = "Georgia"
NATIONS_DEFAULT_MAP["Germany"] = "Germany"
NATIONS_DEFAULT_MAP["Deutschland"] = "Germany"
NATIONS_DEFAULT_MAP["Greece"] = "Greece"
NATIONS_DEFAULT_MAP["Hong Kong"] = "Hong Kong"
NATIONS_DEFAULT_MAP["Hong-Kong"] = "Hong Kong"
NATIONS_DEFAULT_MAP["Hungary"] = "Hungary"
NATIONS_DEFAULT_MAP["Iceland"] = "Iceland"
NATIONS_DEFAULT_MAP["India"] = "India"
NATIONS_DEFAULT_MAP["Indonesia"] = "Indonesia"
NATIONS_DEFAULT_MAP["Iran"] = "Iran"
NATIONS_DEFAULT_MAP["Ireland"] = "Ireland"
NATIONS_DEFAULT_MAP["Israel"] = "Israel"
NATIONS_DEFAULT_MAP["Italy"] = "Italy"
NATIONS_DEFAULT_MAP["Italia"] = "Italy"
NATIONS_DEFAULT_MAP["Japan"] = "Japan"
NATIONS_DEFAULT_MAP["Jamaica"] = "Jamaica"
NATIONS_DEFAULT_MAP["Korea"] = "South Korea"
NATIONS_DEFAULT_MAP["Republic of Korea"] = "South Korea"
NATIONS_DEFAULT_MAP["South Korea"] = "South Korea"
NATIONS_DEFAULT_MAP["Latvia"] = "Latvia"
NATIONS_DEFAULT_MAP["Lebanon"] = "Lebanon"
NATIONS_DEFAULT_MAP["Lithuania"] = "Lithuania"
NATIONS_DEFAULT_MAP["Luxembourg"] = "Luxembourg"
NATIONS_DEFAULT_MAP["Macedonia"] = "Macedonia"
NATIONS_DEFAULT_MAP["Mexico"] = "Mexico"
NATIONS_DEFAULT_MAP["México"] = "Mexico"
NATIONS_DEFAULT_MAP["Monaco"] = "Monaco"
NATIONS_DEFAULT_MAP["Montenegro"] = "Montenegro"
NATIONS_DEFAULT_MAP["Morocco"] = "Morocco"
NATIONS_DEFAULT_MAP["Niger"] = "Niger"
NATIONS_DEFAULT_MAP["Nigeria"] = "Nigeria"
NATIONS_DEFAULT_MAP["Netherlands"] = "Netherlands"
NATIONS_DEFAULT_MAP["The Netherlands"] = "Netherlands"
NATIONS_DEFAULT_MAP["New Zealand"] = "New Zealand"
NATIONS_DEFAULT_MAP["Zealand"] = "New Zealand"
NATIONS_DEFAULT_MAP["Norway"] = "Norway"
NATIONS_DEFAULT_MAP["Oman"] = "Oman"
NATIONS_DEFAULT_MAP["Pakistan"] = "Pakistan"
NATIONS_DEFAULT_MAP["Panama"] = "Panama"
NATIONS_DEFAULT_MAP["Philipines"] = "Philipines"
NATIONS_DEFAULT_MAP["Poland"] = "Poland"
NATIONS_DEFAULT_MAP["Portugalo"] = "Portugal"
NATIONS_DEFAULT_MAP["Portugal"] = "Portugal"
NATIONS_DEFAULT_MAP["P.R.China"] = "China"
NATIONS_DEFAULT_MAP["Romania"] = "Romania"
NATIONS_DEFAULT_MAP["Republic of San Marino"] = "Republic of San Marino"
NATIONS_DEFAULT_MAP["San Marino"] = "Republic of San Marino"
NATIONS_DEFAULT_MAP["Russia"] = "Russia"
NATIONS_DEFAULT_MAP["Russian Federation"] = "Russia"
NATIONS_DEFAULT_MAP["Saudi Arabia"] = "Saudi Arabia"
NATIONS_DEFAULT_MAP["Arabia"] = "Saudi Arabia"
NATIONS_DEFAULT_MAP["Serbia"] = "Serbia"
NATIONS_DEFAULT_MAP["Singapore"] = "Singapore"
NATIONS_DEFAULT_MAP["Slovak Republic"] = "Slovakia"
NATIONS_DEFAULT_MAP["Slovak"] = "Slovakia"
NATIONS_DEFAULT_MAP["Slovakia"] = "Slovakia"
NATIONS_DEFAULT_MAP["Slovenia"] = "Slovenia"
NATIONS_DEFAULT_MAP["South Africa"] = "South Africa"
NATIONS_DEFAULT_MAP["Africa"] = "South Africa"
NATIONS_DEFAULT_MAP["España"] = "Spain"
NATIONS_DEFAULT_MAP["Spain"] = "Spain"
NATIONS_DEFAULT_MAP["Sudan"] = "Sudan"
NATIONS_DEFAULT_MAP["Sweden"] = "Sweden"
NATIONS_DEFAULT_MAP["Switzerland"] = "Switzerland"
NATIONS_DEFAULT_MAP["Syria"] = "Syria"
NATIONS_DEFAULT_MAP["Taiwan"] = "Taiwan"
NATIONS_DEFAULT_MAP["ROC"] = "Taiwan"
NATIONS_DEFAULT_MAP["R.O.C"] = "Taiwan"
NATIONS_DEFAULT_MAP["Republic of China"] = "Taiwan"
NATIONS_DEFAULT_MAP["Thailand"] = "Thailand"
NATIONS_DEFAULT_MAP["Tunisia"] = "Tunisia"
NATIONS_DEFAULT_MAP["Turkey"] = "Turkey"
NATIONS_DEFAULT_MAP["Ukraine"] = "Ukraine"
NATIONS_DEFAULT_MAP["United Kingdom"] = "UK"
NATIONS_DEFAULT_MAP["Kingdom"] = "UK"
NATIONS_DEFAULT_MAP["UK"] = "UK"
NATIONS_DEFAULT_MAP["England"] = "UK"
NATIONS_DEFAULT_MAP["Scotland"] = "UK"
NATIONS_DEFAULT_MAP["Wales"] = "UK"
NATIONS_DEFAULT_MAP["United States of America"] = "USA"
NATIONS_DEFAULT_MAP["United States"] = "USA"
NATIONS_DEFAULT_MAP["USA"] = "USA"
NATIONS_DEFAULT_MAP["America"] = "USA"
NATIONS_DEFAULT_MAP["United Sates"] = "USA"
NATIONS_DEFAULT_MAP["Uruguay"] = "Uruguay"
NATIONS_DEFAULT_MAP["Uzbekistan"] = "Uzbekistan"
NATIONS_DEFAULT_MAP["Venezuela"] = "Venezuela"
NATIONS_DEFAULT_MAP["Vietnam"] = "Vietnam"
NATIONS_DEFAULT_MAP["Viet Nam"] = "Vietnam"
NATIONS_DEFAULT_MAP["Yemen"] = "Yemen"
NATIONS_DEFAULT_MAP["Peru"] = "Peru"
NATIONS_DEFAULT_MAP["Kuwait"] = "Kuwait"
NATIONS_DEFAULT_MAP["Sri Lanka"] = "Sri Lanka"
NATIONS_DEFAULT_MAP["Lanka"] = "Sri Lanka"
NATIONS_DEFAULT_MAP["Kazakhstan"] = "Kazakhstan"
NATIONS_DEFAULT_MAP["Mongolia"] = "Mongolia"
NATIONS_DEFAULT_MAP["United Arab Emirates"] = "United Arab Emirates"
NATIONS_DEFAULT_MAP["Emirates"] = "United Arab Emirates"
NATIONS_DEFAULT_MAP["Malaysia"] = "Malaysia"
NATIONS_DEFAULT_MAP["Qatar"] = "Qatar"
NATIONS_DEFAULT_MAP["Kyrgyz Republic"] = "Kyrgyz Republic"
NATIONS_DEFAULT_MAP["Jordan"] = "Jordan"
## cities #############
NATIONS_DEFAULT_MAP['Belgrade'] = 'Serbia'
NATIONS_DEFAULT_MAP['Istanbul'] = 'Turkey'
NATIONS_DEFAULT_MAP['Ankara'] = 'Turkey'
NATIONS_DEFAULT_MAP['Rome'] = 'Italy'


def find_nation(affiliation):
    possible_affs = []
    result = []

    def _sublistExists(list1, list2):
        return ''.join(map(str, list2)) in ''.join(map(str, list1))

    values = set([y.lower().strip() for y in re.findall(ur"[\w']+", affiliation.replace('.',''), re.UNICODE)])
    for key, val in NATIONS_DEFAULT_MAP.iteritems():
        key_parts = set(key.lower().decode('utf-8').split())
        if key_parts.issubset(values):
            possible_affs.append(val)
            values = values.difference(key_parts)

    if not possible_affs:
        possible_affs = ['HUMAN CHECK']
    if 'CERN' in possible_affs and 'Switzerland' in possible_affs:
        # Don't use remove in case of multiple Switzerlands
        possible_affs = [x for x in possible_affs
                         if x != 'Switzerland']

    result.extend(possible_affs)

    result = sorted(list(set(result)))

    return result[0]
