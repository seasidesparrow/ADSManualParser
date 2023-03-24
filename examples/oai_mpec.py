import os
import json
from adsingestp.parsers.datacite import DataciteParser
from adsmanparse.translator import Translator
from glob import glob
from pyingest.serializers.classic import Tagged

inputFiles = glob('/proj/ads/adstmp/mtemple/mpec_oai_harvester/doi/10.48377/mpec/*')

fout = open('mpec.tagged','a')
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
            lol = Tagged()
            lol.write(xlator.output, fout)
        except Exception as err:
            print('failed to write tagged output for %s: %s' % (f, err))


fout.close()
