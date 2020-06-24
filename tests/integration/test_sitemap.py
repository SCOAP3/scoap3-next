from flask import current_app
from lxml import etree

from scoap3.modules.sitemap.tasks import update_sitemap_cache


def test_sitemap(app_client, test_record):
    # run sitemap generation
    update_sitemap_cache()

    servername = current_app.config.get('SERVER_NAME')

    # check base sitemap
    response = app_client.get('/sitemap.xml')
    expected_sitemap = ('<?xml version="1.0" encoding="UTF-8"?>\n<sitemapindex xmlns="http://www.sitemaps.org/schemas/s'
                        'itemap/0.9">\n  <sitemap>\n    <loc>http://%s/sitemap1.xml</loc>\n  </sitemap>\n</'
                        'sitemapindex>' % servername)
    assert expected_sitemap == response.data

    # check if sitemap 1 contains the test record
    response_1 = app_client.get('/sitemap1.xml')
    xml_1 = etree.fromstring(response_1.data)
    locations = xml_1.xpath('//s:loc/text()', namespaces={'s': 'http://www.sitemaps.org/schemas/sitemap/0.9'})

    expected_location = 'http://%s/records/%s' % (servername, test_record.get('control_number'))
    assert expected_location in locations
