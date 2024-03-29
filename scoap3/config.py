# -*- coding: utf-8 -*-

"""scoap3 base Invenio configuration."""

from __future__ import absolute_import, print_function

import os
from collections import OrderedDict
from datetime import datetime, timedelta
from logging.config import dictConfig

from invenio_records_rest.facets import terms_filter, range_filter

from scoap3.modules.search.utils import Scoap3RecordsSearch, terms_filter_with_must
from scoap3.modules.tools.tools import (
    affiliations_export,
    authors_export,
    search_export,
)


# Identity function for string extraction
def _(x):
    return x


# Default language and timezone
BABEL_DEFAULT_LANGUAGE = "en"
BABEL_DEFAULT_TIMEZONE = "Europe/Zurich"
I18N_LANGUAGES = []

COVER_TEMPLATE = "invenio_theme/page_cover.html"
SERVER_NAME = "web:9000"

SECURITY_REGISTERABLE = False
SECURITY_LOGIN_USER_TEMPLATE = "scoap3_theme/login_user.html"

SECRET_KEY = "REPLACE_WITH_SECRET"

# Theme
THEME_SITENAME = _("SCOAP3 Repository")
THEME_LOGO = "img/logo.png"
SITE_URL = "repo.scoap3.org"

SEARCH_UI_SEARCH_TEMPLATE = "scoap3_search/search.html"
SEARCH_UI_JSTEMPLATE_RESULTS = "templates/scoap3_search/default.html"
SEARCH_UI_JSTEMPLATE_FACETS = "templates/scoap3_search/facets.html"
SEARCH_UI_SEARCH_INDEX = "scoap3-records-record"
SEARCH_UI_JSTEMPLATE_RANGE_FACET = "templates/scoap3_search/range.html"

BASE_TEMPLATE = "scoap3_theme/page.html"
ADMIN_BASE_TEMPLATE = "scoap3_theme/page_admin.html"
SETTINGS_TEMPLATE = "invenio_theme/page_settings.html"

# Elasticsearch
INDEXER_DEFAULT_INDEX = "scoap3-records-record"
INDEXER_DEFAULT_DOC_TYPE = "_doc"
SEARCH_ELASTIC_HOSTS = "localhost"
SEARCH_MAX_RESULT_WINDOW = 50000

RECORDS_REST_ENDPOINTS = dict(
    recid=dict(
        default_endpoint_prefix=True,
        pid_type="recid",
        pid_minter="scoap3_minter",
        pid_fetcher="recid",
        search_class=Scoap3RecordsSearch,
        search_index="scoap3-records-record",
        record_serializers={
            "application/json": (
                "invenio_records_rest.serializers" ":json_v1_response"
            ),
        },
        search_serializers={
            "application/json": ("invenio_records_rest.serializers" ":json_v1_search"),
        },
        list_route="/records/",
        item_route="/records/<pid(recid):pid_value>",
        default_media_type="application/json",
        max_result_window=SEARCH_MAX_RESULT_WINDOW,
        read_permission_factory_imp="scoap3.modules.records.permissions:record_read_permission_factory",
    ),
)
RECORDS_UI_ENDPOINTS = dict(
    recid=dict(
        pid_type="recid",
        route="/records/<pid_value>",
        template="scoap3_theme/records/detail.html",
    ),
)
RECORDS_UI_TOMBSTONE_TEMPLATE = "scoap3_theme/records/tombstone.html"
RECORDS_REST_SORT_OPTIONS = {
    "scoap3-records-record": {
        "date": {
            "title": "Most recent",
            "fields": ["date", "control_number"],
            "default_order": "desc",
            "order": 1,
        },
        "bestmatch": {
            "title": "Best match",
            "fields": ["_score"],
            "default_order": "desc",
            "order": 2,
        },
    },
}

#: Default sort for records REST API.
RECORDS_REST_DEFAULT_SORT = {
    "scoap3-records-record": {"query": "-date", "noquery": "-date"},
}

