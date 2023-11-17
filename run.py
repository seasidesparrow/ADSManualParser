import argparse
import json
import os
from adsmanparse import translator, doiharvest, classic_serializer
from adsenrich.references import ReferenceWriter
from adsingestp.parsers.crossref import CrossrefParser
from adsingestp.parsers.jats import JATSParser
from adsingestp.parsers.datacite import DataciteParser
from adsingestp.parsers.elsevier import ElsevierParser
from adsingestp.parsers.adsfeedback import ADSFeedbackParser
from adsingestp.parsers.copernicus import CopernicusParser
from adsputils import setup_logging
from datetime import datetime, timedelta
from glob import iglob

PARSER_TYPES = {'jats': JATSParser(),
                'dc': DataciteParser(),
                'cr': CrossrefParser(),
                'nlm': JATSParser(),
                'elsevier': ElsevierParser(),
                'feedback': ADSFeedbackParser(),
                'copernicus': CopernicusParser(),
               }

logger = setup_logging('manual-parser')

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

    parser.add_argument('-a',
                        '--age',
                        dest='proc_since',
                        action='store',
                        default=None,
                        help='Age (in days) of oldest files in --proc_path to process')

    parser.add_argument('-t',
                        '--file_type',
                        dest='file_type',
                        action='store',
                        default='jats',
                        help='Type of input file: jats, dc, cr, nlm, elsevier, feedback')

    parser.add_argument('-w',
                        '--write_refs',
                        dest='write_refs',
                        action='store_true',
                        default=False,
                        help='Export references from records along with bibdata')

    parser.add_argument('-r',
                        '--ref_dir',
                        dest='ref_dir',
                        action='store',
                        default='./references/sources',
                        help='Base path to reference output directory')

    parser.add_argument('-s',
                        '--source',
                        dest='source',
                        action='store',
                        default=None,
                        help='Origin/publisher of record/reference data')

    parser.add_argument('-z',
                        '--parsedfile',
                        dest='parsedfile',
                        action='store_true',
                        default=None,
                        help='Output parsed filename in properties tag')


    args = parser.parse_args()
    return args


def create_tagged(rec=None, args=None):
    try:
        xlator = translator.Translator()
        seri = classic_serializer.ClassicSerializer()
        xlator.translate(data=rec, bibstem=args.bibstem, parsedfile=args.parsedfile)
        output = seri.output(xlator.output)
        return output
    except Exception as err:
        logger.warning("Export to tagged file failed: %s\t%s" % (err, rec))


def create_refs(rec=None, args=None):
    try:
        rw = ReferenceWriter(reference_directory=args.ref_dir,
                             reference_source=args.source,
                             data=rec)
        rw.write_references_to_file()
    except Exception as err:
        logger.warning("Unable to write references: %s" % err)


def main():

    args = get_args()
    rawDataList = []
    ingestDocList = []

    # This route processes data from user-input files
    if args.proc_path:
        infiles = iglob(args.proc_path, recursive=True)
        if infiles and args.proc_since:
            dtime = timedelta(days=int(args.proc_since))
            today = datetime.today()
            infiles_since = [x for x in infiles if ((today - datetime.fromtimestamp(os.path.getmtime(x))) <= dtime)]
            infiles = infiles_since
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
                    getdoi = None
                    output = None
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
        if parser:
            try:
                parser.__init__()
                parsedrecord = None
                if ptype == 'nlm':
                    parsedrecord = parser.parse(pdata, bsparser='lxml-xml')
                else:
                    parsedrecord = parser.parse(pdata)
                if parsedrecord:
                    if filename:
                        parsedrecord.setdefault("recordData", {}).setdefault("loadLocation", filename)
                    ingestDocList.append(parsedrecord)
                else:
                    raise Exception("Null body returned by parser!")
            except Exception as err:
                logger.warning("Error parsing record (%s): %s" % (filename,err))
        else:
            logger.error("No parser available for file_type '%s'." % args.file_type)


    if ingestDocList:
        if args.output_file:
            with open(args.output_file, 'a') as fout:
                for d in ingestDocList:
                    tagged = create_tagged(rec=d, args=args)
                    if tagged:
                        fout.write("%s\n" % tagged)
                    else:
                        logger.info("Tagged record not written.")
                    if args.write_refs:
                        create_refs(rec=d, args=args)


if __name__ == '__main__':
    main()
