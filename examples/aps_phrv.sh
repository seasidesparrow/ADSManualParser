BASEDIR="/proj/ads/fulltext/sources"

for j in "PhRvA" "PhRvB" "PhRvC" "PhRvD" "PhRvE" "PhRvF" "PhRvL" "PhRvM" "PhRvP" "PhRvR" "PhRvS" "PhRvX"; do
  xmlpath="$BASEDIR/$j"
  maxage=14
  `python run.py -f "./TEST_APS_PHRV/test_aps_phrv.tag" -p "$xmlpath/**/*.xml" -a $maxage -t jats`
done
