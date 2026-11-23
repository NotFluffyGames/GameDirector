# Research sources

What game-research fetches, on whose terms, and how game-setup checks each host. Every number read from these carries its link and retrieval date into the page that uses it; a number nobody fetched in a session reads `not researched: <why>`.

## Reachability

game-setup probes each host once, and game-research re-probes a host before giving up on it:

```sh
curl -g -sS -o /dev/null -w '%{http_code} %{http_connect}\n' --max-time 15 '<probe>'
```

Any HTTP status from the host means it is reachable: record the code. An unkeyed GetAppReviews call may answer 429, and a bad parameter 400; both still reach it. Only no response is unreachable: `000` from a timeout or a DNS failure, or a proxy refusal (`000` with a `403` connect code and curl's "CONNECT tunnel failed"), recorded with what curl printed. App 1145360 is a known Steam app to probe with.

| Host | Probe | What research loses without it |
| --- | --- | --- |
| `store.steampowered.com` | `https://store.steampowered.com/api/appdetails?appids=1145360` | prices, release dates, genres, screenshots, trailers |
| `api.steampowered.com` | `https://api.steampowered.com/IUserReviewsService/GetAppReviews/v1/?appid=1145360&num_per_page=1&languages[0]=all` | review counts (so every `sell` range), complaints |
| `steamspy.com` | `https://steamspy.com/api.php?request=appdetails&appid=1145360` | the owners cross-check, user tags, tag lists for saturation |
| `itch.io` | `https://itch.io/games/html5.xml` | `hobby` comps, browser-playable references |

SteamDB is never probed: it is never fetched (below).

## Steam

### Reviews: `IUserReviewsService/GetAppReviews`

`https://api.steampowered.com/IUserReviewsService/GetAppReviews/v1/?appid=<appid>&languages[0]=all&num_per_page=100&cursor=*`, then the returned `cursor` (URL-encoded) for the next page.

- **All languages, always.** Left out, `languages` means English only, which undercounts against the store and the multipliers below.
- **Purchase type: the default (Steam purchases).** The store's "All Reviews" count, which the multipliers were calibrated against, leaves out key activations ([Birkett 2018](https://www.gamedeveloper.com/business/using-steam-reviews-to-estimate-sales)).
- **Enum parameters** (`filter`, `review_type`, `purchase_type`) take integers. Pass one only when a source read in this session gives its value, and cite it; otherwise leave them at their defaults and split negative from positive by each review's `voted_up`. The default `filter` (Helpful) widens its day range until it finds reviews, so paging with it may not end: stop at the page count you need.
- **What it gives:** on the first page the totals (`total_reviews`, `total_positive`, `review_score_desc`); per review its text, `voted_up`, `language`, `playtime_at_review`, timestamps and `recommendationid`. Filters by date and by playtime hours (`playtime_min_hours`, `playtime_max_hours`).
- **Terms:** no key needed; a publisher key raises the limit. Unkeyed calls share a lower limit and get HTTP 429: wait and retry later, one request at a time. Anonymous responses may be cached for up to 10 minutes.
- The older `store.steampowered.com/appreviews/<appid>?json=1` was scheduled to be disabled on 22 October 2026 (a Steamworks announcement, read only as a search summary). Use it only when GetAppReviews fails and it still answers, with `language=all`.

Parameters from the generated listing [xPaw/SteamWebAPIDocumentation](https://github.com/xPaw/SteamWebAPIDocumentation) (`api.json`).

### Store data: `appdetails`

`https://store.steampowered.com/api/appdetails?appids=<appid>&cc=us&l=english`, one app per call. No key; undocumented. About 200 requests per 5 minutes per IP, as observed by third parties (not stated by Valve): pace the calls.

It gives the name, `price_overview`, `genres`, `categories`, `release_date`, `platforms`, the descriptions, `screenshots` (each with `path_thumbnail`, a 600×338 JPEG, and `path_full`) and `movies` (trailers). User tags aren't in it: take them from SteamSpy or the store page, or record them not researched. An app id is in the game's store URL (`/app/<appid>/`).

### Achievements

`https://api.steampowered.com/ISteamUserStats/GetGlobalAchievementPercentagesForApp/v2/?gameid=<appid>`: how far players get, for anchors and session norms. Documented, no key; the Steam Web API terms cap use at 100,000 calls a day.

## SteamSpy

`https://steamspy.com/api.php?request=appdetails&appid=<appid>` (owner range, average and median playtime, tags) and `request=tag&tag=<Tag>` (the games in a tag). `request=all` at most once a minute; other calls at most once a second (sources quote four a second or one; keep to one).

Unofficial. Since Valve hid game libraries in April 2018 its owner counts are model estimates: its creator reported 90% of about 70 known games within 10%, and outliers up to fivefold ([Kotaku 2018](https://kotaku.com/steam-spy-is-back-but-not-as-accurate-as-before-1825608646)). Use it as a cross-check beside the review-count range, never as a comp's only number.

## itch.io

Any browse page becomes an RSS feed when `.xml` is appended to its URL: `https://itch.io/games/tag-<tag>.xml`, `https://itch.io/games/html5.xml` (browser-playable games), with the filters the site's browse URLs carry. It gives titles, links, prices and platforms. A game's itch.io page shows ratings and comments, which the complaints read, but no sales numbers, so its comps carry no units range; its server-side API covers only your own games.

## SteamDB

Off limits to an agent: its FAQ says "We also do not allow scraping/crawling", and it has no API. A person may read it for homework.

## Others, only with the person's access

IGDB (Twitch client credentials, 4 requests a second), RAWG (a key, 20,000 requests a month, an active link back required), Apple's iTunes Search API (meant for search fields on a website; its assets only to promote store content), Google Play (no public catalogue API), and paid estimators (Gamalytic, VG Insights, Sensor Tower). Use one only when the person gives access, on its own terms.

## Review counts to units, by launch year

Steam publishes reviews, not sales. Units are estimated as the review count times a ratio, which fell after Steam began prompting players to review at the end of October 2019. Take the count across all languages (`total_reviews`), the ratio for the comp's **launch year**, and state the result as a range with its date and sources. For a 2021 launch with 1,200 reviews read on 2026-11-23: 24,000–72,000 units (20–60×, Carless 2020).

| Launch year | Units per review | Sources |
| --- | --- | --- |
| before 2014 | 40–100× | Kontus 2021 |
| 2014–2017 | 30–150×; medians 64–74× | Birkett 2018 (50+ premium indie games, range 30–150×; post-2014 launches median 64×, 2017 median 65×); Carless 2020 (pre-2017 median 74×) |
| 2018–2019 | 25–100×; 2019 median 51× | Carless 2020 (25–100× is the middle 80% of all 237 games; no range for these years alone was found) |
| 2020 and later | 20–60×; medians 30–38× | Carless 2020 (2020 launches 20–60×, median 38×); Kontus 2021 (2020+ launches 20–55×, best guess 30×) |

No ratio published after 2021 was found: for later launches use the last row and say so.

- **A launch-year ratio, not a lifetime one:** one game's lifetime ratio was 30× while its 2020-only ratio was 14×.
- **Genre and price shift it:** roguelikes, simulation and strategy run higher, story-led adventure and puzzle lower (Birkett); MMOs higher, sports and racing lower, and higher prices lower the ratio (Kontus). These ranges are for premium games: a free-to-play comp gets no units range.
- **Units aren't revenue:** net is "realistically 30%–50%" of units times list price after regional pricing, discounts, refunds, VAT and Steam's cut (Carless). Weinbaum used 0.38, and put his own estimates at 50% to 300% of the actual figure.
- **A range, never a point:** "1000 reviews could mean 30,000 to 150,000 sales" (Birkett).

Sources: [Birkett 2018](https://www.gamedeveloper.com/business/using-steam-reviews-to-estimate-sales), [Carless 2020](https://www.gamedeveloper.com/business/how-that-game-sold-on-steam-using-the-nb-number-2), [Kontus 2021](https://www.gamedeveloper.com/business/how-to-estimate-steam-video-game-sales-in-2021-), [Weinbaum 2019](https://www.gamedeveloper.com/business/genre-viability-on-steam-and-other-trends---an-analysis-using-review-count).

## Saturation (`sell` only)

Read a genre by the share of its games that earn above a threshold, not by how many there are. Weinbaum ranked tags by the share of games grossing over $200,000, ignored games with fewer than 10 reviews, and distrusted tags with fewer than 30 games or more than 2,000. Example: platformer had 1,166 games, 7% over $200k, against FPS with 655 games and 21% ([Carless 2020](https://www.gamedeveloper.com/business/analyzing-the-top-steam-tags-2)). Compute it from SteamSpy's tag list and the ranges above, dated, or record it not researched. It states the odds; it never drops a direction.

## Methods and terms

- **Comps by proximity.** Start from the seed's nearest games, then each close match's "More like this" games, sorted into rings from "most like ours" to "something in common" ([Wagner 2021](https://www.gamedeveloper.com/business/marketing-for-indie-devs-market-research)). Pick three to five (a `sell` scan needs at least three), from the last two or three years, mixing a hit, a middling seller and a weak one; a small team's comps are never only giants.
- **Complaints.** Pull each comp's negative reviews in all languages, with playtime at review, cluster them into themes, count them, and quote one line per theme with its `recommendationid`. In a study of 11 million Steam reviews, 57% of negative reviews mentioned game design and 17% bugs, and most negative reviews came within the first seven hours of play (Lin et al. 2019, via [PC Gamer](https://www.pcgamer.com/steam-study-finds-users-leave-negative-reviews-more-quickly-than-positive-ones/)). Shoppers read negative reviews for flaws in what they care about and discount rants ([Zukowski 2019](https://www.gamedeveloper.com/business/how-steam-users-see-your-game)).
- **Anchors and the hook.** Anchors are what make a game familiar to its genre's players (a metroidvania needs a map); the hook is what makes it unique. One phrase pairs them: "a soulslike metroidvania" ([Logan 2020](https://www.gamedeveloper.com/business/indie-insights-hooks-and-anchors)). The **genre default** is what most games of the kind do; the game departs from it on purpose.
- **The player, by motivation.** Quantic Foundry's twelve motivations in six pairs say who the game is for: Action (Destruction, Excitement), Social (Competition, Community), Mastery (Challenge, Strategy), Achievement (Completion, Power), Immersion (Fantasy, Story), Creativity (Design, Discovery). Name two or three the comps and the loop serve, and those deliberately not served. Self-Determination Theory's needs (autonomy, competence, relatedness), with PENS's presence and intuitive controls, say what any satisfying game must give: a check the loop must pass whatever the audience. Bartle's types describe MUD players: vocabulary only. Write the player as "plays X, Y and Z; wants A and B; leaves at C".
- **References per aspect.**

  | Aspect | Record | Avoid |
  | --- | --- | --- |
  | Play | the mechanic or structure borrowed, the anchor it represents, the comps' complaints about it | copying a comp's loop whole |
  | Look | the shape, palette, value or UI rule taken, and what not to take | a mood board with no rule an asset could fail |
  | Sound | instruments, emotion, tempo, what the player must hear | attachment to a temp track |
  | Feel | per core verb, the moment, the adjective it shows, the timing to match | what the engine or input device can't match |
  | Tone and world | the tone words, and the words to avoid | names, art or logos that would ship: with a selling goal they can't |

- **Left out:** a total-market figure, demographic labels without behaviour, and point estimates.
