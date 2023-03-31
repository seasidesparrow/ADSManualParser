import argparse
import json
from adsmanparse import translator, doiharvest
from adsingestp.parsers.crossref import CrossrefParser
from adsingestp.parsers.jats import JATSParser
from adsingestp.parsers.datacite import DataciteParser
from adsputils import setup_logging
from glob import iglob
from pyingest.serializers.classic import Tagged

PARSER_TYPES = {'jats': JATSParser(),
                'dc': DataciteParser(),
                'cr': CrossrefParser(),
                'nlm': JATSParser()
               }

logger = setup_logging('logs')

def get_args():

    parser = argparse.ArgumentParser('Create an ADS record from a DOI')

    parser.add_argument('-b',
                        '--bibstem',
                        dest='bibstem',
                        action='store',
                        default=None,
                        help='Bibstem for special handling and/or bibcode(s)')

    parser.add_argument('-d',
                        '--doi',
                        dest='fetch_doi',
                        action='store',
                        default=None,
                        help='DOI to fetch')

    parser.add_argument('-l',
                        '--doi-list',
                        dest='fetch_doi_list',
                        action='store',
                        default=None,
                        help='Path to a file containing a list of DOIs, one per line')

    parser.add_argument('-f',
                        '--outfile',
                        dest='output_file',
                        action='store',
                        default='./doi.tag',
                        help='File that tagged format will be written to')

    parser.add_argument('-p',
                      '--proc_path',
                      dest='proc_path',
                      action='store',
                      default=None,
                      help='Path to files or list of files')

    parser.add_argument('-t',
                        '--file_type',
                        dest='file_type',
                        action='store',
                        default=None,
                        help='Type of input file: jats, dc, cr, nlm')

    args = parser.parse_args()
    return args


def main():

    args = get_args()
    rawDataList = []
    ingestDocList = []

    # This route processes data from user-input files
    if args.proc_path:
        infiles = iglob(args.proc_path)
        for f in infiles:
            try:
                with open(f, 'r') as fin:
                    output = {'data': fin.read(),
                              'name': f,
                              'type': args.file_type}
                    rawDataList.append(output)
            except Exception as err:
                logger.warning("Failed to import %s: %s" % (f, err))

    # This route fetches data from Crossref via the Habanero module
    elif args.fetch_doi:
        try:
            getdoi = doiharvest.DoiHarvester(doi=args.fetch_doi)
            output = {'data': getdoi.get_record(),
                      'type': 'cr'}
            rawDataList.append(output)
        except Exception as err:
            logger.warning("Failed to fetch DOI %s: %s" % (args.fetch_doi,err))

    elif args.fetch_doi_list:
        try:
            with open(args.fetch_doi_list, 'r') as fin:
                for l in fin.readlines():
                    fetch_doi = l.strip()
                    try:
                        getdoi = doiharvest.DoiHarvester(doi=fetch_doi)
                        output = {'data': getdoi.get_record(),
                                  'type': 'cr'}
                        rawDataList.append(output)
                    except Exception as err:
                        logger.warning("Failed to fetch DOI %s: %s" % (fetch_doi,err))
        except Exception as err:
            logger.error("Failed to read %s: %s" % (args.fetch_doi_list, err))

    # Now process whatever raw records you have
    for rec in rawDataList:
        pdata = rec.get('data', None)
        ptype = rec.get('type', None)
        filename = rec.get('name', None)
        parser = PARSER_TYPES.get(ptype, None)
        print('Input file: %s' % filename)
        if parser:
            try:
                if ptype == 'nlm':
                    ingestDocList.append(parser.parse(pdata, bsparser='lxml-xml'))
                else:
                    ingestDocList.append(parser.parse(pdata))
            except Exception as err:
                logger.warning("Error parsing record: %s" % err)
        else:
            logger.error("No parser available for file_type '%s'." % args.file_type)


    if ingestDocList:
        if args.output_file:
            x = Tagged()
            with open(args.output_file, 'a') as fout:
                try:
                    for d in ingestDocList:
                        xlator = translator.Translator()
                        xlator.translate(data=d)
                        x.write(xlator.output, fout)
                except Exception as err:
                    logger.warning("Export to tagged file failed: %s\t%s" % (err, d))


if __name__ == '__main__':
    main()



# Plos ONE example from Habanero docs
# doi = '10.1371/journal.pone.0033693'

# MDPI Galaxies -- has abstract
# doi = '10.3390/galaxies9040111'

# PNAS volume 1 paper (1915)
# doi = '10.1073/pnas.1.1.51'