RECORDS_REST_FACETS = {
    "scoap3-records-record": {
        "filters": {
            "journal": terms_filter("publication_info.journal_title"),
            "country": terms_filter_with_must("authors.affiliations.country"),
            "collaboration": terms_filter("facet_collaboration"),
            "year": range_filter("year", format="yyyy", end_date_math="/y"),
        },
        "aggs": {
            "journal": {
                "terms": {
                    "field": "publication_info.journal_title",
                    "size": 20,
                    "order": {"_term": "asc"},
                }
            },
            "country": {
                "terms": {
                    "field": "authors.affiliations.country",
                    "size": 150,
                    "order": {"_term": "asc"},
                }
            },
            "collaboration": {"terms": {"field": "facet_collaboration", "size": 20}},
            "year": {
                "date_histogram": {
                    "field": "year",
                    "interval": "year",
                    "format": "yyyy",
                    "min_doc_count": 1,
                }
            },
        },
    }
}

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
    "stat.TH": "Other",
}

# Inspire mappings
# ================

INSPIRE_CATEGORIES = [
    "Accelerators",
    "Astrophysics",
    "Computing",
    "Experiment-HEP",
    "Experiment-Nucl",
    "General Physics",
    "Gravitation and Cosmology",
    "Instrumentation",
    "Lattice",
    "Math and Math Physics",
    "Other",
    "Phenomenology-HEP",
    "Theory-HEP",
    "Theory-Nucl",
]

INSPIRE_DEGREE_TYPES = [
    "Bachelor",
    "Diploma",
    "Habilitation",
    "Laurea",
    "Master",
    "PhD",
    "Thesis",
]

INSPIRE_LICENSE_TYPES = [
    "CC-BY",
    "CC-BY-NC",
    "CC-BY-NC-ND",
    "CC-BY-NC-SA",
    "CC-BY-ND",
    "CC-BY-SA",
    "Other",
]

INSPIRE_RANK_TYPES = {
    "STAFF": {},
    "SENIOR": {},
    "JUNIOR": {},
    "VISITOR": {
        "alternative_names": ["VISITING SCIENTIST"],
    },
    "POSTDOC": {"abbreviations": ["PD"]},
    "PHD": {"alternative_names": ["STUDENT"]},
    "MASTER": {"abbreviations": ["MAS", "MS", "MSC"]},
    "UNDERGRADUATE": {
        "alternative_names": ["BACHELOR"],
        "abbreviations": ["UG", "BS", "BA", "BSC"],
    },
}


###############################################################################
# Home page
###############################################################################

# Display a homepage.
FRONTPAGE_ENDPOINT = "scoap3_frontpage.index"

# Static file
COLLECT_STORAGE = "flask_collect.storage.link"

# Workflows
WORKFLOWS_UI_URL = "/harvesting"
WORKFLOWS_UI_API_URL = "/api/harvesting/"

WORKFLOWS_UI_DATA_TYPES = dict(
    harvesting=dict(
        search_index="scoap3-workflows-harvesting",
        search_type="_doc",
    ),
)
SQLALCHEMY_DATABASE_URI = "postgresql+psycopg2://scoap3:dbpass123@localhost:5432/scoap3"
WORKFLOWS_UI_INDEX_TEMPLATE = "scoap3_workflows/index.html"
WORKFLOWS_UI_LIST_TEMPLATE = "scoap3_workflows/list.html"
WORKFLOWS_UI_DETAILS_TEMPLATE = "scoap3_workflows/details.html"

WORKFLOWS_UI_JSTEMPLATE_RESULTS = "templates/scoap3_workflows_ui/results.html"

WORKFLOWS_UI_REST_ENDPOINT = dict(
    workflow_object_serializers={
        "application/json": ("invenio_workflows_ui.serializers" ":json_serializer"),
    },
    search_serializers={
        "application/json": (
            "invenio_workflows_ui.serializers" ":json_search_serializer"
        ),
    },
    action_serializers={
        "application/json": (
            "invenio_workflows_ui.serializers" ":json_action_serializer"
        ),
    },
    bulk_action_serializers={
        "application/json": (
            "invenio_workflows_ui.serializers" ":json_action_serializer"
        ),
    },
    file_serializers={
        "application/json": (
            "invenio_workflows_ui.serializers" ":json_file_serializer"
        ),
    },
    list_route="/harvesting/",
    item_route="/harvesting/<object_id>",
    file_list_route="/harvesting/<object_id>/files",
    file_item_route="/harvesting/<object_id>/files/<path:key>",
    search_index="scoap3-workflows-harvesting",
    default_media_type="application/json",
    max_result_window=SEARCH_MAX_RESULT_WINDOW,
)

