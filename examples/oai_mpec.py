import os
import json
from adsingestp.parsers.datacite import DataciteParser
from adsmanparse.translator import Translator
from adsmanparse.classic_serializer import ClassicSerializer
from glob import glob

inputFiles = glob('/proj/ads/abstracts/sources/DataCite/doi/10.48377/mpec/*')

for f in inputFiles:
    try:
        with open(f, 'rb') as fh:
            rawData = fh.read()
        parser = DataciteParser()
        ingestRecord = parser.parse(rawData)
        xlator = Translator(data=ingestRecord)
        xlator.translate(bibstem='MPEC')
    except Exception as err:
        print('There was a problem with %s: %s' % (f, err))
    else:
        try:
            lol = ClassicSerializer()
            with open('mpec.tagged','a') as fout:
                fout.write(lol.output(xlator.output))
        except Exception as err:
            print('failed to write tagged output for %s: %s' % (f, err))


fout.close()
