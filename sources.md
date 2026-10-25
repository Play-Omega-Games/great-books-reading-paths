# Great Books: sources, license notes and verification

Built Oct 25, 2026 by build.py (six paths: stoics, shakespeare, homer, plato, dante, tragedies) (run `python3 build.py --fetch` to download sources into ./src and rebuild). Link check: check_links.py.
Source names and translators stay in these files only; nothing user-facing credits them (John's rule).

## Stoics (stoics.json, 365 days)
| Work | Translation | Exact source | License |
|---|---|---|---|
| Epictetus, Enchiridion (52 chapters in this edition) | George Long, 1877 | https://en.wikisource.org/wiki/The_Discourses_of_Epictetus;_with_the_Encheiridion_and_Fragments/The_Encheiridion_or_Manual | Public domain (Long died 1879) |
| Epictetus, Discourses, Books 1-4 (95 chapters) | George Long, 1877 | https://en.wikisource.org/wiki/The_Discourses_of_Epictetus;_with_the_Encheiridion_and_Fragments (subpages Book_N/Chapter_M) | Public domain |
| Marcus Aurelius, Meditations (The Thoughts), Books I-XII | George Long | https://www.gutenberg.org/cache/epub/15877/pg15877.txt and pg15877-images.html (PG #15877) | Public domain |
| Seneca, Moral Letters to Lucilius, 1-124 | Richard Mott Gummere, Loeb 1917-1925 | https://en.wikisource.org/wiki/Moral_letters_to_Lucilius (subpages Letter_N) | Public domain in the US (published before 1930). Gummere died 1969, so it is still under copyright in life-plus-70 countries until 2040. |

Note: PG #2680 "Meditations" is not Long's translation, so it was not used. PG #10661 is only a selection of Long's Discourses, so the full Wikisource edition was used instead.
Plan: days 1-18 Enchiridion; days 19-365 interleave Meditations (102 days, section groups, each book's share proportional to its length), Seneca (145 days) and Discourses (100 days) so all three end on day 365. Letters or chapters over 3,000 words are split at paragraph breaks into parts (22 items become 48 days); each part records its opening words.
Verification: every Wikisource page's header checked for translator and section (book/chapter or letter number), with body text over 80 words; Meditations section numbers parsed in sequence from the Long text; Enchiridion chapters I-LII parsed in sequence. 365 of 365 verified.

## Shakespeare (shakespeare.json, 190 days)
| Source | License |
|---|---|
| The Complete Works of William Shakespeare, Project Gutenberg #100: https://www.gutenberg.org/cache/epub/100/pg100-images.html (act links use its scene anchors) and https://www.gutenberg.org/cache/epub/100/pg100.txt | Public domain text. Project Gutenberg's trademark terms only apply when redistributing their files with the name; we link to them. |
Plan: 38 plays, 5 acts each. Twelve best-known plays first, then the English histories in story order (King John to Henry VIII), then the rest alternating comedies, tragedies and romances. The Taming of the Shrew's Induction is read with Act I. Poems and Sonnets are not included.
Verification: act and scene anchors parsed from the HTML edition; each play's five ACT headings confirmed in the plain-text edition. 190 of 190 verified.

## Homer (homer.json, 112 days)
| Work | Translation | Exact source | License |
|---|---|---|---|
| Iliad, 24 books (61 days) | Samuel Butler, prose, 1898 | https://www.gutenberg.org/cache/epub/2199/pg2199.txt and pg2199-images.html (PG #2199) | Public domain worldwide (Butler died 1902) |
| Odyssey, 24 books (51 days) | Samuel Butler, prose, 1900 | https://www.gutenberg.org/cache/epub/1727/pg1727.txt and pg1727-images.html (PG #1727) | Public domain worldwide. This file carries a 1921 preface by Henry Festing Jones, which we do not use. |
Plan: each book split at paragraph breaks into parts of about 2,000 to 3,000 words (1,644 to 3,062, average 2,425). The Iliad's short Butler book summaries are kept as `book_summary`.

## Plato (plato.json, 125 days)
Translation: Benjamin Jowett (died 1893), public domain worldwide. Dialogue text only; Jowett's introductions are excluded.
| Dialogue | PG # | Days |
|---|---|---|
| Euthyphro | 1642 | 3 |
| Apology | 1656 | 4 |
| Crito | 1657 | 2 |
| Phaedo | 1658 | 10 |
| Symposium | 1600 | 8 |
| Phaedrus | 1636 | 8 |
| Meno | 1643 | 5 |
| Gorgias | 1672 | 13 |
| Republic (Books I-X) | 1497 | 42 |
| Protagoras | 1591 | 8 |
| Theaetetus | 1726 | 11 |
| Timaeus | 1572 | 11 |
Each at https://www.gutenberg.org/cache/epub/<id>/pg<id>.txt and pg<id>-images.html. Parts of about 2,000 to 3,000 words (1,892 to 3,515, average 2,814).

## Dante (dante.json, 100 days)
Translation: Henry Wadsworth Longfellow, 1867 (died 1882), public domain worldwide. Source: https://www.gutenberg.org/cache/epub/1004/pg1004.txt and pg1004-images.html (PG #1004, complete). One canto a day: Inferno 34, Purgatorio 33, Paradiso 33. Verification: each canto heading found in the plain text (115 to 160 verse lines each; Paradiso XXXIII has 145) and its HTML anchor (#CantoI.I style) confirmed.

## Greek tragedies (tragedies.json, 107 days)
All translators below died more than 70 years ago and published before 1929, so every play is public domain worldwide. None is US-only.
| Author | Plays (days) | Translation | Exact source | License |
|---|---|---|---|---|
| Aeschylus | Agamemnon (7), The Libation Bearers (4), The Eumenides (4) | E. D. A. Morshead, 1881 (died 1912) | https://www.gutenberg.org/cache/epub/8604/pg8604-images.html (PG #8604) | Worldwide PD |
| Aeschylus | Prometheus Bound (4), The Persians (4), Seven Against Thebes (4), The Suppliant Maidens (4) | E. D. A. Morshead, 1908 | https://www.gutenberg.org/cache/epub/8714/pg8714-images.html (PG #8714) | Worldwide PD |
| Sophocles | Oedipus the King (6), Oedipus at Colonus (6), Antigone (5) | Francis Storr, 1912 (died 1919) | https://www.gutenberg.org/cache/epub/31/pg31-images.html (PG #31) | Worldwide PD |
| Sophocles | Ajax (5), Electra (6), The Women of Trachis (5), Philoctetes (5) | Lewis Campbell, 1883, rev. 1896 (died 1908) | https://www.gutenberg.org/cache/epub/14484/pg14484-images.html (PG #14484) | Worldwide PD |
| Euripides | Alcestis (5), Medea (6), Hippolytus (6), The Trojan Women (5), Ion (7), The Children of Heracles (4), The Bacchae (5) | Edward Philip Coleridge, prose, 1891 (died 1936) | https://en.wikisource.org/wiki/The_Plays_of_Euripides_(Coleridge) (subpages Alcestis, Medea, Hippolytus, The_Trojan_Women, Ion, Heracleidae, The_Bacchantes) | Worldwide PD |
Choices: Jebb's and Plumptre's Sophocles are not on Project Gutenberg, so Storr (three Theban plays) and Campbell (the other four) were used. Coleridge's Euripides is only on Wikisource, where ten of the nineteen plays are transcribed; Helen is only partly transcribed, so The Children of Heracles replaced it. Gilbert Murray's versions on Gutenberg were avoided because they are public domain in the US only (Murray died 1957).
Plan: Aeschylus, then Sophocles, then Euripides, one episode or scene group a day: each play split at speech breaks into parts of about 2,200 words (1,366 to 2,950), preferring a break just before a choral passage.

## Verification for homer, plato and tragedies
Book, dialogue, Republic-book and play boundaries come from headings in the plain text (24 + 24 Homer books, 10 Republic books, 14 Gutenberg plays by their cast-list headings). Each part's opening words were then found in the HTML edition, and the link uses the nearest anchor before them (a book, dialogue or play anchor; scroll to the opening words for later parts). Euripides pages were checked for translator in the Wikisource header. All days verified: homer 112/112, plato 125/125, dante 100/100, tragedies 107/107.

## US-only public domain flag
Only Gummere's Seneca (in the Stoics path) is public domain in the US only. Every other text in all six paths is public domain worldwide.

## Link check (Oct 25, 2026)
check_links.py: every unique page URL across all six datasets, 248 URLs, all HTTP 200.