WORKFLOWS_UI_REST_SORT_OPTIONS = {
    "workflows": {
        "mostrecent": {
            "title": "Most recent",
            "fields": ["_updated"],
            "default_order": "desc",
            "order": 1,
        },
        "workflowid": {
            "title": "Workflow ID",
            "fields": ["id"],
            "default_order": "desc",
            "order": 2,
        },
    },
}

WORKFLOWS_UI_REST_DEFAULT_SORT = {
    "workflows": {"query": "mostrecent", "noquery": "-workflowid"}
}

WORKFLOWS_UI_REST_FACETS = {
    "workflows": {
        "filters": {
            "status": terms_filter("_workflow.status"),
            "journal": terms_filter("journal_title_facet"),
            "workflow_name": terms_filter("_workflow.workflow_name"),
        },
        "aggs": {
            "status": {"terms": {"field": "_workflow.status", "size": 20}},
            "journal": {"terms": {"field": "journal_title_facet", "size": 20}},
            "workflow_name": {
                "terms": {"field": "_workflow.workflow_name", "size": 20}
            },
        },
    }
}

WORKFLOWS_STORAGEDIR = "/tmp/workflows-harvesting"

ARTICLE_UPLOAD_SEND_HALTED_EMAILS = True
"""
If True an email will be send if an article_upload workflow gets halted.
"""

CRAWLER_DATA_TYPE = "harvesting"
SCRAPY_FEED_URI = "/eos/project/s/scoap3repo/scrapy_feed.json"

OAISERVER_RECORD_INDEX = "scoap3-records-record"
#: OAI identifier prefix
OAISERVER_ID_PREFIX = "oai:repo.scoap3.org:"
#: Managed OAI identifier prefixes
OAISERVER_MANAGED_ID_PREFIXES = [OAISERVER_ID_PREFIX]
#: Number of records to return per page in OAI-PMH results.
OAISERVER_PAGE_SIZE = 100
#: Resumption token expire time in seconds.
OAISERVER_RESUMPTION_TOKEN_EXPIRE_TIME = 60 * 60 * 24
#: PIDStore fetcher for OAI ID control numbers
OAISERVER_CONTROL_NUMBER_FETCHER = "scoap3_fetcher"
#: Support email for OAI-PMH.
OAISERVER_ADMIN_EMAILS = ["scoap3repo.admin@cern.ch"]
#: Do not register signals to automatically update records on updates.
OAISERVER_REGISTER_RECORD_SIGNALS = False
#: Do not register signals to automatically update records on oaiset updates.
OAISERVER_REGISTER_OAISET_SIGNALS = False

OAISERVER_METADATA_FORMATS = {
    "oai_dc": {
        "namespace": "http://www.openarchives.org/OAI/2.0/oai_dc/",
        "serializer": (
            "invenio_oaiserver.utils:dumps_etree",
            {
                "xslt_filename": "/usr/var/scoap3-instance/static/xsl/MARC21slim2OAIDC.xsl"
            },
        ),
        "schema": "http://www.openarchives.org/OAI/2.0/oai_dc.xsd",
    },
    "marc21": {
        "namespace": "http://www.loc.gov/MARC21/slim",
        "serializer": (
            "scoap3.modules.records.oai_serializer:dumps_etree",
            {"prefix": "marc"},
        ),
        "schema": "http://www.loc.gov/standards/marcxml/schema/MARC21slim.xsd",
    },
}

# Invenio Logging config
LOGGING_SENTRY_CLASS = "invenio_logging.sentry6.Sentry6"
dictConfig(
    {
        "version": 1,
        "formatters": {
            "default": {
                "format": "[%(asctime)s: %(levelname)s/%(processName)s] %(name)s: %(message)s",
            }
        },
        "handlers": {
            "stdout_handler": {
                "class": "logging.StreamHandler",
                "formatter": "default",
            }
        },
        "loggers": {
            "scoap3": {
                "level": "INFO",
                "handlers": ["stdout_handler"],
                "propagate": False,
            },
        },
    }
)


