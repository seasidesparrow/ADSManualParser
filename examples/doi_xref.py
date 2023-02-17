import argparse
from newparse import translator, doiharvest
from adsingestp.parsers.crossref import CrossrefParser
from pyingest.serializers.classic import Tagged

def get_args():
    parser = argparse.ArgumentParser('Create an ADS record from a DOI')
    parser.add_argument('-d',
                        '--doi',
                        dest='fetch_doi',
                        action='store',
                        default=None,
                        help='DOI to fetch')
    parser.add_argument('-f',
                        '--outfile',
                        dest='output_file',
                        action='store',
                        default='./doi.tag',
                        help='File that tagged format will be written to')
    args = parser.parse_args()
    return args


def main():

    args = get_args()
    documents = []
    if args.fetch_doi:
        try:
            getdoi = doiharvest.DoiHarvester(doi=args.fetch_doi)
            xml_record = getdoi.get_record()
        except Exception as err:
            print('parsing failed, because doi_harvester failed: %s' % err)
        else:
            try:
                parser = CrossrefParser()
                ingest_record = parser.parse(xml_record)
            except Exception as err:
                print('parsing failed, because ingestparser failed: %s' % err)
            else:
                try:
                    t = translator.Translator(data=ingest_record)
                    t.translate()
                    documents.append(t.output)
                except Exception as err:
                    print('tagged record creation failed: %s' % err)
    if documents:
        if args.output_file:
            x = Tagged()
            with open(args.output_file, 'a') as fout:
                try:
                    for d in documents:
                        x.write(d, fout)
                except Exception as err:
                    print('export to tagged file failed: %s' % err)
    else:
        print('No DOI supplied!  Invoke with -d DOI')

    # Plos ONE example from Habanero docs
    # doi = '10.1371/journal.pone.0033693'

    # MDPI Galaxies -- has abstract
    # doi = '10.3390/galaxies9040111'

    # PNAS volume 1 paper (1915)
    # doi = '10.1073/pnas.1.1.51'

if __name__ == '__main__':
    main()

