# -*- coding: utf-8 -*-

"""scoap3 base Invenio configuration."""

from __future__ import absolute_import, print_function


# Identity function for string extraction
def _(x):
    return x

# Default language and timezone
BABEL_DEFAULT_LANGUAGE = 'en'
BABEL_DEFAULT_TIMEZONE = 'Europe/Zurich'
I18N_LANGUAGES = [
]

HEADER_TEMPLATE = "scoap3_theme/header.html"
BASE_TEMPLATE = "scoap3_theme/page.html"
COVER_TEMPLATE = "invenio_theme/page_cover.html"
SETTINGS_TEMPLATE = "invenio_theme/settings/content.html"

# WARNING: Do not share the secret key - especially do not commit it to
# version control.
SECRET_KEY = "5EeAQcsqST1J6U7dTlQsBsJMcAuMgqdbfvut9YoDw75fRTlnQ7OtMcNcfp4OzOtQUUsVFWThN5YmJ023XzKHOMcMZIEblxgyoMSkyP5rcnlBCQ4yJOCBsXxmn13RxcK7yQ7U996ey59zce1i47VoVTyk1wwOKJocafnyOk4HfcE3Xx2IxKQYk8EXWtPVlndmVZZuba9kivA73QfWB9uxumFd8wtMhLm6quRa8KB9eqywNyCwcz6DHGYQzRKKvtgo"

# Theme
THEME_SITENAME = _("scoap3")
ASSETS_DEBUG = True
COLLECT_STORAGE = "flask_collect.storage.link"

# Inspire subject translation
# ===========================
ARXIV_TO_INSPIRE_CATEGORY_MAPPING = {
    "alg-geom": "Math and Math Physics",
    "astro-ph": "Astrophysics",
    "astro-ph.CO": "Astrophysics",
    "astro-ph.EP": "Astrophysics",
    "astro-ph.GA": "Astrophysics",
    "astro-ph.HE": "Astrophysics",
    "astro-ph.IM": "Instrumentation",
    "astro-ph.SR": "Astrophysics",
    "cond-mat": "General Physics",
    "cond-mat.dis-nn": "General Physics",
    "cond-mat.mes-hall": "General Physics",
    "cond-mat.mtrl-sci": "General Physics",
    "cond-mat.other": "General Physics",
    "cond-mat.quant-gas": "General Physics",
    "cond-mat.soft": "General Physics",
    "cond-mat.stat-mech": "General Physics",
    "cond-mat.str-el": "General Physics",
    "cond-mat.supr-con": "General Physics",
    "cs": "Computing",
    "cs.AI": "Computing",
    "cs.AR": "Computing",
    "cs.CC": "Computing",
    "cs.CE": "Computing",
    "cs.CG": "Computing",
    "cs.CL": "Computing",
    "cs.CR": "Computing",
    "cs.CV": "Computing",
    "cs.CY": "Computing",
    "cs.DB": "Computing",
    "cs.DC": "Computing",
    "cs.DL": "Computing",
    "cs.DM": "Computing",
    "cs.DS": "Computing",
    "cs.ET": "Computing",
    "cs.FL": "Computing",
    "cs.GL": "Computing",
    "cs.GR": "Computing",
    "cs.GT": "Computing",
    "cs.HC": "Computing",
    "cs.IR": "Computing",
    "cs.IT": "Computing",
    "cs.LG": "Computing",
    "cs.LO": "Computing",
    "cs.MA": "Computing",
    "cs.MM": "Computing",
    "cs.MS": "Computing",
    "cs.NA": "Computing",
    "cs.NE": "Computing",
    "cs.NI": "Computing",
    "cs.OH": "Computing",
    "cs.OS": "Computing",
    "cs.PF": "Computing",
    "cs.PL": "Computing",
    "cs.RO": "Computing",
    "cs.SC": "Computing",
    "cs.SD": "Computing",
    "cs.SE": "Computing",
    "cs.SI": "Computing",
    "cs.SY": "Computing",
    "dg-ga": "Math and Math Physics",
    "gr-qc": "Gravitation and Cosmology",
    "hep-ex": "Experiment-HEP",
    "hep-lat": "Lattice",
    "hep-ph": "Phenomenology-HEP",
    "hep-th": "Theory-HEP",
    "math": "Math and Math Physics",
    "math-ph": "Math and Math Physics",
    "math.AC": "Math and Math Physics",
    "math.AG": "Math and Math Physics",
    "math.AP": "Math and Math Physics",
    "math.AT": "Math and Math Physics",
    "math.CA": "Math and Math Physics",
    "math.CO": "Math and Math Physics",
    "math.CT": "Math and Math Physics",
    "math.CV": "Math and Math Physics",
    "math.DG": "Math and Math Physics",
    "math.DS": "Math and Math Physics",
    "math.FA": "Math and Math Physics",
    "math.GM": "Math and Math Physics",
    "math.GN": "Math and Math Physics",
    "math.GR": "Math and Math Physics",
    "math.GT": "Math and Math Physics",
    "math.HO": "Math and Math Physics",
    "math.IT": "Math and Math Physics",
    "math.KT": "Math and Math Physics",
    "math.LO": "Math and Math Physics",
    "math.MG": "Math and Math Physics",
    "math.MP": "Math and Math Physics",
    "math.NA": "Math and Math Physics",
    "math.NT": "Math and Math Physics",
    "math.OA": "Math and Math Physics",
    "math.OC": "Math and Math Physics",
    "math.PR": "Math and Math Physics",
    "math.QA": "Math and Math Physics",
    "math.RA": "Math and Math Physics",
    "math.RT": "Math and Math Physics",
    "math.SG": "Math and Math Physics",
    "math.SP": "Math and Math Physics",
    "math.ST": "Math and Math Physics",
    "nlin": "General Physics",
    "nlin.AO": "General Physics",
    "nlin.CD": "General Physics",
    "nlin.CG": "General Physics",
    "nlin.PS": "Math and Math Physics",
    "nlin.SI": "Math and Math Physics",
    "nucl-ex": "Experiment-Nucl",
    "nucl-th": "Theory-Nucl",
    "patt-sol": "Math and Math Physics",
    "physics": "General Physics",
    "physics.acc-ph": "Accelerators",
    "physics.ao-ph": "General Physics",
    "physics.atm-clus": "General Physics",
    "physics.atom-ph": "General Physics",
    "physics.bio-ph": "Other",
    "physics.chem-ph": "Other",
    "physics.class-ph": "General Physics",
    "physics.comp-ph": "Computing",
    "physics.data-an": "Computing",
    "physics.ed-ph": "Other",
    "physics.flu-dyn": "General Physics",
    "physics.gen-ph": "General Physics",
    "physics.geo-ph": "General Physics",
    "physics.hist-ph": "Other",
    "physics.ins-det": "Instrumentation",
    "physics.med-ph": "Other",
    "physics.optics": "General Physics",
    "physics.plasm-ph": "General Physics",
    "physics.pop-ph": "Other",
    "physics.soc-ph": "Other",
    "physics.space-ph": "Astrophysics",
    "q-alg": "Math and Math Physics",
    "q-bio.BM": "Other",
    "q-bio.CB": "Other",
    "q-bio.GN": "Other",
    "q-bio.MN": "Other",
    "q-bio.NC": "Other",
    "q-bio.OT": "Other",
    "q-bio.PE": "Other",
    "q-bio.QM": "Other",
    "q-bio.SC": "Other",
    "q-bio.TO": "Other",
    "q-fin.CP": "Other",
    "q-fin.EC": "Other",
    "q-fin.GN": "Other",
    "q-fin.MF": "Other",
    "q-fin.PM": "Other",
    "q-fin.PR": "Other",
    "q-fin.RM": "Other",
    "q-fin.ST": "Other",
    "q-fin.TR": "Other",
    "quant-ph": "General Physics",
    "solv-int": "Math and Math Physics",
    "stat.AP": "Other",
    "stat.CO": "Other",
    "stat.ME": "Other",
    "stat.ML": "Other",
    "stat.OT": "Other",
    "stat.TH": "Other"
}

