import json
from adsingestp.parsers.datacite import DataciteParser
from adsmanparse.translator import Translator
from pyingest.serializers.classic import Tagged

infile = '/proj/ads/abstracts/sources/DataCite/doi/10.48377/mpec/2023-f01.xml'

try:
    with open(infile, 'rb') as fh:
        rawData = fh.read()
    parser = DataciteParser()
    ingestRecord = parser.parse(rawData)
    xlator = Translator(data=ingestRecord)
    xlator.translate(bibstem='MPEC')
except Exception as err:
    print('There was a problem: %s' % err)
else:
    lol = Tagged()
    lol.write(xlator.output)
    print(json.dumps(ingestRecord, indent=2))
