from adsingestp.parsers import arxiv, crossref, datacite, jats
from glob import glob
from newparse.translator import Translator
from pyingest.serializers.classic import Tagged
import json


def load_file(filename):
    try:
        with open(filename, 'rb') as fx:
            data = fx.read()
    except Exception as err:
        print("error loading file: %s" % err)
    else:
        return data


def main():
    infiles = glob('newparse/tests/data/input/*jats*.xml')
    # infiles = ['newparse/tests/data/input/apsjats_10.1103.PhysRevA.97.019999.fulltext.xml', 'newparse/tests/data/input/apsjats_10.1103.PhysRevAccelBeams.21.014702.fulltext.xml', 'newparse/tests/data/input/apsjats_10.1103.PhysRevA.97.012101.fulltext.xml', 'newparse/tests/data/input/apsjats_10.1103.PhysRevB.96.081117.fulltext.xml', 'newparse/tests/data/input/apsjats_10.1103.PhysRevB.96.104435.fulltext.xml', 'newparse/tests/data/input/VOR_10.1119_10.0009409.xml']
    filetype = 'jats'
    documents=[]

    for f in infiles:
        print('file: %s' % f)
        try:
            data = load_file(f)
            if data:
                if filetype == 'arxiv':
                    parser = arxiv.ArxivParser()
                elif filetype == 'crossref':
                    parser = crossref.CrossrefParser()
                elif filetype == 'datacite':
                    parser = datacite.DataciteParser()
                elif filetype == 'jats':
                    parser = jats.JATSParser()
                else:
                    parser = None

                if parser:
                    try:
                        parsed = parser.parse(data)
                    except Exception as err:
                        print("Parsing failed: %s" % err)
                    else:
                        if parsed:
                            #outf = f.split('/')[-1] + '.json'
                            #with open(outf,'w') as fj:
                            #    fj.write(json.dumps(parsed, indent=2, sort_keys=True))
                            xlator = Translator(data=parsed)
                            xlator.translate()
                            documents.append(xlator.output)
            else:
                print("No useful data from %s, skipping..." % f)
        except Exception as err:
            print('oops: %s' % err)

    for d in documents:
        x = Tagged()
        with open('test.tag','a') as fw:
            try:
                x.write(d, fw)
            except Exception as err:
                print('serializer problem... %s' % err)


if __name__ == '__main__':
    main()
