# Great Books Reading Paths

This repo holds Omega Games' public-domain Great Books reading plans: the Stoics, Shakespeare one act a day, Homer, Plato's dialogues, Dante one canto a day, and the Greek tragedies. Each plan is a JSON list of daily readings with a reference and a full-text link, and it powers the Great Books: Reading Paths Grok Bot template.

A bot loads a plan from `https://raw.githubusercontent.com/Play-Omega-Games/great-books-reading-paths/main/plans/<path>.json`. `build.py` rebuilds the plans from public sources (`python3 build.py --fetch`) and `check_links.py` checks the links. Questions or translation requests go to john@playomega.games.
