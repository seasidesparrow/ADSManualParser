# ADSManualParser
Simple repo for setting up a data import directory for CSG / Curators.  Uses the new Ingest Data Model along with select functionality from adsabs-pyingest to generate Classic tagged files.


## Usage

`run.py` provides a basic all-in-one interface to the tools, but the modules
in adsmanparse can be called from custom scripts if desired.

```
usage: Create an ADS record from a DOI [-h] [-b BIBSTEM] [-d FETCH_DOI]
                                       [-l FETCH_DOI_LIST] [-f OUTPUT_FILE]
                                       [-p PROC_PATH] [-t FILE_TYPE]

optional arguments:
  -h, --help            show this help message and exit
  -b BIBSTEM, --bibstem BIBSTEM
                        Bibstem for special handling and/or bibcode(s)
  -d FETCH_DOI, --doi FETCH_DOI
                        DOI to fetch
  -l FETCH_DOI_LIST, --doi-list FETCH_DOI_LIST
                        Path to a file containing a list of DOIs, one per line
  -f OUTPUT_FILE, --outfile OUTPUT_FILE
                        File that tagged format will be written to
  -p PROC_PATH, --proc_path PROC_PATH
                        Path to files or list of files
  -t FILE_TYPE, --file_type FILE_TYPE
                        Type of input file: jats, dc, cr, nlm
```

### Generate tagged format output from a DOI

If you want to harvest a single record from a DOI, use the `-d` option, and provide the doi you want to harvest as the command line argument.  You can optionally specify a name for the output file, otherwise results will be written to `./doi.tag`.

`python run.py -d '10.3847/1538-4357/aca326' -f my_output.tag`

Result:

```
%R 2022ApJ...941..205M
%T Effects of Active Galactic Nucleus Feedback on Cold Gas Depletion and Quenching of Central Galaxies
%A Ma, Wenlin; Liu, Kexin; Guo, Hong; Cui, Weiguang; Jones, Michael G.; Wang, Jing; Zhang, Le; Dav&eacute;, Romeel
%F AA(<ID system="ORCID">0000-0003-4978-5569</ID>), AB(<ID system="ORCID">0000-0002-8604-2556</ID>), AC(<ID system="ORCID">0000-0003-4936-8247</ID>), AD(<ID system="ORCID">0000-0002-2113-4863</ID>), AE(<ID system="ORCID">0000-0002-5434-4904</ID>), AF(<ID system="ORCID">0000-0002-6593-8820</ID>), AG(), AH(<ID system="ORCID">0000-0003-2842-9434</ID>)
%D 2022/12
%J The Astrophysical Journal, Volume 941, Issue 2, page 205
%B We investigate the influence of active galactic nucleus (AGN) feedback on the galaxy cold gas content and its connection to galaxy quenching in three hydrodynamical simulations of Illustris, IllustrisTNG, and SIMBA. By comparing to the observed atomic and molecular neutral hydrogen measurements for central galaxies, we find that Illustris overpredicts the cold gas masses in star-forming galaxies and significantly underpredicts them for quenched galaxies. IllustrisTNG performs better in this comparison than Illustris, but quenched galaxies retain too much cold gas compared with observations. SIMBA shows good agreement with observations, by depleting the global cold gas reservoir for quenched galaxies. We find that the discrepancies in IllustrisTNG are caused by its weak kinetic AGN feedback that only redistributes the cold gas from the inner disks to the outer regions and reduces the inner cold gas densities. It agrees with observations much better when only the cold gas within the stellar disk is considered to infer the star formation rates. From dependences of the cold gas reservoir on the black hole mass and Eddington ratio, we find that the cumulative energy release during the black hole growth is the dominant reason for the cold gas depletion and thus the galaxy quenching. We further measure the central stellar surface density within 1 kpc (&Sigma; 1 ) for the high-resolution run of IllustrisTNG and find a tight correlation between &Sigma; 1 and black hole mass. It suggests that the observed decreasing trend of cold gas mass with &Sigma; 1 is also a reflection of the black hole growth.
%I DOI: 10.3847/1538-4357/aca326
```