# Inspire mappings
# ================

INSPIRE_CATEGORIES = [
    'Accelerators',
    'Astrophysics',
    'Computing',
    'Experiment-HEP',
    'Experiment-Nucl',
    'General Physics',
    'Gravitation and Cosmology',
    'Instrumentation',
    'Lattice',
    'Math and Math Physics',
    'Other',
    'Phenomenology-HEP',
    'Theory-HEP',
    'Theory-Nucl'
]

INSPIRE_DEGREE_TYPES = [
    'Bachelor',
    'Diploma',
    'Habilitation',
    'Laurea',
    'Master',
    'PhD',
    'Thesis'
]

INSPIRE_LICENSE_TYPES = [
    'CC-BY',
    'CC-BY-NC',
    'CC-BY-NC-ND',
    'CC-BY-NC-SA',
    'CC-BY-ND',
    'CC-BY-SA',
    'Other'
]

INSPIRE_RANK_TYPES = {
    'STAFF': {},
    'SENIOR': {},
    'JUNIOR': {},
    'VISITOR': {
        'alternative_names': ['VISITING SCIENTIST'],
    },
    'POSTDOC': {
        'abbreviations': ['PD']
    },
    'PHD': {
        'alternative_names': ['STUDENT']
    },
    'MASTER': {
        'abbreviations': ['MAS', 'MS', 'MSC']
    },
    'UNDERGRADUATE': {
        'alternative_names': ['BACHELOR'],
        'abbreviations': ['UG', 'BS', 'BA', 'BSC']
    }
}