JSONSCHEMAS_HOST = "localhost:5000"
JSONSCHEMAS_REPLACE_REFS = False

MAIL_SUPPRESS_SEND = True  # only log email in local environment
MAIL_DEFAULT_SENDER = "repo.admin@scoap3.org"
ADMIN_DEFAULT_EMAILS = [
    "scoap3repo.admin@cern.ch",
]
OPERATIONS_EMAILS = [
    "scoap3repo.admin@cern.ch",
]
CROSSREF_API_URL = "https://api.crossref.org/works/"

#  Abbreviations
PUBLISHER_ABBREVIATIONS = {
    "Jagiellonian University": "Jagiellonian Uni.",
    "Hindawi Publishing Corporation": "Hindawi",
    "Institute of Physics Publishing/Chinese Academy of Sciences": "IOP",
    "Institute of Physics Publishing/SISSA": "IOP",
    "Institute of Physics Publishing/Deutsche Physikalische Gesellschaft": "IOP",
    "Springer/SISSA": "Springer",
    "Springer/Societ\xe0 Italiana di Fisica": "Springer",
    "Elsevier": "Elsevier",
    "American Physical Society": "APS",
    "Oxford University Press/Physical Society of Japan": "OUP",
}

JOURNAL_ABBREVIATIONS = {
    "Acta Physica Polonica B": "APPB",
    "Advances in High Energy Physics": "AHEP",
    "Chinese Physics C": "CPC",
    "European Physical Journal C": "EPJC",
    "Journal of Cosmology and Astroparticle Physics": "JCAP",
    "Journal of High Energy Physics": "JHEP",
    "New Journal of Physics": "NJP",
    "Nuclear Physics B": "NPB",
    "Physics Letters B": "PLB",
    "Physical Review C": "PRC",
    "Physical Review D": "PRD",
    "Physical Review Letters": "PRL",
    "Progress of Theoretical and Experimental Physics": "PTEP",
}

ARTICLE_CHECK_JOURNALS = {
    "Acta Physica Polonica B": (datetime(2014, 1, 1), None),
    "Advances in High Energy Physics": (datetime(2014, 1, 1), None),
    "Chinese Physics C": (datetime(2014, 1, 1), None),
    "The European Physical Journal C": (datetime(2014, 1, 1), None),
    "Journal of High Energy Physics": (datetime(2014, 1, 1), None),
    "Nuclear Physics B": (datetime(2014, 1, 1), None),
    "Physics Letters B": (datetime(2014, 1, 1), None),
    "Physical Review C": (datetime(2018, 1, 1), None),
    "Physical Review D": (datetime(2018, 1, 1), None),
    "Physical Review Letters": (datetime(2018, 1, 1), None),
    "Progress of Theoretical and Experimental Physics": (datetime(2014, 1, 1), None),
}
"""Settings for the automatic journal check.
Key has to be the name of the journal (used as a filter on crossref),
the value has to be a (start_date, end_date) tuple, which will be used as a publication date filter.
"""

ARTICLE_CHECK_DEFAULT_TIME_DELTA = timedelta(days=14)
"""Representing the timedelta used to determine the starting date for the check."""

ARTICLE_CHECK_HAS_TO_BE_HEP = (
    "Acta Physica Polonica B",
    "Advances in High Energy Physics",
    "Chinese Physics C",
    "Physical Review C",
    "Physical Review D",
    "Physical Review Letters",
    "Progress of Theoretical and Experimental Physics",
)
"""
List of journals in which articles need to have 'hep-*' primary arXiv category.
Used in the article and compliance checks.
"""

ARTICLE_CHECK_IGNORE_TIME = timedelta(hours=48)
"""An article will only be considered missing if it was published at least ARTICLE_CHECK_IGNORE_TIME ago."""

