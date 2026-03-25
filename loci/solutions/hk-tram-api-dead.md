# HK Tramways ETA API — Dead (Feb 2026)

The old endpoint `https://www.hktramways.com/nextTram/geteat.php?stop_code=10W` is non-functional. TLS handshake succeeds but server returns 0 bytes (hangs indefinitely).

- Originally reverse-engineered ~2014 (node-hongkong-trams on GitHub)
- Returned XML with `<eat>`, `<tram_id>`, `<dest_stop_code>` fields
- No authentication required
- Stop list was at `hktramways.com/js/googleMap.js` (still accessible)

## No Public Alternative

- data.gov.hk has no tram ETA dataset (MTR, KMB, CTB, Light Rail only)
- Citymapper had integration but likely uses a private arrangement

## Stop Reference (if API revives)

Westbound stops near Sai Wan Ho:
- 08W: Holy Cross Path 聖十字徑 (22.2813, 114.2225)
- 10W: Tai Hong Street 太康街 (22.2831, 114.2212) ← nearest to Grand Promenade
- 14W: Kornhill 康山 (22.2845, 114.2160) ← destination
