from __future__ import annotations

import math
import random
import re
import time
from datetime import datetime, timezone

from jobspy.model import (
    Compensation,
    CompensationInterval,
    Country,
    DescriptionFormat,
    JobPost,
    JobResponse,
    JobType,
    Location,
    Scraper,
    ScraperInput,
    Site,
)
from jobspy.util import create_logger, create_session, markdown_converter

log = create_logger("Seek")

# Seek only operates in AU and NZ. Everything else falls back to AU.
_REGIONS = {
    Country.AUSTRALIA: {
        "host": "www.seek.com.au",
        "site_key": "AU-Main",
        "locale": "en-AU",
        "country_code": "AU",
        "currency": "AUD",
        "timezone": "Australia/Sydney",
    },
    Country.NEWZEALAND: {
        "host": "www.seek.co.nz",
        "site_key": "NZ-Main",
        "locale": "en-NZ",
        "country_code": "NZ",
        "currency": "NZD",
        "timezone": "Pacific/Auckland",
    },
}

_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.0 Safari/605.1.15"
)

_WORK_TYPE_MAP = {
    "full time": JobType.FULL_TIME,
    "part time": JobType.PART_TIME,
    "contract/temp": JobType.CONTRACT,
    "contract": JobType.CONTRACT,
    "casual/vacation": JobType.PART_TIME,
    "internship": JobType.INTERNSHIP,
}

_INTERVAL_MAP = [
    (("year", "annum", "annual", "p.a", "pa"), CompensationInterval.YEARLY),
    (("month",), CompensationInterval.MONTHLY),
    (("week",), CompensationInterval.WEEKLY),
    (("day",), CompensationInterval.DAILY),
    (("hour",), CompensationInterval.HOURLY),
]


