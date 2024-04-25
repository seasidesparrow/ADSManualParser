import argparse
import json
import os
from adsenrich.references import ReferenceWriter
from adsingestp.parsers.crossref import CrossrefParser
from adsingestp.parsers.jats import JATSParser
from adsingestp.parsers.datacite import DataciteParser
from adsingestp.parsers.elsevier import ElsevierParser
from adsingestp.parsers.adsfeedback import ADSFeedbackParser
from adsingestp.parsers.copernicus import CopernicusParser
from adsingestp.parsers.wiley import WileyParser
from adsmanparse import translator, doiharvest, classic_serializer, utils
from adsputils import load_config, setup_logging
from datetime import datetime, timedelta
from glob import iglob

PARSER_TYPES = {'jats': JATSParser(),
                'dc': DataciteParser(),
                'cr': CrossrefParser(),
                'nlm': JATSParser(),
                'elsevier': ElsevierParser(),
                'feedback': ADSFeedbackParser(),
                'copernicus': CopernicusParser(),
                'wiley': WileyParser(),
               }

proj_home = os.path.realpath(os.path.join(os.path.dirname(__file__), "./"))
conf = load_config(proj_home=proj_home)
logger = setup_logging(
    "run.py",
    proj_home=proj_home,
    level=conf.get("LOGGING_LEVEL", "INFO"),
    attach_stdout=conf.get("LOG_STDOUT", False),
)


def get_args():

    parser = argparse.ArgumentParser('Create an ADS record from a DOI')

    parser.add_argument('-b',
                        '--bibstem',
                        dest='bibstem',
                        action='store',
                        default=None,
                        help='Bibstem for special handling and/or bibcode(s)')

    parser.add_argument('-v',
                        '--volume',
                        dest='volume',
                        action='store',
                        default=None,
                        help='Volume for special handling and/or bibcodes(s)')

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
                        default=None,
                        help='Type of input file: jats, dc, cr, nlm, elsevier, feedback, copernicus, wiley')

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
                        default='/proj/ads/references/sources/',
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
                        default=False,
                        help='Output parsed filename in properties tag')


    args = parser.parse_args()
    return args

def create_tagged(rec=None, args=None):
    try:
        xlator = translator.Translator()
        seri = classic_serializer.ClassicSerializer()
        xlator.translate(data=rec, bibstem=args.bibstem, volume=args.volume, parsedfile=args.parsedfile)
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

def write_record(record, args):
    if args.output_file:
        tagged = create_tagged(rec=record, args=args)
        if tagged:
            with open(args.output_file, "a") as fout:
                fout.write("%s\n" % tagged)
            if args.write_refs:
                create_refs(rec=record, args=args)
        else:
            raise Exception("Tagged record not generated.")
    else:
        raise Exception("Output_file not defined, no place to write records to!")


def parse_record(rec):
    pdata = rec.get('data', None)
    ptype = rec.get('type', None)
    filename = rec.get('name', None)
    parser = PARSER_TYPES.get(ptype, None)
    write_file = utils.has_body(pdata)
    parsedrecord = None
    if not parser:
        logger.error("No parser available for file_type '%s'." % ptype)
    else:
        try:
            parser.__init__()
            if ptype == 'nlm':
                parsedrecord = parser.parse(pdata, bsparser='lxml-xml')
            else:
                parsedrecord = parser.parse(pdata)
            if parsedrecord:
                if utils.suppress_title(parsedrecord, conf.get("DEPRECATED_TITLES", [])):
                    raise Exception("Warning: article matches a suppressed title.")
                if filename:
                    if not parsedrecord.get("recordData", {}).get("loadLocation", None):
                        parsedrecord["recordData"]["loadLocation"] = filename
                    if not write_file:
                        parsedrecord["recordData"]["loadLocation"] = None
            else:
                raise Exception("Null body returned by parser!")
        except Exception as err:
            logger.warning("Error parsing record (%s): %s" % (filename,err))
    return parsedrecord


def process_record(rec, args):
    try:
        parsedRecord = parse_record(rec)
        if not parsedRecord:
            logger.error("Parsing yielded no data for %s" % rec.get("name", None))
        else:
            try:
                write_record(parsedRecord, args)
            except Exception as err:
                logger.error("Classic tagger did not generate a tagged record for %s" % f)
            else:
                logger.debug("Successfully processed %s with %s" % (rec.get("name", None), str(args)))
    except Exception as err:
        logger.error("Error parsing and processing record %s: %s" % (rec.get("name", None), err))


def process_filepath(args):
    if args.proc_path:
        logger.info("Finding files in path %s ..." % args.proc_path)
        infiles = [x for x in iglob(args.proc_path, recursive=True)]
        if not infiles:
            logger.warning("No files found in path %s." % args.proc_path)
        else:
            logger.info("Found %s files." % len(infiles))
            if args.proc_since:
                logger.info("Checking file ages...")
                dtime = timedelta(days=int(args.proc_since))
                today = datetime.today()
                infiles_since = [x for x in infiles if ((today - datetime.fromtimestamp(os.path.getmtime(x))) <= dtime)]
                infiles = infiles_since
            if not infiles:
                logger.error("No files more recent than %s days old!" % str(args.proc_since))
            else:
                nfiles = len(infiles)
                logger.info("There were %s files found to process" % str(nfiles))
                for f in infiles:
                    inputRecord = {}
                    try:
                        with open(f, 'r') as fin:
                            inputRecord = {'data': fin.read(),
                                           'name': f,
                                           'type': args.file_type}
                    except Exception as err:
                        logger.warning("Failed to read input file %s: %s" % (f, err))
                    else:
                        process_record(inputRecord, args)
    else:
        logger.warning("Null processing path given, nothing processed.")


def process_doilist(doilist, args):
    if doilist:
        ptype = args.file_type
        if not ptype:
            ptype = 'cr'
        for d in doilist:
            try:
                getdoi = doiharvest.DoiHarvester(doi=d)
                inputRecord = {'data': getdoi.get_record(),
                               'name': d,
                               'type': ptype}
            except Exception as err:
                logger.warning("Failed to fetch doi %s: %s" % (d, err))
            else:
                process_record(inputRecord, args)
    else:
        logger.warning("No DOIs provided, nothing processed.")


def main():
    args = get_args()
    rawDataList = []
    ingestDocList = []

    logger.debug("Initiating parsing with the following arguments: %s" % str(args))

    if args.proc_path and not args.file_type:
        fileTypeList = PARSER_TYPES.keys()
        logger.error("You need to provide a filetype from this list: %s" % str(fileTypeList))
    else:
        # This route processes data from user-input files
        if args.proc_path:
            process_filepath(args)
            
        # This route fetches data from Crossref via the Habanero module
        elif (args.fetch_doi or args.fetch_doi_list):
            doiList = None
            if args.fetch_doi:
                doiList = [args.fetch_doi]
            elif args.fetch_doi_list:
                doiList = []
                with open(args.fetch_doi_list, 'r') as fin:
                    for l in fin.readlines():
                        doiList.append(l.strip())
            process_doilist(doiList, args)


if __name__ == '__main__':
    main()
