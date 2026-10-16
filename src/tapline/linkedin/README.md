# LinkedIn with the Tapline Python SDK

Use the LinkedIn client to read public LinkedIn data as linkedin.com shows it to logged-out visitors: member profiles, company, school and showcase pages and their posts, single posts and Pulse articles, video transcripts, job search and job postings. No LinkedIn account is needed.

[Package guide](../../../README.md) · [LinkedIn API reference](https://tapline.sh/docs?utm_source=python_client&utm_medium=referral&utm_campaign=developer_acquisition&utm_content=linkedin_readme#/linkedin)

## Get started

[Create a Tapline account](https://tapline.sh/sign-up?utm_source=python_client&utm_medium=referral&utm_campaign=developer_acquisition&utm_content=linkedin_readme) and create an API key on the [API keys page](https://tapline.sh/dashboard?tab=api-keys&utm_source=python_client&utm_medium=referral&utm_campaign=developer_acquisition&utm_content=linkedin_readme).

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

| Method | Key inputs | Credits | Returns |
| --- | --- | --- | --- |
| `get_profile` | `url`: a `/in/<name>` profile URL | 2 | `LinkedinProfileResponse`: name, headline, location, followers, About, `experience` and `education`, articles, recent posts, publications, projects, recommendations, websites, `similarProfiles` |
| `get_company` | `url`: a `/company/`, `/school/` or `/showcase/` page URL | 1 | `LinkedinCompanyResponse`: id, name, description, location, employee and follower counts, website, industry, size, founding year, specialties, similar and affiliated pages, featured employees, latest posts |
| `get_company_posts` | `url`, `page` (1 to 7) | 1 | `LinkedinCompanyPostsResponse`: 10 `posts` per page with text, counts, `author` and `isRepost`, and `hasNextPage` |
| `get_post` | `url`: a `/posts/`, `/feed/update/urn:li:...` or `/pulse/` URL | 1 | `LinkedinPostResponse`: text, publish time, counts, author, comments, images, `video`, and `moreArticles` for an article |
| `get_post_transcript` | `url`: a post with a native video | 1 | `LinkedinPostTranscriptResponse`: the video's captions as plain text |
| `search_jobs` | `keywords`, `location` or `geo_id`, `distance`, `posted_within`, `company_ids`, `easy_apply`, `cursor` | 1 | `LinkedinJobsSearchResponse`: 10 `jobs` per page and `pagination` |
| `get_job` | `url`: a `/jobs/view/<id>/` URL | 1 | `LinkedinJobResponse`: title, company, location, applicants, salary when published, description, seniority, employment type, industries, `easyApply` |

Field names follow Scrape Creators' LinkedIn endpoints where both exist, without their status and credit metadata. Fields LinkedIn leaves out for a page are `None`.

## Read a profile

```python
with SyncTaplineClient() as tapline:
    profile = tapline.linkedin.get_profile(url="https://www.linkedin.com/in/williamhgates/")

print(profile.name, profile.headline, profile.followers)
for role in profile.experience:
    print(role.name, role.member.title, role.member.startDate, role.member.endDate)
for school in profile.education:
    print(school.name, school.member.title)
for similar in profile.similarProfiles:
    print(similar.name, similar.link)
```

Each `experience` and `education` entry is a schema.org organization: `name` is the company or school and `member` is the role, where `title` is the job title or the degree and field. Dates are a year (`2018`) or a month (`"2018-04"`). LinkedIn masks some members' employers with asterisks for guests; those arrive masked with `member.title` set to `None`.

## Read a company and walk its posts

```python
with SyncTaplineClient() as tapline:
    company = tapline.linkedin.get_company(url="https://www.linkedin.com/company/shopify/")
    print(company.id, company.name, company.followers, company.employeeCount, company.industry)

    page_number = 1
    while True:
        page = tapline.linkedin.get_company_posts(
            url="https://www.linkedin.com/company/shopify/", page=page_number
        )
        for post in page.posts:
            print(
                post.datePublished, post.url, post.author.name, "repost" if post.isRepost else "own"
            )
        if not page.hasNextPage:
            break
        page_number += 1
```

LinkedIn shows guests 7 pages of 10 posts at most. `isRepost` is `True` whenever the post's author is not the page itself, judged against the page LinkedIn serves, so a URL LinkedIn redirects (`/company/stanford-university/` serves the school page) still flags only real reposts.

## Read a post, an article or a video transcript

```python
with SyncTaplineClient() as tapline:
    post = tapline.linkedin.get_post(
        url="https://www.linkedin.com/posts/shopify_activity-7511428251756515329-ezTG"
    )
    print(post.datePublished, post.likeCount, post.commentCount, post.description)
    if post.video:
        print("video", post.video.url)
        transcript = tapline.linkedin.get_post_transcript(url=post.url)
        print(transcript.transcript)
```

A post with no captions answers `NotFoundError` from `get_post_transcript`, and that call is charged.

## Search jobs and page through the results

```python
from tapline import SyncTaplineClient
from tapline.linkedin import PostedWithin

with SyncTaplineClient() as tapline:
    job_ids: list[str] = []
    for page in tapline.linkedin.pages(
        lambda cursor: tapline.linkedin.search_jobs(
            keywords="data engineer",
            location="New York, United States",
            posted_within=PostedWithin.PAST_WEEK,
            cursor=cursor,
        )
    ):
        for card in page.jobs:
            print(card.id, card.title, card.company.name, card.location, card.postedDate)
            job_ids.append(card.id)
        if len(job_ids) >= 30:
            break

    job = tapline.linkedin.get_job(url=f"https://www.linkedin.com/jobs/view/{job_ids[0]}/")
    print(job.title, job.salary, job.easyApply, job.applicants)
```

Each page costs a credit, so break out of the walk once you have enough. When a search ends, `pagination.completion` is `exhausted`; LinkedIn's guest search stops at 1,000 results, and a walk that reaches that cap ends with `depth_limit`. Send `location` or `geo_id`: without either, LinkedIn picks the country of the exit it was asked from. Search cards carry no salary; read it from `get_job`, which has it when the employer published a pay range.

## Handle errors and check costs

Failed calls raise the errors described in the [package guide](../../../README.md#handle-errors).

- A profile, company, post or job LinkedIn does not have raises `NotFoundError` (404, `not_found`). So does a post without captions on `get_post_transcript`. The call is charged.
- A jobs cursor that was not handed out by `search_jobs` raises `InvalidCursorError` (400, `invalid_cursor`), and is not charged.
- A malformed URL, a URL of the wrong kind (a profile URL on `get_company`), a numeric company URL such as `/company/1035/`, or an out-of-range `page`, `distance` or `geo_id` raises `UnprocessableEntityError` (422) before any fetch, and is not charged.
- Upstream failures raise `InternalServerError` (503) and are not charged.

The [LinkedIn API reference](https://tapline.sh/docs?utm_source=python_client&utm_medium=referral&utm_campaign=developer_acquisition&utm_content=linkedin_readme#/linkedin) lists every response field.
