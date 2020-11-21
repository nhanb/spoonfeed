API docs: https://github.com/4chan/4chan-API

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
- Present matches on a glance-friendly web page, maybe sorted by number of
  replies
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
```
