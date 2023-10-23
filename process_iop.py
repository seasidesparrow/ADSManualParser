import argparse
import json
import os
from adsmanparse import translator, doiharvest
from adsingestp.parsers.crossref import CrossrefParser
from adsingestp.parsers.jats import JATSParser
from adsingestp.parsers.datacite import DataciteParser
from adsingestp.parsers.elsevier import ElsevierParser
from adsputils import setup_logging
from datetime import datetime, timedelta
from glob import iglob
from pyingest.serializers.classic import Tagged

PARSER_TYPES = {'jats': JATSParser(),
                'dc': DataciteParser(),
                'cr': CrossrefParser(),
                'nlm': JATSParser(),
                'elsevier': ElsevierParser()
               }

logger = setup_logging('manual-parser')

IOP_CONFIG = {"type": "jats",
              "ref_ext": ".iopft.xml",
              "raw_data_base": "/proj/ads/adstmp/mtemple/data/IOPP/",

def main():

    rawDataList = []
    ingestDocList = []

    proc_path = IOP_CONFIG.get("raw_data_base", "./")+"2023-10-21"

    output_file = IOP_CONFIG.get("raw_data_base", "./")+"output.tag"

    # This route processes data from user-input files
    infiles = iglob(proc_path, recursive=True)
    if infiles:
        dtime = timedelta(days=365)
        today = datetime.today()
        infiles_since = [x for x in infiles if ((today - datetime.fromtimestamp(os.path.getmtime(x))) <= dtime)]
            infiles = infiles_since
        for f in infiles:
            try:
                with open(f, 'r') as fin:
                    output = {'data': fin.read(),
                              'name': f,
                              'type': IOP_CONFIG.get("type", "jats")}
                    rawDataList.append(output)
            except Exception as err:
                logger.warning("Failed to import %s: %s" % (f, err))

    # Now process whatever raw records you have
    for rec in rawDataList:
        pdata = rec.get('data', None)
        ptype = rec.get('type', None)
        filename = rec.get('name', None)
        parser = PARSER_TYPES.get(ptype, None)
        if parser:
            try:
                parser.__init__()
                if ptype == 'nlm':
                    ingestDocList.append(parser.parse(pdata, bsparser='lxml-xml'))
                else:
                    ingestDocList.append(parser.parse(pdata))
            except Exception as err:
                logger.warning("Error parsing record (%s): %s" % (filename,err))
        else:
            logger.error("No parser available for file_type '%s'." % ptype)


    if ingestDocList:
        if output_file:
            x = Tagged()
            with open(output_file, 'a') as fout:
                for d in ingestDocList:
                    try:
                        xlator = translator.Translator()
                        xlator.translate(data=d)
                        x.write(xlator.output, fout)
                    except Exception as err:
                        logger.warning("Export to tagged file failed: %s\t%s" % (err, d))


if __name__ == '__main__':
    main()
