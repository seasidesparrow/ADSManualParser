import os
import json
from adsingestp.parsers.arxiv import ArxivParser
from adsmanparse.translator import Translator
from adsmanparse.classic_serializer import ClassicSerializer
from glob import glob

inputFiles = glob('/proj/ads_abstracts/sources/PoS/oai/pos.sissa.it/ECRS/*')

fout = open('pos.tagged','a')
for f in inputFiles:
    try:
        with open(f, 'rb') as fh:
            rawData = fh.read()
        parser = ArxivParser()
        ingestRecord = parser.parse(rawData)
        xlator = Translator(data=ingestRecord)
        xlator.translate(bibstem='fnord')
    except Exception as err:
        print('There was a problem with %s: %s' % (f, err))
    else:
        try:
            lol = ClassicSerializer()
            with open('pos.tagged', 'a') as fout:
                fout.write(lol.output(xlator.output))
        except Exception as err:
            print('failed to write tagged output for %s: %s' % (f, err))


fout.close()