COMPLIANCE_JOURNAL_FILES = {
    "Acta Physica Polonica B": {"pdf", "pdf/a"},
    "Advances in High Energy Physics": {"pdf", "pdf/a", "xml"},
    "Chinese Physics C": {"pdf", "xml"},
    "The European Physical Journal C": {"pdf/a", "xml"},
    "Journal of High Energy Physics": {"pdf/a", "xml"},
    "Nuclear Physics B": {"pdf", "pdf/a", "xml"},
    "Physics Letters B": {"pdf", "pdf/a", "xml"},
    "Physical Review C": {"pdf", "xml"},
    "Physical Review D": {"pdf", "xml"},
    "Physical Review Letters": {"pdf", "xml"},
    "Progress of Theoretical and Experimental Physics": {"pdf", "pdf/a", "xml"},
}
"""
Required file types for journals. This is validated in the compliance check.
The articles are required to have *exactly* these files.
"""

COMPLIANCE_SEND_FAILED_EMAILS = True
"""
If true an email will be sent every time a compliance check doesn't pass.
"""

PARTNER_COUNTRIES = [
    "Australia",
    "Austria",
    "Belgium",
    "Canada",
    "China",
    "CERN",
    "Czech Republic",
    "Denmark",
    "Finland",
    "France",
    "Germany",
    "Greece",
    "Hong-Kong",
    "Hungary",
    "Iceland",
    "Israel",
    "Italy",
    "Japan",
    "JINR",
    "South Korea",
    "Mexico",
    "Netherlands",
    "Norway",
    "Poland",
    "Portugal",
    "Slovak Republic",
    "South Africa",
    "Spain",
    "Sweden",
    "Switzerland",
    "Taiwan",
    "Turkey",
    "United Kingdom",
    "United States",
]


