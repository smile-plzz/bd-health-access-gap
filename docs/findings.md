# Findings — Kishoreganj pilot

Pilot scope: Kishoreganj district (13 upazilas), road-network travel time
from each upazila centroid to the nearest OSM-tagged health facility
(hospital/clinic/doctors/pharmacy), computed via Dijkstra over the OSM
drive-network graph. Full run: `src/join_data.py` then `src/score_pilot.py`.

## Results

| Upazila | Population | Nearest facility (min) |
|---|---:|---:|
| Austagram | 152,402 | 54.7 |
| Itna | 170,622 | 30.1 |
| Mithamain | 115,555 | 16.0 |
| Bhairab | 348,881 | 15.4 |
| Kuliarchar | — | 13.9 |
| Bajitpur | 284,301 | 12.9 |
| Hossainpur | 200,880 | 12.5 |
| Katiadi | 336,508 | 12.2 |
| Nikli | 142,964 | 10.2 |
| Pakundia | 251,520 | 4.9 |
| Karimganj | 307,979 | 3.4 |
| Kishoreganj Sadar | 476,400 | 1.4 |
| Tarail | 158,196 | 0.9 |

## Read

- **Austagram and Itna are the clear outliers** — 30-55 min to the nearest
  facility, 6-40x worse than the rest of the district. Both sit in the
  Kishoreganj haor (wetland) belt, which matches the known pattern:
  haor upazilas have sparse road networks and are seasonally
  boat-dependent, so a road-only "drive" network likely *understates*
  their true isolation for parts of the year.
- **Kishoreganj Sadar and Tarail are best-served** (under 1.5 min) —
  Sadar is the district headquarters, Tarail is small and centrally
  located near the main road corridor. Expected.
- No strong population-size vs. access-time relationship in this sample
  (Bhairab is large and moderately underserved; Austagram is mid-sized
  and worst-served) — sparse-road-network geography looks like the
  bigger driver than population here, not something you'd guess without
  running the numbers.

## Caveats (see also `docs/methodology.md`)

- n=13 upazilas, one district — not a claim about Bangladesh as a whole.
- Facility set is OSM-tagged POIs, not an official DGHS registry; may
  undercount facilities in less-mapped rural areas, which would bias
  travel times *upward* precisely in the areas already scoring worst
  (Austagram, Itna) — the gap could be even larger, or partly an
  OSM-coverage artifact. Worth cross-checking against the DGHS "Doctor
  Directory" dataset before treating this as a real access finding.
- Drive-network travel time doesn't capture walking/rickshaw/boat access,
  which matters most exactly in the haor upazilas driving the result.
- Kuliarchar has no matched population figure (name-join gap, see
  `docs/methodology.md`) — travel time is still valid, just missing pop.

## Next

- Scale to the rest of Kishoreganj's neighboring districts, or go
  national with a proper pcode crosswalk for the population join.
- Pull DGHS facility data as a cross-check on OSM coverage.
- Test a walking-speed network for haor upazilas as a sensitivity check.
