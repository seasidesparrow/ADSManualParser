"""
This uses the new infrastructure developed for ADSManualParser, including
* ADSIngestParser
* ADSIngestEnrichment

    -MT 2023 November 08
"""

import argparse
import os
from adsingestp.parsers.datacite import DataciteParser
from adsmanparse import translator, classic_serializer
from adsputils import setup_logging

logger = setup_logging('zenodo-parser')

def get_args():

    parser = argparse.ArgumentParser("Parse a Zenodo record")

    parser.add_argument("-f",
                        "--infile",
                        dest="infile",
                        action="store",
                        default=None,
                        help="Full path to input file")

    args = parser.parse_args()
    return args


def parse(infile):
    try:
        with open(infile, "r") as fin:
            rawdata = fin.read()
            parser = DataciteParser()
            record = parser.parse(rawdata)

            xlator = translator.Translator()
            xlator.translate(record)

            seri = classic_serializer.ClassicSerializer()
            tagged_output = seri.output(xlator.output)

            return tagged_output
    except Exception as err:
        logger.warning("Parsing failed for file %s: %s" % (infile, err))



def main():
    args=get_args()

    if args.infile:
        if os.path.exists(args.infile):
            tagged_record = parse(args.infile)
            print("%s\n" % tagged_record)
        else:
            logger.error("The file %s does not exist." % args.infile)
    else:
        logger.error("You must supply a filename to parse")


if __name__ == "__main__":
    main()
