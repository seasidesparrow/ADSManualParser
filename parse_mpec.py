import json
from adsingestp.parsers.datacite import DataciteParser
from adsmanparse.translator import Translator
from pyingest.serializers.classic import Tagged

infile = "/Users/mtempleton/mpec/MPEC2023-C14-NewObject.xml"
# infile = "/Users/mtempleton/mpec/MPEC2023-C19-DAILYORBITUPDATE.xml"

try:
    with open(infile, 'rb') as fh:
        rawData = fh.read()
    parser = DataciteParser()
    ingestRecord = parser.parse(rawData)
    print(json.dumps(ingestRecord, indent=2))
    xlator = Translator(data=ingestRecord)
    xlator.translate(bibstem='MPEC')
except Exception as err:
    print('There was a problem: %s' % err)
else:
    lol = Tagged()
    lol.write(xlator.output)
#   print(json.dumps(ingestRecord, indent=2))
