BASEDIR="/proj/ads/fulltext/sources"

for j in "AnPhy" "CoPhC" "EP&S" "Icar" "JCoPh" "JMoSp" "JSSCh" "OptCo" "PEPI" "P&SS" "NDS" "ADNDT" "PrPNP" "PhyD" "NIMPB" "NIMPA" "AdSpR" "ChA&A" "JMMM" "PhR" "PhLB" "NuPhA" "PhLA" "PhyA" "JGP" "NuPhB" "SuMi" "MSSP" "JFS" "NuPhS" "PhyB" "PhyC" "APh" "RaPC" "OptFT" "JMagR" "InPhT" "JATP" "NewA" "PhyE" "NewAR"; do
  xmlpath="$BASEDIR/$j"
  maxage=14
  `python run.py -f "./elsevier.tag" -p "$xmlpath/**/*.xml" -a $maxage -t elsevier`
done
