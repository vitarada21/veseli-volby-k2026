# Okrsky Veselí nad Lužnicí — volby 2022 × 2026

Interaktivní srovnání výsledků komunálních voleb 2022 a 2026 po jednotlivých
volebních okrscích (1–7) ve Veselí nad Lužnicí. Schematická mapa okrsků,
klikací detail s porovnáním účasti a hlasů pro jednotlivé strany, seznam ulic
v každém okrsku.

Živá verze: **https://vitarada21.github.io/veseli-volby-k2026/**

## Zdroje dat

- Hranice okrsků a seznam ulic: Oznámení MěÚ Veselí nad Lužnicí o době a
  místě konání voleb (23. 9. 2026).
- Výsledky voleb: [ČSÚ / volby.gov.cz](https://volby.gov.cz) a
  [seznamzpravy.cz](https://www.seznamzpravy.cz) (výsledky po okrscích).
- 2022: finální. 2026: průběžné — doplňuje se v průběhu sčítání.

## Aktualizace dat

Výsledky jsou zapečené přímo v `index.html` jako `const DATA = {...}`.
Pro osvěžení (např. jakmile se sečtou další okrsky 2026):

```bash
python scripts/update_data.py
```

Skript znovu stáhne výsledky za všechny okrsky a přepíše datový blok
v `index.html`. Okrsky, které ještě nejsou finální, zůstanou v aplikaci
označené jako „čeká se“ a jde je v prohlížeči ručně doplnit (uloží se jen
lokálně, do `localStorage`).

## Nasazení

Statická stránka, žádný build krok. GitHub Pages: Settings → Pages →
Deploy from branch `main` / `/ (root)`.
