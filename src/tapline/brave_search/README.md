# Brave Search with the Tapline Python SDK

Use the Brave Search client to read search.brave.com: web, news, video and image results, Brave's AI answers with their sources, places and directions, sports standings and games, and Goggles.

[Package guide](../../../README.md) · [Brave Search API reference](https://tapline.sh/docs?utm_source=python_client&utm_medium=referral&utm_campaign=developer_acquisition&utm_content=brave_search_readme#/brave_search)

## Get started

[Create a Tapline account](https://tapline.sh/sign-up?utm_source=python_client&utm_medium=referral&utm_campaign=developer_acquisition&utm_content=brave_search_readme) and create an API key on the [API keys page](https://tapline.sh/dashboard?tab=api-keys&utm_source=python_client&utm_medium=referral&utm_campaign=developer_acquisition&utm_content=brave_search_readme).

Install the package and save your key in `TAPLINE_API_KEY`:

```sh
pip install tapline
export TAPLINE_API_KEY="your-api-key"
```

```python
import os

from tapline import SyncTaplineClient

tapline = SyncTaplineClient(api_key=os.environ["TAPLINE_API_KEY"])
```

The async `TaplineClient` accepts the same `api_key=` argument. If you omit it, both clients read `TAPLINE_API_KEY`.

## What you can do

The web, news and video searches take `country`, `safe_search`, `freshness` and `search_language`. Web and news also take a `date_from`/`date_to` range.

| Method | Key inputs | Returns | Credits |
| --- | --- | --- | --- |
| `search` | `query`, the filters, `spellcheck`, `goggle_url`, `cursor` | 20 web results per page with the news, videos, places, discussions, cards and AI answer shown beside them | 5 |
| `get_ai_answer` | `conversation_id` | Brave's AI-written answer in markdown, with its sources and follow-up questions | 5 |
| `search_news` | `query`, the filters, `cursor` | news articles with their outlet and relative age | 5 |
| `search_videos` | `query`, the filters, `cursor` | videos with their creator, duration and thumbnail | 5 |
| `search_images` | `query`, `country`, `safe_search` | up to 200 images in one page | 5 |
| `list_similar_images` | `token` | images that look like an image result | 5 |
| `list_suggestions` | `query` | autocomplete suggestions, with entity names and pictures | 1 |
| `search_places` | `query`, `latitude`, `longitude` | up to 100 businesses, addresses and areas within about 8 km | 8 |
| `list_place_suggestions` | `query`, `latitude`, `longitude` | place autocomplete near the point | 1 |
| `get_place` | `place_id` | one place: address, phone, hours, photos, ratings and reviews | 5 |
| `get_place_description` | `place_id` | Brave's AI-written description of the place in markdown | 1 |
| `get_directions` | `origin`, `destination`, `via`, `profile`, `avoid`, a departure or arrival time | driving, walking or cycling routes with turn-by-turn steps | 1 |
| `get_transit_directions` | `origin`, `destination`, `exclude_modes`, `max_changes`, `max_walking_meters`, `wheelchair_accessible`, a time | public transit routes with lines, stops and departure times | 1 |
| `get_sports_standings` | `sport`, `league_id`, `season` | a league's table | 1 |
| `list_sports_games` | `sport`, `league_id`, `season`, `date` | a league's games in one matchday | 1 |
| `list_team_games` | `team_id`, `sport`, `season` | a team's games in a season | 1 |
| `get_sports_fixture` | `fixture_id`, `sport`, `league_id`, `season` | one game with events, lineups and statistics | 1 |
| `list_goggles` | | popular Goggles, the rule sets that re-rank results | 1 |
| `search_goggles` | `query` | Goggles matching a name | 1 |
| `get_goggle` | `goggle_url` | one Goggle | 1 |

Paged methods cost their credits per page.

## Search and read the AI answer

```python
page = tapline.brave_search.search(query="why do cats purr", freshness="past_year")
for result in page.results:
    print(result.title, result.url, result.site.domain)

if page.ai_answer and page.ai_answer.is_possible:
    answer = tapline.brave_search.get_ai_answer(conversation_id=page.ai_answer.conversation_id)
    print(answer.markdown)
    for source in answer.sources:
        print(source.title, source.url)
```

`get_ai_answer` takes the `conversation_id` of a recent search. Brave kept the ids we tested readable for at least 90 minutes.

Queries take `site:`, quotes, `-term`, `OR`, `filetype:` and `inbody:`. Brave asks for a captcha on `intitle:`, `inurl:`, `intext:`, `inanchor:` and their `allin` forms, and on `site:linkedin.com/in` in web search, so the API answers those with an uncharged 422. Use `site:www.linkedin.com/in` for profiles.

## Page through results

```python
cursor = ""
while True:
    page = tapline.brave_search.search_news(query="openai", cursor=cursor)
    for article in page.results:
        print(article.title, article.age_label)
    if page.pagination.next_cursor is None:
        break
    cursor = page.pagination.next_cursor
```

Send the same filters with every page. Brave serves 6 pages of web results and 2 of news and videos; `pagination.completion` is `exhausted` or `depth_limit` on the last one.

## Find a place

```python
places = tapline.brave_search.search_places(query="pizza", latitude=41.8781, longitude=-87.6298)
if places.places and places.places[0].id:
    place = tapline.brave_search.get_place(places.places[0].id)
    print(place.title, place.address.display_address, place.contact and place.contact.telephone)
```

## Read a league table

```python
table = tapline.brave_search.get_sports_standings(sport="football", league_id="39", season="2026")
for row in table.groups[0].standings:
    print(row.rank, row.team.name, row.points, row.form_results)
```

League ids include `39` (Premier League), `12` (NBA), `1` (MLB), `57` (NHL) and `nfl`. Seasons go by start year; the NBA and other two-year basketball seasons take `2026-2027`. Team and game ids come from the standings and games answers.

## Read the response

- Distances are in meters (`distance_meters`) and durations in seconds (`duration_seconds`). When Brave sends a value this API cannot read, the field is `None` and Brave's text is in a `<field>_as_sent` sibling.
- Snippets are plain text. The markup Brave puts in them is in a `<field>_html` sibling, such as `description_html`.
- `site.domain` is the registrable domain, `site.hostname` the full host, and `site.breadcrumbs` the path Brave shows under the title.
- On `search`, `ai_answer.is_possible` says Brave can write an answer for the query and `is_triggered` that Brave opened one on its own. `ai_answer.answer` has the same shape as `get_ai_answer`, with the parts Brave left out set to `None` or empty.
- `get_ai_answer` returns the whole answer in `markdown` and the same text split into `blocks`, one per paragraph Brave streamed, with citations. `usage` is Brave's LLM token count and does not change the credit cost.
- News results carry only a relative age (`age_label`, such as `1 day ago`). Brave's news search sends no timestamp.
- On images, `thumbnail` is the copy Brave displays and `image` the original file. `proxied_url` is Brave's proxy of the original and `resized_url` a larger resized copy. Pass `similar_images_token` to `list_similar_images`; it lasts at least two hours.
- `places[].id` is the id `get_place` and `get_place_description` take; `/search` returns the same ids in `locations.results[].id`.
- A route's `typical_duration_seconds` is its duration without current traffic. Polylines are HERE flexible polylines (`polyline_format`). Times keep the local offset of the place. When there is no route, `routes` is empty and `notices` says why.
- In games answers, `game_times` is the season's matchday calendar and `focus_time` the matchday Brave picked. `status.code` is Brave's code (`FT`, `1H`, `HT`, ...) and `status.label` its wording. `form_results` spells out `form` as `win`, `draw` and `loss`.
- A Goggle's `url` is what `search` takes as `goggle_url`. A Goggle Brave has not indexed is ignored without an error; check one with `get_goggle`.
- Objects typed `BraveSearchUnobservedObject` were empty in every answer Brave gave us. Every key Brave sends in them is kept.

## Handle errors and check costs

Failed calls raise the errors described in the [package guide](../../../README.md#handle-errors). Validation errors are not charged: an unknown enum value, malformed coordinates, half a date range, both a departure and an arrival time, a two-year season outside basketball, or a cursor this API did not issue or that goes past the pages Brave serves. An unknown place, conversation, Goggle, league, team or game answers 404 and is charged. A similar-images token this API cannot decode answers 422 and is not charged; a well-formed token Brave did not sign answers 400 `invalid_request` and is charged, as does a directions or sports request Brave rejects.

The [Brave Search API reference](https://tapline.sh/docs?utm_source=python_client&utm_medium=referral&utm_campaign=developer_acquisition&utm_content=brave_search_readme#/brave_search) lists the inputs, response fields, and credit cost for each method.
