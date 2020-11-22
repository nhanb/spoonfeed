Shitty source code for https://spoonfeed.pytaku.com/

Deps: `urllib3 beautifulsoup4`

If you're RUNNING ARCH BTW:

```sh
doas pacman -S python-urllib3 python-beautifulsoup4
```

# What

Scrapes 4chan's "one page threads" (/opt/) to find interesting manga titles.

# How

- Periodically check /opt/
- Run images throught saucenao
- Present matches on a glance-friendly web page, sorted by number of (You)s
- Profit(?)

# Using

```sh
# create conf.json
{
    "SAUCENAO_API_KEY": "FILL_ME",
    "OUTPUT_PATH": "out"
}

# then just run
python main.py

# which will generate a static website into OUTPUT_PATH that you can serve
# using nginx or caddy.
```

# Yakshaving ideas

- Cache saucenao results: because their API has strict 30s and daily rate
  limits.
- Store everything in sqlite: may allow for incremental updates & more powerful
  derived metrics.
