# Indeed with the Tapline Python SDK

Use the Indeed client to read job postings, companies and reported pay from Indeed's 62 country sites.

[Package guide](../../../README.md) · [Indeed API reference](https://tapline.sh/docs?utm_source=python_client&utm_medium=referral&utm_campaign=developer_acquisition&utm_content=indeed_readme#/indeed)

## Get started

[Create a Tapline account](https://tapline.sh/sign-up?utm_source=python_client&utm_medium=referral&utm_campaign=developer_acquisition&utm_content=indeed_readme) and create an API key on the [API keys page](https://tapline.sh/dashboard?tab=api-keys&utm_source=python_client&utm_medium=referral&utm_campaign=developer_acquisition&utm_content=indeed_readme).

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

Every method except `get_salaries` takes `country`, the Indeed site to read (`us` by default, `gb` for the UK).

| Method | Key inputs | Returns | Credits |
| --- | --- | --- | --- |
| `search_jobs` | `query`, `location`, the filters, `cursor` | up to 25 jobs per page, each with its full record, plus the total and facets | 31 |
| `get_job` | `job_key` | one job: description, pay, company, location, attributes, apply details and applicant count | 3 |
| `list_company_jobs` | `company_key`, the filters, `cursor` | up to 25 of a company's jobs per page | 31 |
| `get_company` | `company_key` | profile, employee ratings, happiness scores, CEO approval, average pay and similar companies | 2 |
| `search_companies` | `query` | companies matching a name, with their keys | 1 |
| `list_company_directory` | `query`, `location` | companies by name, industry or the titles they hire for, with ratings | 1 |
| `get_salaries` | `location`, `job_title`, `company_key` | average reported pay per year, month, week, day and hour | 1 |
| `list_job_title_suggestions` | `query` | job searches for partly typed text | 1 |
| `list_location_suggestions` | `query` | places for partly typed text | 1 |
| `list_popular_searches` | | the searches run most on a country site | 1 |

Paged methods cost their credits per page.

## Search jobs and page through them

```python
cursor = ""
while True:
    page = tapline.indeed.search_jobs(
        query="registered nurse",
        location="Houston, TX",
        job_type=["full_time"],
        posted_within_days=7,
        cursor=cursor,
    )
    for result in page.results:
        job = result.job
        print(job.key, job.title, job.company_name_as_posted, job.pay and job.pay.text)
    if page.pagination.next_cursor is None:
        break
    cursor = page.pagination.next_cursor
```

Send the same search and `limit` with every cursor. `job_type`, `work_setting` and `experience_level` keep jobs matching any of the values you pass; `attribute` and `occupation` keep jobs carrying every code. The `exclude_` filters drop jobs, and keeping and excluding the same value answers 422.

## Read a company and its jobs

```python
companies = tapline.indeed.search_companies(query="google")
company = tapline.indeed.get_company(companies.companies[0].key)
print(company.name, company.ratings.overall, company.ceo.approval)

jobs = tapline.indeed.list_company_jobs(company.key, query="engineer", limit=10)
for result in jobs.results:
    print(result.job.title, result.job.location and result.job.location.label)
```

A job's `company.key` works here too.

## Look up pay

```python
pay = tapline.indeed.get_salaries(location="US/TX/Austin", job_title="registered nurse")
print(pay.reported_pay.report_count, pay.reported_pay.year and pay.reported_pay.year.mean)
```

`location` is Indeed's path: `US`, `US/TX` or `US/TX/Austin`. `list_location_suggestions` returns it as `salary_location` for US cities.

## Read the response

- `job.key` is what `get_job` takes, the same as `jk` in an Indeed viewjob URL. Pass the job's own `country` to `get_job`: Indeed sends a job's pay only on the site it was posted on.
- `pay.text` is the pay as the posting shows it and `pay.posted` the parsed range, exact amount or bound. `pay.estimated` is Indeed's own estimate when the posting has no pay.
- `company` is `None` when Indeed links no company page to the job; `company_name_as_posted` is the name the posting shows.
- `attributes` groups Indeed's codes by kind (job types, work settings, schedules, benefits, education and more). Each `code` works in the `attribute` and `exclude_attribute` filters.
- `applicants` is filled by `get_job`. In search results it is `None`.
- `total.is_estimate` says whether `total.count` is Indeed's estimate. `facets.companies` carries company keys and counts only; Indeed sends no names there.
- `sort="date"` favours recent postings, but Indeed does not order a page strictly by date. Use `posted_within_days` for a cut-off.
- A rating with no reviews is `None`, not zero, and so are happiness scores and CEO approval with no votes.

## Handle errors and check costs

Failed calls raise the errors described in the [package guide](../../../README.md#handle-errors). Validation errors are not charged: an unknown enum value, a kept and excluded filter, a `language` the country site does not offer, a malformed salary location, or a cursor from another search or `limit`. A company key Indeed cannot read answers 400 `invalid_request` on `list_company_jobs`, `search_jobs` (`exclude_company`) and `get_salaries`, and is not charged. An unknown job or company answers 404 on `get_job` and `get_company`, and is charged.

The [Indeed API reference](https://tapline.sh/docs?utm_source=python_client&utm_medium=referral&utm_campaign=developer_acquisition&utm_content=indeed_readme#/indeed) lists the inputs, response fields, and credit cost for each method.