class Seek(Scraper):
    def __init__(
        self,
        proxies: list[str] | str | None = None,
        ca_cert: str | None = None,
        user_agent: str | None = None,
    ):
        super().__init__(Site.SEEK, proxies=proxies, ca_cert=ca_cert)
        self.scraper_input = None
        self.session = None
        self.region = _REGIONS[Country.AUSTRALIA]
        self.delay = 2
        self.band_delay = 2

    def scrape(self, scraper_input: ScraperInput) -> JobResponse:
        self.scraper_input = scraper_input
        self.region = _REGIONS.get(scraper_input.country, _REGIONS[Country.AUSTRALIA])
        self.session = create_session(
            proxies=self.proxies, ca_cert=self.ca_cert, is_tls=False, has_retry=True
        )
        self.session.headers.update(
            {"User-Agent": _USER_AGENT, "Accept": "application/json"}
        )

        results_wanted = scraper_input.results_wanted or 15
        job_list: list[JobPost] = []
        page = 1

        while len(job_list) < results_wanted:
            log.info(f"search page: {page}")
            data = self._fetch_page(page)
            if not data:
                break
            jobs = data.get("data") or []
            if not jobs:
                break

            for job in jobs:
                try:
                    job_post = self._process_job(job)
                    if job_post:
                        job_list.append(job_post)
                        if len(job_list) >= results_wanted:
                            break
                except Exception as e:
                    log.error(f"Seek: error processing job: {str(e)}")
                    continue

            # Stop if we've consumed every page Seek reports.
            total = data.get("totalCount") or 0
            page_size = (data.get("solMetadata") or {}).get("pageSize") or len(jobs)
            if page_size and page * page_size >= total:
                break

            page += 1
            time.sleep(random.uniform(self.delay, self.delay + self.band_delay))

        return JobResponse(jobs=job_list[:results_wanted])

    def _fetch_page(self, page: int) -> dict | None:
        params = {
            "siteKey": self.region["site_key"],
            "sourcesystem": "houston",
            "page": page,
            "locale": self.region["locale"],
            "include": "seodata",
        }
        if self.scraper_input.search_term:
            params["keywords"] = self.scraper_input.search_term
        if self.scraper_input.is_remote:
            params["workarrangement"] = "2"  # Seek code for remote
        elif self.scraper_input.location:
            params["where"] = self.scraper_input.location
        if self.scraper_input.hours_old:
            params["daterange"] = max(1, math.ceil(self.scraper_input.hours_old / 24))

        url = f"https://{self.region['host']}/api/jobsearch/v5/search"
        try:
            response = self.session.get(url, params=params, timeout=self.scraper_input.request_timeout)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            log.error(f"Seek: error fetching search page {page} - {str(e)}")
            return None

    def _process_job(self, job: dict) -> JobPost | None:
        job_id = job.get("id")
        if not job_id:
            return None
        job_id = str(job_id)
        title = job.get("title")
        if not title:
            return None

        job_url = f"https://{self.region['host']}/job/{job_id}"
        company_name = job.get("companyName") or (job.get("advertiser") or {}).get(
            "description"
        )

        locations = job.get("locations") or []
        city = locations[0].get("label") if locations else job.get("location")
        location = Location(
            city=city,
            country=self.scraper_input.country or Country.AUSTRALIA,
        )

        work_arrangements = (job.get("workArrangements") or {}).get("displayText")
        is_remote = bool(work_arrangements) and "remote" in work_arrangements.lower()

        description = None
        if self.scraper_input.linkedin_fetch_description:
            description = self._fetch_description(job_id)

        return JobPost(
            id=f"se-{job_id}",
            title=title,
            company_name=company_name,
            job_url=job_url,
            location=location,
            job_type=self._parse_job_type(job.get("workTypes")),
            compensation=self._parse_compensation(job.get("salaryLabel")),
            date_posted=self._parse_date(job.get("listingDate")),
            is_remote=is_remote,
            work_from_home_type=work_arrangements,
            description=description,
        )

    def _fetch_description(self, job_id: str) -> str | None:
        url = f"https://{self.region['host']}/graphql"
        payload = {
            "operationName": "jobDetails",
            "variables": {
                "jobId": job_id,
                "locale": self.region["locale"],
                "languageCode": "en",
                "countryCode": self.region["country_code"],
                "timezone": self.region["timezone"],
            },
            "query": (
                "query jobDetails($jobId: ID!) { jobDetails(id: $jobId) "
                "{ job { content(platform: WEB) } } }"
            ),
        }
        try:
            response = self.session.post(
                url,
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "seek-request-brand": "seek",
                    "seek-request-country": self.region["country_code"],
                },
                timeout=self.scraper_input.request_timeout,
            )
            response.raise_for_status()
            content = (
                (((response.json() or {}).get("data") or {}).get("jobDetails") or {})
                .get("job")
                or {}
            ).get("content")
            if not content:
                return None
            if self.scraper_input.description_format == DescriptionFormat.MARKDOWN:
                return markdown_converter(content)
            return content
        except Exception as e:
            log.error(f"Seek: error fetching description for {job_id} - {str(e)}")
            return None

    @staticmethod
    def _parse_job_type(work_types: list | None) -> list[JobType] | None:
        if not work_types:
            return None
        types = []
        for wt in work_types:
            mapped = _WORK_TYPE_MAP.get(str(wt).strip().lower())
            if mapped and mapped not in types:
                types.append(mapped)
        return types or None

    def _parse_compensation(self, salary_label: str | None) -> Compensation | None:
        if not salary_label:
            return None
        amounts = self._extract_amounts(salary_label)
        interval = self._extract_interval(salary_label)
        if not amounts and not interval:
            return None
        min_amount = amounts[0] if amounts else None
        max_amount = amounts[1] if len(amounts) > 1 else min_amount
        return Compensation(
            interval=interval,
            min_amount=min_amount,
            max_amount=max_amount,
            currency=self.region["currency"],
        )

    @staticmethod
    def _extract_amounts(text: str) -> list[float]:
        amounts = []
        for raw in re.findall(r"\$?\s*([\d,]+(?:\.\d+)?)\s*([kK])?", text):
            number, suffix = raw
            number = number.replace(",", "")
            if not number or number == ".":
                continue
            try:
                value = float(number)
            except ValueError:
                continue
            if suffix:
                value *= 1000
            # Ignore stray small numbers (e.g. "10% super") that aren't wages.
            if value >= 100:
                amounts.append(value)
        return amounts[:2]

    @staticmethod
    def _extract_interval(text: str) -> CompensationInterval | None:
        lowered = text.lower()
        for keywords, interval in _INTERVAL_MAP:
            if any(k in lowered for k in keywords):
                return interval
        return None

    @staticmethod
    def _parse_date(listing_date: str | None):
        if not listing_date:
            return None
        try:
            cleaned = listing_date.replace("Z", "+00:00")
            return datetime.fromisoformat(cleaned).astimezone(timezone.utc).date()
        except (ValueError, TypeError):
            return None
