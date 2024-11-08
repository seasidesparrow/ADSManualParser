from adsmanparse.exceptions import *
from adsenrich.bibcodes import BibcodeGenerator
from bs4 import BeautifulSoup
import re

fix_ampersand = re.compile(r"(&amp;)(.*?)(;)")

try:
    bibgen = BibcodeGenerator()
except Exception as err:
    print('Warning, BibcodeGenerator not initialized!')


class Translator(object):
    '''
    translates an ingest data model (dict) object into something approximating
    what gets passed to the serializer for an ADS Classic Tagged record
    '''

    # INITIALIZATION
    def __init__(self, data=None, **kwargs):
        self.data = data
        self.output = dict()
        return

    # DETAGGER (from jats.py)
    def _detag(self, r, tags_keep, **kwargs):

        newr = BeautifulSoup(str(r), 'lxml-xml')
        try:
            tag_list = list(set([x.name for x in newr.find_all()]))
        except Exception as err:
            tag_list = []
        for t in tag_list:
            elements = newr.findAll(t)
            for e in elements:
                if t in JATS_TAGS_DANGER:
                    e.decompose()
                elif t in tags_keep:
                    e.contents
                else:
                    if t.lower() == 'sc':
                        e.string = e.string.upper()
                    e.unwrap()

        # Note: newr is converted from a bs4 object to unicode here.
        # Everything after this point is string manipulation.

        newr = str(newr)

        amp_fix = fix_ampersand.findall(newr)
        for s in amp_fix:
            s_old = ''.join(s)
            s_new = '&' + s[1] + ';'
            newr = newr.replace(s_old, s_new)

        newr = newr.replace(u'\n', u' ').replace(u'  ', u' ')
        newr = newr.replace('&nbsp;', ' ')

        return newr

    # TITLE
    def _get_title(self):
        title = self.data.get('title', None)
        subtitle = self.data.get('subtitle', None)
        if title:
            title_en = title.get('textEnglish', None)
            title_tn = title.get('textNative', None)
            title_ln = title.get('langNative', None)
            if title_en:
                self.output['title'] = title_en
            elif title_tn:
                self.output['title'] = title_tn
                self.output['language'] = title_ln
            if subtitle:
                subtitle_en = subtitle.get('textEnglish', None)
                subtitle_tn = subtitle.get('textNative', None)
                subtitle_ln = subtitle.get('langNative', None)
                if subtitle_en:
                    self.output['title'] += ": " + subtitle_en
                elif subtitle_tn:
                    self.output['title'] += ": " + subtitle_tn


    # INDIVIDUAL NAME
    def _get_name(self, name):
        surname = name.get('surname', None)
        given_name = name.get('given_name', None)
        middle_name = name.get('middle_name', None)
        pubraw = name.get('pubraw', None)
        collab = name.get('collab', None)
        native = name.get('native_lang', None)
        outname = None
        if surname:
            outname = surname
            if given_name:
                outname = outname + ', ' + given_name
                if middle_name:
                    outname = outname + ' ' + middle_name
        elif collab:
            outname = collab
        return outname, native

    # INDIVIDUAL AFFIL
    def _get_affil(self, contrib):
        attribs = contrib.get('attrib', None)
        affil = contrib.get('affiliation', None)
        affarray = []
        affidarray = []
        orcid = None
        email = None
        outaffil=None

        try:
            if affil:
                for a in affil:
                    aff = a.get('affPubRaw', None)
                    if aff:
                        affarray.append(aff)
                        affid = a.get('affPubID', None)
                        aid_out = {}
                        if affid:
                            aid_dict = {}
                            for x in affid:
                                aid_dict[x["affIDType"]]=x["affID"]
                            for system in ['ROR','GRID','ISNI']:
                                try:
                                    aid_out = {system: aid_dict[system]}
                                    break
                                except:
                                    pass
                        affidarray.append(aid_out)
                     
            if affidarray:
                new_affarray = []
                for ids, affstr in zip(affidarray, affarray):
                    if ids:
                        idkey = list(ids.keys())[0]
                        idvalue = list(ids.values())[0]
                        newaff='<AFF id="%s:%s">%s</AFF>' % (idkey,idvalue,affstr)
                        new_affarray.append(newaff)
                    else:
                        new_affarray.append(affstr)
                     
                if len(affarray) == len(new_affarray):
                    affarray = new_affarray
                
            if attribs:
                orcid = attribs.get('orcid', None)
                if orcid:
                    orcid = '<ID system="ORCID">' + orcid + '</ID>'
                    affarray.append(orcid)
                email = attribs.get('email', None)

            if affarray:
                outaffil = '; '.join(affarray)
                if email:
                    email = '<EMAIL>' + email + '</EMAIL>'
                    outaffil = outaffil + ' ' + email
        except Exception as err:
            print('Error in _get_affil: %s' % err)
        if outaffil:
            return outaffil
        else:
            return ''
            

    # ALL CONTRIB (NAME & AFFIL)
    def _get_auths_affils(self):
        authors = self.data.get('authors', None)
        if authors:
            author_list = list()
            affil_list = list()
            native_author_list = list()
            for a in authors:
                # person
                name = a.get('name', None)
                if name:
                    # person name
                    (auth, native_auth) = self._get_name(name)
                    # person attribs and affil
                    aff = self._get_affil(a)
                    if aff == 'None':
                        aff = ''
                    if native_auth == 'None':
                        native_auth = ''
                    author_list.append(auth)
                    native_author_list.append(native_auth)
                    affil_list.append(aff)
            self.output['authors'] = author_list
            self.output['affiliations'] = affil_list
            self.output['native_authors'] = native_author_list


    # ABSTRACT
    def _get_abstract(self):
        abstract = self.data.get('abstract', None)
        if abstract:
            abstract_raw = abstract.get('textEnglish', None)
        #tagset = JATS_TAGSET['abstract'] or None
        #self.output['abstract'] = self._detag(abstract_raw, tagset)
            self.output['abstract'] = abstract_raw


    def _get_keywords(self):
        keywords = self.data.get('keywords', None)
        keyword_list = []
        uat_list = []
        if keywords:
            for k in keywords:
                keyw = k.get('keyString', None)
                keytype = k.get('keySystem', None)
                keyid = k.get('keyID', None)
                if keyw:
                    keyword_list.append(keyw)
                if keytype == 'UAT':
                    if keyid:
                        uat_list.append(keyid)
        if keyword_list:
            self.output['keywords'] = ', '.join(keyword_list)
        if uat_list:
            self.output['uatkeys'] = ', '.join(uat_list)


    def _get_date(self):
        pubdate = self.data.get('pubDate', None)

        # what dates are available?
        printdate = pubdate.get('printDate', None)
        elecdate = pubdate.get('electrDate', None)
        otherdate = pubdate.get('otherDate', None)

        if printdate:
            if len(printdate) < 4:
                printdate = None
        if elecdate:
            if len(elecdate) < 4:
                elecdate = None
        if otherdate:
            odate = None
            
            for od in otherdate:
                odtype = od.get('otherDateType', None)
                if odtype in ['Available', 'Issued']:
                    odate = od.get('otherDateValue', None)
            if odate:
                otherdate = odate
            else:
                otherdate = None

        # choose a pubdate based on what's available (or not)
        date = None
        if printdate:
            date = printdate
        elif elecdate:
            date = elecdate
        elif otherdate:
            date = otherdate

        # if a date string was found, parse it to make output[pubdate]
        if date:
            try:
                dateparts = date.split('-')
                (y, m, d) = (0,0,0)
                if len(dateparts) == 1:
                    y = dateparts[0]
                elif len(dateparts) == 2:
                    m = dateparts[1]
                    y = dateparts[0]
                elif len(dateparts) == 3:
                    [y, m, d] = dateparts
                if int(m) == 0:
                    m = '00'
                elif int(m) < 10:
                    m = '0'+str(int(m))
                elif int(m) > 12:
                    m = '00'
                self.output['pubdate'] = "%s/%s" % (m,y)
            except Exception as err:
                pass

    def _get_properties(self, parsedfile):
        props = {}
        persistentids = self.data.get('persistentIDs', None)
        esources = self.data.get('esources', None)
        if esources:
            for src in esources:
                source = src.get('source', None)
                location = src.get('location', None)
                if source == 'pub_pdf' and location:
                    props['PDF'] = location
                elif source == 'pub_html' and location:
                    props['HTML'] = location
                    
                
        if persistentids:
            for i in persistentids:
                doi = i.get('DOI', None)
                preprint = i.get('preprint', None)
                if doi:
                    props['DOI'] = doi
                if preprint:
                   source = preprint.get('source', None)
                   ident = preprint.get('identifier', None)
                   if source == 'arxiv' and ident:
                       props['ARXIV'] = ident
        openaccess = self.data.get('openAccess', {}).get('open', False)
        if openaccess:
            props['OPEN'] = 1

        if parsedfile:
            parsedFileName = self.data.get('recordData', {}).get('loadLocation', None)
            if parsedFileName:
                props['FILE'] = parsedFileName
            
        if props:
            self.output['properties'] = props
        pass


    def _get_references(self):
        references = self.data.get('references', None)
        if references:
            self.output['refhandler_list'] = references


    def _get_editors(self):
        otherContrib = self.data.get("otherContributor", [])
        editors = []
        editorstring=None
        for oc in otherContrib:
            if oc.get("role", None) == "editor":
                given = oc.get("contrib", {}).get("name", {}).get("given_name", None)
                surname = oc.get("contrib", {}).get("name", {}).get("surname", None)
                if given:
                    given = given[0]
                editors.append(given + ". " + surname)
        if len(editors) == 1:
            editorstring = editor[0] + ", editor."
        elif len(editors) <= 3:
            editorstring = ", ".join(editors) + ", editors."
        elif len(editors) > 3:
            editorstring = editor[0] + "et al., editors."
        return editorstring

    def _get_publication(self):
        if not self.output.get('publication', None):
            publication = self.data.get('publication', None)
            pagination = self.data.get('pagination', None)
            pubstring = None
            if publication:
                journal = publication.get('pubName', None)
                year = publication.get('pubYear', None)
                volume = publication.get('volumeNum', None)
                issue = publication.get('issueNum', None)
                publisher = publication.get('publisher', None)
                book = publication.get('bookSeries', {}).get('seriesName', None)
                conf = publication.get('confName', None)
                dates = publication.get('confDates', None)
                editors = self._get_editors()
                if journal:
                    pubstring = journal
                elif book:
                    pubstring = book
                    if editors:
                        pubstring = pubstring + "; " + editors
                elif conf:
                    pubstring = conf
                    if dates:
                        pubstring = pubstring + ', ' + dates
                    if editors:
                        pubstring = pubstring + "; " + editors
                if volume:
                    if pubstring:
                        pubstring = pubstring + ', Volume ' + volume
                    else:
                        pubstring = 'Volume ' + volume
                elif publisher:
                    if publisher == 'OUP' or publisher == 'Oxford University Press':
                        pubstring = pubstring + ', Advance Access'
                if issue:
                    if pubstring:
                        pubstring = pubstring + ', Issue ' + issue
                    else:
                        pubstring = 'Issue ' + issue
            if pagination:
                pagerange = pagination.get('pageRange', None)
                pagecount = pagination.get('pageCount', None)
                idno = pagination.get('electronicID', None)
                firstp = pagination.get('firstPage', None)
                lastp = pagination.get('lastPage', None)
                if (firstp and lastp) and not pagerange:
                    pagerange = firstp + '-' + lastp
                if pagerange:
                    if pubstring:
                        pubstring = pubstring + ', pp. ' + pagerange
                    else:
                        pubstring = 'pp. ' + pagerange
                elif firstp:
                    if pubstring:
                        pubstring = pubstring + ', page ' + firstp
                elif idno:
                    if pubstring:
                        pubstring = pubstring + ', id.' + idno
                    else:
                        pubstring = 'id.' + idno
                if pagecount:
                    pubstring = pubstring + ', ' + pagecount + ' pp.'
            if pubstring:
                self.output['publication'] = pubstring
            if publisher == 'Zenodo':
                self.output['source'] = publisher

    def _get_bibcode(self, bibstem=None, volume=None):
        try:
            self.output['bibcode'] = bibgen.make_bibcode(self.data, bibstem=bibstem, volume=volume)
        except Exception as err:
            print('Couldnt make a bibcode: %s' % str(err))

    def _get_copyright(self):
        copyright_statement=self.data.get("copyright", {}).get("statement", None)
        if copyright_statement:
            self.output["copyright"] = copyright_statement

    def _special_handling(self, bibstem=None):
        # Special data handling rules on a per-bibstem basis
        if bibstem == "pds..data" or bibstem == "pdss.data":
             urn = ""
             for ident in self.data.get("publisherIDs", []):
                 if ident.get("Identifier", "")[0:3] == "urn":
                     urn = ident.get("Identifier", "")
             pubstring = "NASA Planetary Data System, %s" % urn
             self.output["publication"] = pubstring
        
        elif bibstem == 'MPEC':
            # To do:
            #	- reparse title into Circular no. and title
            #	- remove MPC Staff as author
            #	- add all otherContributor.DataCollector as author(s)
            #   - delete abstract
            #   - create the output publication (%J) field
            
            if self.data.get('title', {}).get('textEnglish', None):
                (circular_number, circular_title) = self.data.get('title', {}).get('textEnglish').split(':')
                circular_number = circular_number.replace('MPEC ','').strip()
                circular_issue = circular_number.split('-')[1]
                (circular_series, circular_page) = re.split(r'(\D+)', circular_issue)[1:]
                circular_title = circular_title.strip()
                self.data['title']['textEnglish'] = circular_title
                publication = self.data.get('publication', None)
                if publication:
                    self.data['publication']['volumeNum'] = circular_series
                if self.data.get('pagination', None):
                    self.data['pagination']['firstPage'] = str(int(circular_page))
                else:
                   self.data['pagination'] = {'firstPage': str(int(circular_page))}
                self.output['publication'] = 'Minor Planet Electronic Circ., No. %s' % circular_number
                
                  
            if self.data.get('abstract', None):
                self.data['abstract'] = None

            new_authors = []
            for a in self.data.get('authors', []):
                pubraw = a.get('name', {}).get('pubraw', None)
                if pubraw:
                    if pubraw != 'Minor Planet Center Staff':
                        new_authors.append(a)
            for a in self.data.get('otherContributor', []):
                if a.get('contrib', {}):
                    new_authors.append(a['contrib'])
            self.data['authors'] = new_authors
                   

    def translate(self, data=None, publisher=None, bibstem=None, volume=None, parsedfile=False):
        if data:
            self.data = data
        if not self.data:
            raise NoParsedDataException('You need to supply data to translate!')
        else:
            if bibstem:
                self._special_handling(bibstem)
            self._get_title()
            self._get_abstract()
            self._get_keywords()
            self._get_auths_affils()
            self._get_date()
            self._get_references()
            self._get_properties(parsedfile)
            self._get_publication()
            self._get_bibcode(bibstem=bibstem, volume=volume)
            self._get_copyright()
