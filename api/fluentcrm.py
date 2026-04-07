import os
import requests


class FluentCRMClient:
    def __init__(self):
        self.base_url = os.getenv("FLUENTCRM_BASE_URL", "https://saveourclubs.nz/wp-json/fluent-crm/v2")
        self.username = os.getenv("FLUENTCRM_USERNAME", "")
        self.password = os.getenv("FLUENTCRM_PASSWORD", "")
        self.auth = (self.username, self.password)

    def _get(self, endpoint, params=None):
        url = f"{self.base_url}{endpoint}"
        try:
            resp = requests.get(url, auth=self.auth, params=params, timeout=15)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.HTTPError:
            return None
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            return None

    def is_available(self):
        result = self._get("/tags", {"per_page": 1})
        return result is not None

    def get_subscribers(self, per_page=15, page=1, search=None, tags=None,
                        lists=None, statuses=None, order_by="id", order_type="DESC"):
        params = {"per_page": per_page, "page": page, "order_by": order_by, "order_type": order_type}
        if search:
            params["search"] = search
        if tags:
            for i, t in enumerate(tags):
                params[f"tags[{i}]"] = t
        if lists:
            for i, l in enumerate(lists):
                params[f"lists[{i}]"] = l
        if statuses:
            for i, s in enumerate(statuses):
                params[f"statuses[{i}]"] = s
        raw = self._get("/subscribers", params)
        if raw and "subscribers" in raw:
            return raw["subscribers"]
        return raw

    def get_subscriber(self, subscriber_id):
        return self._get(f"/subscribers/{subscriber_id}")

    def get_campaigns(self, per_page=100, page=1, with_stats=True):
        params = {"per_page": per_page, "page": page}
        if with_stats:
            params["with[]"] = "stats"
        raw = self._get("/campaigns", params)
        if raw and "campaigns" in raw:
            return raw["campaigns"]
        return raw

    def get_campaign(self, campaign_id):
        return self._get(f"/campaigns/{campaign_id}")

    def get_campaign_emails(self, campaign_id, page=1, per_page=100):
        return self._get(f"/campaigns/{campaign_id}/emails", {"page": page, "per_page": per_page})

    def get_campaign_links(self, campaign_id):
        return self._get(f"/campaigns/{campaign_id}/links")

    def get_campaign_unsubscribes(self, campaign_id, page=1, per_page=100):
        return self._get(f"/campaigns/{campaign_id}/unsubscribes", {"page": page, "per_page": per_page})

    def get_tags(self):
        raw = self._get("/tags", {"per_page": 100})
        if raw and "tags" in raw:
            return raw["tags"]
        return raw

    def get_lists(self):
        raw = self._get("/lists", {"per_page": 100})
        # Lists endpoint returns a flat list under "lists" key
        if raw and "lists" in raw:
            lists_data = raw["lists"]
            if isinstance(lists_data, list):
                return {"data": lists_data, "total": len(lists_data)}
            return lists_data
        return raw

    def get_sequences(self, with_stats=True):
        params = {"per_page": 100}
        if with_stats:
            params["with[]"] = "stats"
        return self._get("/sequences", params)
