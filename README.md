# Armenia — legislation as Markdown (LawCodex)

Legislation of the Republic of Armenia (Հայաստանի Հանրապետություն) as Markdown, one file per
act: the Constitution, the codes and all laws in force, in their current consolidated
("incorporated") text, plus the English translations hosted by the same official system.
Part of [LawCodex](https://github.com/LawCodex).

Retrieved: **2026-10-12**.

## Coverage

| Directory | Contents | Files |
|---|---|---:|
| `hy/sahmanadrutyun/` | Constitution of 1995 as revised by the 2015 referendum (ARLIS id 143723), consolidated | 1 |
| `hy/orensgrqer/` | codes (Օրենսգիրք) in force: civil, criminal, procedure, labour, tax, land, electoral, judicial, EAEU customs code, … | 18 |
| `hy/orenqner/<year>/` | laws (Օրենք) and constitutional laws in force, by year of adoption (1988–2026) | 982 |
| `en/constitution/` | English translation of the Constitution | 1 |
| `en/codes/` | English translations of codes | 29 |
| `en/laws/<year>/` | English translations of laws | 186 |
| **Total** | | **1,217** |

- Armenian (`hy/`) is the only official language; it is the authoritative text. All 1,004 acts that
  ARLIS returns for "Constitution / Constitutional law / Code / Law", status "in force" or
  "partly in force", with "exclude amending acts" switched on, were downloaded. Three were left
  out because ARLIS still flags them "in force" although they are not current Armenian law:
  the original 1995 Constitution (id 1), the 1995 Constitution as amended in 2005 (id 75780),
  both superseded by the 2015 text, and the WHO Constitution (id 77862, an international treaty).
- English (`en/`): the 216 English acts of type CONSTITUTION / CODE / LAW with status Active /
  Partly active. These are translations sent to ARLIS for publication; they are **not
  authoritative** and often lag behind the Armenian text (the front matter `last_amended` / the
  first quoted line show which amendments they include). ARLIS keeps several English editions
  of some codes (e.g. Tax Code, Labour Code) as separate acts; each is kept as its own file.
- Each file name is `<ARLIS act id>-<transliterated title>.md`. Front matter: `identifier` (act
  number, e.g. ՀՕ-239), `arlis_id`, adoption `date`, `entry_into_force`, `last_amended` (start
  date of the current consolidated version), `status_text` (ARLIS status), `publication`
  (official gazette reference), `source` (the ARLIS page).
- Structure: parts / sections (ԲԱԺԻՆ, ՀԱՏՎԱԾ) / chapters (ԳԼՈՒԽ) become `##`… headings in order
  of appearance and articles (Հոդված) the deepest heading. Editorial notes of ARLIS on
  amendments (e.g. *(հոդվածը լրաց. 16.12.16 ՀՕ-36-Ն)*) are kept in italics; ARLIS warnings shown
  above a text are kept as a `>` quote. Complex tables are kept as HTML tables.
- Normalisation: the source HTML (from Word) letter-spaces some words ("Գ Լ ՈՒ Խ", "Օ ՐԵՆՔ",
  "Տ նտեսական"); such spacing artefacts (a single capital letter separated from the rest of its
  word) are joined. Links to case law (⚖) and images are dropped.

## Not covered

- Secondary legislation (government decisions, ministerial orders, decrees of the President,
  Central Bank acts…), local acts, court decisions and ECHR judgments that ARLIS also hosts.
- Amending laws (their content is already merged in the consolidated texts) and repealed acts.
- Russian translations (ARLIS has about 980; Russian is not an official language of Armenia).
- Images embedded in some acts (forms, maps) — text only.

## Source

- **ARLIS — Armenian Legal Information System** (https://www.arlis.am), operated by
  "Pashtonakan Teghekagir" CJSC for the Ministry of Justice; since 2020 it hosts the *official
  incorporation* (consolidation) of normative acts (Ministry of Justice order 302-N of 3 Aug 2020).
- Access: the site's own search endpoint (`/hy/search/page/<n>?<filters>`) and act pages
  (`/hy/acts/<id>/latest`). arlis.am has no robots.txt and its pages state no restriction on
  automated access; requests were sequential, ≥ 1.5 s apart, with User-Agent
  `LawCodex/1.0 (+https://github.com/LawCodex)`.
- Copyright: under the Law of the Republic of Armenia on Copyright and Related Rights (art. 4),
  official documents — laws and other normative acts and their official translations — are
  not objects of copyright.

## Regenerate

```
python3 -m pip install -r scripts/requirements.txt
python3 scripts/am_fetch.py     # downloads to ../_raw/am/ (cached)
python3 scripts/am_convert.py   # writes hy/ and en/
```
