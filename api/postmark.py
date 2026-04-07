import os
import requests


class PostmarkClient:
    def __init__(self):
        self.base_url = os.getenv("POSTMARK_BASE_URL", "https://api.postmarkapp.com")
        self.token = os.getenv("POSTMARK_SERVER_TOKEN", "")
        self.headers = {
            "Accept": "application/json",
            "X-Postmark-Server-Token": self.token,
        }

    def _get(self, endpoint, params=None):
        url = f"{self.base_url}{endpoint}"
        try:
            resp = requests.get(url, headers=self.headers, params=params, timeout=15)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.HTTPError as e:
            return None
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            return None

    def _stats_params(self, from_date=None, to_date=None, tag=None, message_stream=None):
        params = {}
        if from_date:
            params["fromdate"] = from_date
        if to_date:
            params["todate"] = to_date
        if tag:
            params["tag"] = tag
        if message_stream:
            params["messagestream"] = message_stream
        return params

    def get_overview_stats(self, from_date=None, to_date=None, tag=None, message_stream=None):
        params = self._stats_params(from_date, to_date, tag, message_stream)
        return self._get("/stats/outbound", params)

    def get_sends_by_day(self, from_date=None, to_date=None, tag=None, message_stream=None):
        params = self._stats_params(from_date, to_date, tag, message_stream)
        return self._get("/stats/outbound/sends", params)

    def get_opens_by_day(self, from_date=None, to_date=None, tag=None, message_stream=None):
        params = self._stats_params(from_date, to_date, tag, message_stream)
        return self._get("/stats/outbound/opens", params)

    def get_clicks_by_day(self, from_date=None, to_date=None, tag=None, message_stream=None):
        params = self._stats_params(from_date, to_date, tag, message_stream)
        return self._get("/stats/outbound/clicks", params)

    def get_bounces_by_day(self, from_date=None, to_date=None, tag=None, message_stream=None):
        params = self._stats_params(from_date, to_date, tag, message_stream)
        return self._get("/stats/outbound/bounces", params)

    def get_spam_by_day(self, from_date=None, to_date=None, tag=None, message_stream=None):
        params = self._stats_params(from_date, to_date, tag, message_stream)
        return self._get("/stats/outbound/spam", params)

    def get_platform_stats(self, from_date=None, to_date=None, tag=None, message_stream=None):
        params = self._stats_params(from_date, to_date, tag, message_stream)
        return self._get("/stats/outbound/opens/platforms", params)

    def get_client_stats(self, from_date=None, to_date=None, tag=None, message_stream=None):
        params = self._stats_params(from_date, to_date, tag, message_stream)
        return self._get("/stats/outbound/opens/emailclients", params)

    def search_messages(self, count=50, offset=0, recipient=None, from_email=None,
                        tag=None, status=None, subject=None, message_stream=None,
                        from_date=None, to_date=None):
        params = {"count": count, "offset": offset}
        if recipient:
            params["recipient"] = recipient
        if from_email:
            params["fromemail"] = from_email
        if tag:
            params["tag"] = tag
        if status:
            params["status"] = status
        if subject:
            params["subject"] = subject
        if message_stream:
            params["messagestream"] = message_stream
        if from_date:
            params["fromdate"] = from_date
        if to_date:
            params["todate"] = to_date
        return self._get("/messages/outbound", params)

    def get_open_events(self, count=500, offset=0, recipient=None, tag=None,
                        client_name=None, client_company=None, client_family=None,
                        os_name=None, os_family=None, os_company=None,
                        platform=None, region=None, city=None):
        params = {"count": count, "offset": offset}
        if recipient:
            params["recipient"] = recipient
        if tag:
            params["tag"] = tag
        if client_name:
            params["client_name"] = client_name
        if client_family:
            params["client_family"] = client_family
        if client_company:
            params["client_company"] = client_company
        if os_name:
            params["os_name"] = os_name
        if os_family:
            params["os_family"] = os_family
        if os_company:
            params["os_company"] = os_company
        if platform:
            params["platform"] = platform
        if region:
            params["region"] = region
        if city:
            params["city"] = city
        return self._get("/messages/outbound/opens", params)

    def get_click_events(self, count=500, offset=0, recipient=None, tag=None,
                         client_name=None, client_company=None, client_family=None,
                         os_name=None, os_family=None, os_company=None,
                         platform=None, region=None, city=None):
        params = {"count": count, "offset": offset}
        if recipient:
            params["recipient"] = recipient
        if tag:
            params["tag"] = tag
        if client_name:
            params["client_name"] = client_name
        if client_family:
            params["client_family"] = client_family
        if client_company:
            params["client_company"] = client_company
        if os_name:
            params["os_name"] = os_name
        if os_family:
            params["os_family"] = os_family
        if os_company:
            params["os_company"] = os_company
        if platform:
            params["platform"] = platform
        if region:
            params["region"] = region
        if city:
            params["city"] = city
        return self._get("/messages/outbound/clicks", params)

    def get_message_streams(self):
        return self._get("/message-streams")