COUNTRIES_DEFAULT_MAPPING = OrderedDict(
    [
        ("INFN", "Italy"),
        ("Democratic People's Republic of Korea", "North Korea"),
        ("DPR Korea", "North Korea"),
        ("DPR. Korea", "North Korea"),
        ("CERN", "CERN"),
        ("European Organization for Nuclear Research", "CERN"),
        ("KEK", "Japan"),
        ("DESY", "Germany"),
        ("FERMILAB", "USA"),
        ("FNAL", "USA"),
        ("SLACK", "USA"),
        ("Stanford Linear Accelerator Center", "USA"),
        ("Joint Institute for Nuclear Research", "JINR"),
        ("JINR", "JINR"),
        ("Northern Cyprus", "Turkey"),
        ("North Cyprus", "Turkey"),
        ("New Mexico", "USA"),
        ("South China Normal University", "China"),
        ("Hong Kong China", "Hong Kong"),
        ("Hong-Kong China", "Hong Kong"),
        ("Hong Kong, China", "Hong Kong"),
        ("Hong Kong", "Hong Kong"),
        ("Hong-Kong", "Hong Kong"),
        ("Algeria", "Algeria"),
        ("Argentina", "Argentina"),
        ("Armenia", "Armenia"),
        ("Australia", "Australia"),
        ("Austria", "Austria"),
        ("Azerbaijan", "Azerbaijan"),
        ("Belarus", "Belarus"),
        ("Belgium", "Belgium"),
        ("Belgique", "Belgium"),
        ("Bangladesh", "Bangladesh"),
        ("Brazil", "Brazil"),
        ("Brasil", "Brazil"),
        ("Benin", "Benin"),
        (u"Bénin", "Benin"),
        ("Bulgaria", "Bulgaria"),
        ("Bosnia and Herzegovina", "Bosnia and Herzegovina"),
        ("Canada", "Canada"),
        ("Chile", "Chile"),
        ("ROC", "Taiwan"),
        ("R.O.C", "Taiwan"),
        ("Republic of China", "Taiwan"),
        ("China (PRC)", "China"),
        ("PR China", "China"),
        ("China", "China"),
        ("People's Republic of China", "China"),
        ("Republic of China", "China"),
        ("Colombia", "Colombia"),
        ("Costa Rica", "Costa Rica"),
        ("Cuba", "Cuba"),
        ("Croatia", "Croatia"),
        ("Cyprus", "Cyprus"),
        ("Czech Republic", "Czech Republic"),
        ("Czech", "Czech Republic"),
        ("Czechia", "Czech Republic"),
        ("Denmark", "Denmark"),
        ("Egypt", "Egypt"),
        ("Estonia", "Estonia"),
        ("Ecuador", "Ecuador"),
        ("Finland", "Finland"),
        ("France", "France"),
        ("Germany", "Germany"),
        ("Deutschland", "Germany"),
        ("Greece", "Greece"),
        ("Hungary", "Hungary"),
        ("Iceland", "Iceland"),
        ("India", "India"),
        ("Indonesia", "Indonesia"),
        ("Iran", "Iran"),
        ("Ireland", "Ireland"),
        ("Israel", "Israel"),
        ("Italy", "Italy"),
        ("Italia", "Italy"),
        ("Japan", "Japan"),
        ("Jamaica", "Jamaica"),
        ("Korea", "South Korea"),
        ("Republic of Korea", "South Korea"),
        ("South Korea", "South Korea"),
        ("Latvia", "Latvia"),
        ("Lebanon", "Lebanon"),
        ("Lithuania", "Lithuania"),
        ("Luxembourg", "Luxembourg"),
        ("Macedonia", "Macedonia"),
        ("Mexico", "Mexico"),
        (u"México", "Mexico"),
        ("Monaco", "Monaco"),
        ("Montenegro", "Montenegro"),
        ("Morocco", "Morocco"),
        ("Niger", "Niger"),
        ("Nigeria", "Nigeria"),
        ("Netherlands", "Netherlands"),
        ("The Netherlands", "Netherlands"),
        ("New Zealand", "New Zealand"),
        ("Zealand", "New Zealand"),
        ("Norway", "Norway"),
        ("Oman", "Oman"),
        ("Sultanate of Oman", "Oman"),
        ("Pakistan", "Pakistan"),
        ("Panama", "Panama"),
        ("Philipines", "Philipines"),
        ("Poland", "Poland"),
        ("Portugalo", "Portugal"),
        ("Portugal", "Portugal"),
        ("P.R.China", "China"),
        (u"People’s Republic of China", "China"),
        ("Republic of Belarus", "Belarus"),
        ("Republic of Benin", "Benin"),
        ("Republic of Korea", "South Korea"),
        ("Republic of San Marino", "San Marino"),
        ("Republic of South Africa", "South Africa"),
        ("Romania", "Romania"),
        ("Russia", "Russia"),
        ("Russian Federation", "Russia"),
        ("Saudi Arabia", "Saudi Arabia"),
        ("Kingdom of Saudi Arabia", "Saudi Arabia"),
        ("Arabia", "Saudi Arabia"),
        ("Serbia", "Serbia"),
        ("Singapore", "Singapore"),
        ("Slovak Republic", "Slovakia"),
        ("Slovak", "Slovakia"),
        ("Slovakia", "Slovakia"),
        ("Slovenia", "Slovenia"),
        ("South Africa", "South Africa"),
        ("Africa", "South Africa"),
        (u"España", "Spain"),
        ("Spain", "Spain"),
        ("Sudan", "Sudan"),
        ("Sweden", "Sweden"),
        ("Switzerland", "Switzerland"),
        ("Syria", "Syria"),
        ("Taiwan", "Taiwan"),
        ("Thailand", "Thailand"),
        ("Tunisia", "Tunisia"),
        ("Turkey", "Turkey"),
        ("Ukraine", "Ukraine"),
        ("United Kingdom", "UK"),
        ("Kingdom", "UK"),
        ("United Kingdom of Great Britain and Northern Ireland", "UK"),
        ("UK", "UK"),
        ("England", "UK"),
        ("Scotland", "UK"),
        ("Wales", "UK"),
        ("New South Wales", "Australia"),
        ("U.K", "UK"),
        ("United States of America", "USA"),
        ("United States", "USA"),
        ("USA", "USA"),
        ("U.S.A", "USA"),
        ("America", "USA"),
        ("Uruguay", "Uruguay"),
        ("Uzbekistan", "Uzbekistan"),
        ("Venezuela", "Venezuela"),
        ("Vietnam", "Vietnam"),
        ("Viet Nam", "Vietnam"),
        ("Yemen", "Yemen"),
        ("Peru", "Peru"),
        ("Kuwait", "Kuwait"),
        ("Sri Lanka", "Sri Lanka"),
        ("Lanka", "Sri Lanka"),
        ("Kazakhstan", "Kazakhstan"),
        ("Mongolia", "Mongolia"),
        ("United Arab Emirates", "United Arab Emirates"),
        ("Emirates", "United Arab Emirates"),
        ("Malaysia", "Malaysia"),
        ("Qatar", "Qatar"),
        ("Kyrgyz Republic", "Kyrgyz Republic"),
        ("Jordan", "Jordan"),
        ("Belgrade", "Serbia"),
        ("Istanbul", "Turkey"),
        ("Ankara", "Turkey"),
        ("Rome", "Italy"),
        ("Georgia", "Georgia"),
    ]
)

API_UNAUTHENTICATED_PAGE_LIMIT = 20

# GOOGLE API key. Value should come from secrets.
# Used to determine the country of affiliations.
GOOGLE_API_KEY = ""

ACCOUNTS_SETTINGS_TEMPLATE = "scoap3_accounts/settings.html"

ARXIV_HEP_CATEGORIES = {"hep-ex", "hep-lat", "hep-ph", "hep-th"}
DELETE_WORKFLOWS_OLDER_THEN_DAYS = 183

#: Files REST permission factory
FILES_REST_PERMISSION_FACTORY = (
    "scoap3.modules.records.permissions:files_permission_factory"
)

# ##################### Robotupload ############################
ROBOTUPLOAD_FOLDER = "/tmp/robotupload"
ROBOTUPLOAD_ALLOWED_USERS = {
    "127.0.0.1": ["ALL"],
}
"""IP addresses of users who can access the robotupload API as a dictionary.

Key is the ip or subnet, value is a list of journals or 'ALL' if all journals are allowed for the specified ip.
The name of the journal has to match the publication_info.journal_title field.
Example: {'127.0.0.1': ['ALL'], '127.0.0.0/16': ['ALL']}
"""

JOURNAL_PUBLISHER_MAPPING = {
    "Acta Physica Polonica B": "Jagiellonian University",
    "Chinese Physics C": "Institute of Physics Publishing/Chinese Academy of Sciences",
}

JOURNAL_TITLE_MAPPING = {"1674-1137": "Chinese Physics C"}

CLI_HARVEST_SLEEP_TIME = 0.5  # seconds
CLI_HARVEST_MAX_WAIT_TIME = 60  # seconds
CLI_HARVEST_MAX_RETRIES = 2

INSPIRE_LITERATURE_API_URL = "https://labs.inspirehep.net/api/literature"

SEARCH_EXPORT_FIELDS = (
    ("Publication year", "year", "year"),
    ("Control number", "control_number", "control_number"),
    ("DOI", "dois", "dois[0].value"),
    ("Title", "titles", "titles[0].title"),
    ("arXiv id", "arxiv_eprints", "arxiv_eprints[0].value"),
    ("arXiv primary category", "arxiv_eprints", "arxiv_eprints[0].categories[0]"),
    ("Publication date", "imprints", "imprints[0].date"),
    ("Record creation date", "record_creation_date", "record_creation_date"),
    ("Journal", "publication_info", "publication_info[0].journal_title"),
)
"""List of 3-tuples that describe the fields used for the serach export feature.

Elements are 3-tuples: (name, field, key)
 - name: human readable name. This will be displayed in the header of the exported csv.
 - field: metadata top-level field, which contains the information.
 - key: selector for the needed value.
"""

TOOL_FUNCTIONS = {
    "affiliations": affiliations_export,
    "authors": authors_export,
    "search": search_export,
}
"""Mapping tool names to evaluation functions"""

TOOL_ELASTICSEARCH_PAGE_SIZE = 100
"""Defines the page size for ES queries in tools."""

TOOL_COMPRESS_ATTACHMENT = True
"""If True, attachments sent via email will be compressed using gzip."""

SITEMAP_URL_SCHEME = "http"
"""URL scheme used for generating sitemap files."""

SITEMAP_MAX_URL_COUNT = 10000
"""Max URL count per sitemap page."""

S3_HOSTNAME = os.environ.get("AWS_S3_ENDPOINT")
S3_BUCKET = os.environ.get("AWS_S3_EMAIL_ATTACHMENT_BUCKET")
