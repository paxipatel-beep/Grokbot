#!/usr/bin/env python3
"""Purge nil-balance customers from Zoho Books Cash (VLIGHTS, org 698806983).

For each contact, unlink credit-note applications and refunds, then delete
customer payments, credit notes, invoices, retainer invoices, sales orders,
and estimates. Up to three full passes handle dependency order. The contact
is deleted only after those passes.

Credentials are read from an env file. Nothing in this script is a secret.

Exit status is 0 when every selected contact is deleted (or already gone),
1 when the run finishes with one or more contacts still present, and 2 when
Zoho's org call cap (code 45) or --max-calls stops the run early.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path

DEFAULT_ORG_ID = "698806983"
DEFAULT_ACCOUNTS_URL = "https://accounts.zoho.com"
DEFAULT_BOOKS_BASE = "https://www.zohoapis.com/books/v3"
MAX_PASSES = 3
MAX_PAGES = 50
PER_PAGE = 200
REQUEST_PAUSE_SECONDS = 0.2
# One pause-and-retry when Zoho returns the org call cap, then the run stops.
CALL_CAP_BACKOFF_SECONDS = 15
REQUIRED_ENV = ("ZOHO_CLIENT_ID", "ZOHO_CLIENT_SECRET", "ZOHO_REFRESH_TOKEN")

# Copied onto the JSONString invoice update. A salesperson_id-only PUT is
# rejected on older paid invoices, so the line has to go back with the id.
LINE_ITEM_PUT_KEYS = (
    "line_item_id",
    "item_id",
    "name",
    "description",
    "rate",
    "quantity",
    "tax_id",
    "tax_name",
    "discount",
    "unit",
    "item_order",
    "hsn_or_sac",
    "account_id",
)

# Delete order after credit applications and refunds are removed.
# Retainer invoices sit with invoices because quotes cannot be deleted while
# a retainer invoice or a regular invoice still exists (Zoho code 9208).
DOC_STEPS = (
    ("customerpayments", "/customerpayments", "customerpayments", "payment_id", "payment_number", False),
    ("creditnotes", "/creditnotes", "creditnotes", "creditnote_id", "creditnote_number", False),
    ("invoices", "/invoices", "invoices", "invoice_id", "invoice_number", False),
    ("retainerinvoices", "/retainerinvoices", "retainerinvoices", "retainerinvoice_id", "retainerinvoice_number", True),
    ("salesorders", "/salesorders", "salesorders", "salesorder_id", "salesorder_number", False),
    ("estimates", "/estimates", "estimates", "estimate_id", "estimate_number", False),
)


def load_env(path: Path) -> dict[str, str]:
    if not path.is_file():
        raise SystemExit(f"env file not found: {path}")
    env: dict[str, str] = {}
    for lineno, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :].strip()
        if "=" not in line:
            raise SystemExit(f"env file {path}:{lineno} is not KEY=VALUE")
        key, value = line.split("=", 1)
        env[key.strip()] = value.strip().strip('"').strip("'")
    missing = [key for key in REQUIRED_ENV if not env.get(key)]
    if missing:
        raise SystemExit("env file is missing " + ", ".join(missing))
    return env


def contact_sort_key(contact: dict) -> tuple:
    number = str(contact.get("contact_number") or "").strip()
    match = re.fullmatch(r"CUS-(\d+)", number, flags=re.IGNORECASE)
    if match:
        return (0, int(match.group(1)), number.lower())
    digits = re.search(r"(\d+)", number)
    if digits:
        return (1, int(digits.group(1)), number.lower())
    return (2, 0, number.lower())


def load_contacts(path: Path) -> list[dict]:
    if not path.is_file():
        raise SystemExit(f"contacts file not found: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"contacts file is not valid JSON: {exc}") from exc
    if isinstance(data, dict):
        data = data.get("contacts")
    if not isinstance(data, list):
        raise SystemExit("contacts file must be a JSON array of contact objects")
    contacts = []
    for index, item in enumerate(data):
        if not isinstance(item, dict) or not item.get("contact_id"):
            raise SystemExit(f"contacts[{index}] needs a contact_id")
        contacts.append(item)
    contacts.sort(key=contact_sort_key)
    return contacts


def message_of(body: object) -> str:
    if isinstance(body, dict):
        message = body.get("message")
        if message is None:
            return ""
        return str(message)
    return str(body or "")


def code_of(body: object):
    if isinstance(body, dict):
        return body.get("code")
    return None


def is_missing(body: object) -> bool:
    message = message_of(body).lower()
    if "invalid url" in message:
        return False
    if code_of(body) == 1002:
        return True
    return any(
        snippet in message
        for snippet in (
            "does not exist",
            "doesn't exist",
            "do not exist",
            "not exist",
            "already deleted",
            "has been deleted",
        )
    )


def is_success(body: object, http: int | None) -> bool:
    if is_missing(body):
        return True
    code = code_of(body)
    if code in (0, "0"):
        return True
    return http is not None and 200 <= http < 300 and code is None


def is_unsupported(body: object, http: int | None) -> bool:
    message = message_of(body).lower()
    if "invalid url" in message or "not supported" in message or "module is not" in message:
        return True
    return http == 404 and "does not exist" not in message


def is_credits_blocked(body: object) -> bool:
    message = message_of(body).lower()
    code = code_of(body)
    if code in (1040, 12008):
        return True
    if "credits applied" in message or "refunded cannot be deleted" in message:
        return True
    return "refund" in message and "cannot be deleted" in message


def is_salesperson_blocked(body: object) -> bool:
    message = message_of(body).lower()
    return code_of(body) == 120104 or "salesperson cannot be empty" in message


def is_invoice_linked(body: object) -> bool:
    message = message_of(body).lower()
    if code_of(body) == 9208:
        return True
    return "invoices have been created" in message or "retainer invoice" in message or (
        "invoice" in message and "cannot be deleted" in message
    )


def is_payment_blocked(body: object) -> bool:
    message = message_of(body).lower()
    if "credit" in message:
        return False
    return "payment" in message and "cannot be deleted" in message


def is_already_void(body: object) -> bool:
    message = message_of(body).lower()
    return "already" in message and "void" in message


def is_org_call_cap(body: object) -> bool:
    """Zoho code 45: org maximum call rate (the 2,000 cap), not a short 429."""
    if code_of(body) in (45, "45"):
        return True
    message = message_of(body).lower()
    return "maximum call rate" in message or "call rate limit" in message


def is_json_encoding_error(body: object) -> bool:
    message = message_of(body).lower()
    return "jsonstring" in message or "invalid json" in message or "content-type" in message or "content type" in message


class ZohoCallBudgetStop(Exception):
    """Stop the whole purge. Further Books calls would keep failing or burn the cap."""

    def __init__(self, reason: str, body: dict | None = None, http: int | None = None):
        super().__init__(reason)
        self.reason = reason
        self.body = body or {}
        self.http = http


def invoice_salesperson_payload(invoice: dict, salesperson_id: str) -> dict | None:
    """Full invoice body for PUT. salesperson_id alone is not enough on paid invoices."""
    line_items = []
    for line in invoice.get("line_items") or []:
        if not isinstance(line, dict):
            continue
        item = {key: line.get(key) for key in LINE_ITEM_PUT_KEYS if line.get(key) not in (None, "")}
        if item:
            line_items.append(item)
    if not invoice.get("customer_id") or not line_items:
        return None
    payload: dict = {
        "customer_id": invoice.get("customer_id"),
        "salesperson_id": salesperson_id,
        "line_items": line_items,
    }
    for key in ("date", "due_date", "discount", "discount_type", "is_discount_before_tax", "reference_number"):
        if invoice.get(key) not in (None, ""):
            payload[key] = invoice.get(key)
    return payload


def load_deleted_contacts(path: Path) -> list[dict]:
    """Contacts a previous results file already marked deleted."""
    if not path.is_file():
        raise SystemExit(f"skip file not found: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"skip file is not valid JSON: {exc}") from exc
    rows = data.get("results") if isinstance(data, dict) else data
    if not isinstance(rows, list):
        raise SystemExit("skip file must be a purge results object or a list of contact results")
    deleted = []
    for row in rows:
        if isinstance(row, dict) and row.get("contact_deleted") and (row.get("contact_id") or row.get("contact_number")):
            deleted.append(row)
    return deleted


def prior_skip_entry(row: dict) -> dict:
    return {
        "contact_number": row.get("contact_number"),
        "contact_name": row.get("contact_name"),
        "contact_id": None if row.get("contact_id") is None else str(row.get("contact_id")),
        "passes_run": row.get("passes_run") or 0,
        "docs": [],
        "unresolved": [],
        "contact_deleted": True,
        "contact_code": row.get("contact_code"),
        "contact_message": row.get("contact_message") or "skipped; deleted in a previous run",
        "contact_http": row.get("contact_http"),
        "skipped_prior": True,
    }


def contact_is_prior_deleted(contact: dict, deleted_ids: set[str], deleted_numbers: set[str]) -> bool:
    contact_id = str(contact.get("contact_id") or "")
    number = str(contact.get("contact_number") or "").strip().upper()
    return (contact_id and contact_id in deleted_ids) or (number and number in deleted_numbers)


def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def atomic_write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(path)


def unresolved_deletes(docs: list[dict]) -> list[dict]:
    latest: dict[tuple, dict] = {}
    for doc in docs:
        if doc.get("action") != "delete":
            continue
        latest[(doc.get("kind"), str(doc.get("id")))] = doc
    return [
        {
            "kind": doc.get("kind"),
            "id": doc.get("id"),
            "number": doc.get("number"),
            "code": doc.get("code"),
            "message": doc.get("message"),
        }
        for doc in latest.values()
        if not doc.get("ok")
    ]


def summarize(results: list[dict], requested: int) -> dict:
    deleted = sum(1 for entry in results if entry.get("contact_deleted"))
    doc_ok = 0
    doc_fail = 0
    reasons: Counter[str] = Counter()
    for entry in results:
        latest: dict[tuple, dict] = {}
        for doc in entry.get("docs") or []:
            if doc.get("action") != "delete":
                continue
            latest[(doc.get("kind"), str(doc.get("id")))] = doc
        for doc in latest.values():
            if doc.get("ok"):
                doc_ok += 1
            else:
                doc_fail += 1
                reasons[f"{doc.get('kind')}: {doc.get('message')}"] += 1
    return {
        "requested": requested,
        "completed": len(results),
        "deleted": deleted,
        "failed": len(results) - deleted,
        "doc_delete_ok": doc_ok,
        "doc_delete_fail": doc_fail,
        "top_delete_failures": [
            {"reason": reason, "count": count} for reason, count in reasons.most_common(15)
        ],
    }


def print_summary(payload: dict) -> None:
    summary = payload.get("summary") or {}
    stopped = bool(payload.get("stopped"))
    print("SUMMARY", flush=True)
    if stopped:
        print("  status: STOPPED", flush=True)
        print(f"  reason: {payload.get('stop_reason')}", flush=True)
        if payload.get("stop_code") not in (None, ""):
            print(f"  stop_code: {payload.get('stop_code')}", flush=True)
        print("  No further Zoho Books calls were made after this stop.", flush=True)
    else:
        print("  status: finished", flush=True)
    print(f"  calls_made: {payload.get('calls_made')}", flush=True)
    if payload.get("max_calls") is not None:
        print(f"  max_calls: {payload.get('max_calls')}", flush=True)
    print(f"  skipped_prior: {payload.get('skipped_prior') or 0}", flush=True)
    print(
        f"  requested={summary.get('requested')} deleted={summary.get('deleted')} "
        f"failed={summary.get('failed')}",
        flush=True,
    )
    print(f"  results: {payload.get('results_path')}", flush=True)
    if stopped:
        print("  Resume after the cap resets with --skip-deleted-from pointing at this results file.", flush=True)


class ZohoBooks:
    """Minimal Books v3 client. `call` is the only method that touches the network."""

    def __init__(self, env: dict[str, str], org_id: str):
        self.env = env
        self.org_id = org_id
        accounts = (env.get("ZOHO_ACCOUNTS_URL") or DEFAULT_ACCOUNTS_URL).rstrip("/")
        self.accounts_url = accounts
        self.base = (env.get("ZOHO_BOOKS_BASE") or DEFAULT_BOOKS_BASE).rstrip("/")
        pause = env.get("ZOHO_REQUEST_PAUSE_SECONDS")
        try:
            self.pause = float(pause) if pause else REQUEST_PAUSE_SECONDS
        except ValueError:
            self.pause = REQUEST_PAUSE_SECONDS
        self.access: str | None = None
        self.token_at = 0.0
        self._last_request = time.monotonic()
        self._salesperson_id: str | None = None
        self._salesperson_ready = False
        self.skip_prefixes: set[str] = set()
        self.calls_made = 0
        self.max_calls: int | None = None
        self.cap_backoff_seconds = CALL_CAP_BACKOFF_SECONDS

    def token_endpoint(self) -> str:
        if self.accounts_url.endswith("/oauth/v2/token"):
            return self.accounts_url
        return self.accounts_url + "/oauth/v2/token"

    def refresh(self) -> None:
        form = urllib.parse.urlencode(
            {
                "refresh_token": self.env["ZOHO_REFRESH_TOKEN"],
                "client_id": self.env["ZOHO_CLIENT_ID"],
                "client_secret": self.env["ZOHO_CLIENT_SECRET"],
                "grant_type": "refresh_token",
            }
        ).encode()
        req = urllib.request.Request(
            self.token_endpoint(),
            data=form,
            method="POST",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read().decode() or "{}")
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode("utf-8", errors="replace")[:300]
            raise SystemExit(f"token refresh failed: HTTP {exc.code} {raw}") from exc
        except urllib.error.URLError as exc:
            raise SystemExit(f"token refresh failed: {exc.reason}") from exc
        token = data.get("access_token") if isinstance(data, dict) else None
        if not token:
            err = ""
            desc = ""
            if isinstance(data, dict):
                err = str(data.get("error") or "unknown_error")
                desc = str(data.get("error_description") or "")
            raise SystemExit(f"token refresh failed: {err} {desc}".strip())
        self.access = token
        self.token_at = time.monotonic()

    def refresh_if_stale(self, force: bool = False) -> None:
        age = time.monotonic() - self.token_at if self.token_at else 10**9
        if force or age > 30 * 60:
            self.refresh()
            print("token refreshed", flush=True)

    def _pace(self) -> None:
        elapsed = time.monotonic() - self._last_request
        if elapsed < self.pause:
            time.sleep(self.pause - elapsed)
        self._last_request = time.monotonic()

    @staticmethod
    def _parse(raw: str, status: int) -> dict:
        if not raw:
            if 200 <= status < 300:
                return {"code": 0, "message": "success"}
            return {"code": status, "message": ""}
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return {"code": status, "message": raw[:500]}
        if isinstance(data, dict):
            return data
        return {"code": status, "message": raw[:500]}

    def _once(self, method: str, path: str, query: dict | None, json_body, form_body):
        params = {"organization_id": self.org_id}
        if query:
            for key, value in query.items():
                if value is not None:
                    params[key] = value
        url = f"{self.base}{path}?{urllib.parse.urlencode(params)}"
        headers = {"Authorization": f"Zoho-oauthtoken {self.access}"}
        data = None
        if json_body is not None:
            data = json.dumps(json_body).encode()
            headers["Content-Type"] = "application/json"
        elif form_body is not None:
            data = urllib.parse.urlencode({"JSONString": json.dumps(form_body)}).encode()
            headers["Content-Type"] = "application/x-www-form-urlencoded"
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=90) as resp:
                raw = resp.read().decode() or ""
                return self._parse(raw, resp.status), resp.status, None
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode("utf-8", errors="replace")
            body = self._parse(raw, exc.code)
            retry_after = exc.headers.get("Retry-After") if exc.headers else None
            return body, exc.code, retry_after
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            reason = getattr(exc, "reason", exc)
            return {"code": None, "message": f"{type(exc).__name__}: {reason}"}, None, None

    def _stop_if_over_budget(self) -> None:
        if self.max_calls is not None and self.calls_made >= self.max_calls:
            raise ZohoCallBudgetStop(
                f"local --max-calls {self.max_calls} reached ({self.calls_made} Zoho Books calls)",
                {"code": None, "message": f"--max-calls {self.max_calls} reached"},
                None,
            )

    def call(self, method: str, path: str, query: dict | None = None, json_body=None, form_body=None):
        auth_retries = 0
        transient_retries = 0
        cap_retries = 0
        while True:
            self._stop_if_over_budget()
            self._pace()
            body, http, retry_after = self._once(method, path, query, json_body, form_body)
            self.calls_made += 1
            # Code 45 is the org cap ("maximum call rate limit of 2,000").
            # Pause once and retry that single call. If it is still the cap, stop
            # the process instead of walking the rest of the contact list.
            if is_org_call_cap(body):
                can_retry = cap_retries < 1 and (self.max_calls is None or self.calls_made < self.max_calls)
                if can_retry:
                    cap_retries += 1
                    wait = self.cap_backoff_seconds
                    if retry_after:
                        try:
                            wait = max(wait, float(retry_after))
                        except ValueError:
                            pass
                    detail = message_of(body).rstrip(".")
                    print(
                        f"Zoho code 45 call cap on {method} {path}: {detail}. "
                        f"Backing off {wait:.0f}s for one retry.",
                        flush=True,
                    )
                    time.sleep(wait)
                    continue
                raise ZohoCallBudgetStop(
                    f"Zoho code 45: {message_of(body) or 'maximum call rate limit'}",
                    body if isinstance(body, dict) else {"message": message_of(body)},
                    http,
                )
            message = message_of(body).lower()
            transient = http in (429, 500, 502, 503, 504) or "too many requests" in message
            if http == 401 and auth_retries < 1:
                auth_retries += 1
                print("access token rejected, refreshing", flush=True)
                self.refresh()
                continue
            if (transient or http is None) and transient_retries < 5:
                transient_retries += 1
                wait = min(60, 2 ** transient_retries)
                if retry_after:
                    try:
                        wait = max(wait, float(retry_after))
                    except ValueError:
                        pass
                print(f"transient {http} on {method} {path}, sleeping {wait:.0f}s", flush=True)
                time.sleep(wait)
                continue
            return body, http

    @staticmethod
    def _pagination_rejected(body: object) -> bool:
        if code_of(body) in (0, "0"):
            return False
        message = message_of(body).lower()
        return "per_page" in message or "extra parameter" in message

    def list_collection(
        self,
        path: str,
        list_key,
        customer_id: str | None = None,
        optional: bool = False,
        extra_query: dict | None = None,
        _stripped: bool = False,
    ):
        keys = (list_key,) if isinstance(list_key, str) else tuple(list_key)
        if path in self.skip_prefixes:
            return [], "skipped", {"code": 0, "message": "skipped"}, None
        items: list[dict] = []
        seen: set[str] = set()
        page = 1
        while page <= MAX_PAGES:
            query: dict = {"per_page": PER_PAGE, "page": page}
            if customer_id:
                query["customer_id"] = customer_id
            if extra_query:
                query.update(extra_query)
            body, http = self.call("GET", path, query=query)
            single_page = False
            if page == 1 and self._pagination_rejected(body):
                bare: dict = {}
                if customer_id:
                    bare["customer_id"] = customer_id
                if extra_query:
                    bare.update(extra_query)
                body, http = self.call("GET", path, query=bare or None)
                single_page = True
            if (
                page == 1
                and extra_query
                and not _stripped
                and not (isinstance(body, dict) and code_of(body) in (0, "0"))
            ):
                message = message_of(body).lower()
                if "filter" in message or "extra parameter" in message:
                    return self.list_collection(
                        path, list_key, customer_id, optional, extra_query=None, _stripped=True
                    )
            if optional and is_unsupported(body, http):
                self.skip_prefixes.add(path)
                return items, "unsupported", body, http
            if not (isinstance(body, dict) and code_of(body) in (0, "0")):
                return items, "error", body, http
            batch: list[dict] = []
            containers = [body]
            for wrap in ("creditnote", "invoice"):
                inner = body.get(wrap)
                if isinstance(inner, dict):
                    containers.append(inner)
            for container in containers:
                for key in keys:
                    value = container.get(key) or []
                    if isinstance(value, list):
                        batch.extend(row for row in value if isinstance(row, dict))
            for row in batch:
                marker = json.dumps(row, sort_keys=True, default=str)
                if marker not in seen:
                    seen.add(marker)
                    items.append(row)
            ctx = body.get("page_context") or {}
            has_more = ctx.get("has_more_page")
            if single_page or has_more is False or not batch:
                break
            if has_more is None and len(batch) < PER_PAGE:
                break
            page += 1
        return items, "ok", {"code": 0, "message": "success"}, 200

    def salesperson_id(self) -> str | None:
        if self._salesperson_ready:
            return self._salesperson_id
        body, _http = self.call("GET", "/salespersons")
        if not (isinstance(body, dict) and code_of(body) in (0, "0")):
            return None
        rows: list[dict] = []
        for key in ("data", "salespersons"):
            value = body.get(key)
            if isinstance(value, list):
                rows = [row for row in value if isinstance(row, dict) and row.get("salesperson_id")]
                break
        self._salesperson_ready = True
        active = [
            row
            for row in rows
            if row.get("is_active") is True or str(row.get("status") or "").lower() == "active"
        ]
        chosen = active or [row for row in rows if row.get("is_active") is not False]
        if not chosen:
            chosen = rows
        self._salesperson_id = str(chosen[0]["salesperson_id"]) if chosen else None
        return self._salesperson_id


def record(entry: dict, *, pass_i: int, action: str, kind: str, doc_id, number, body, http, related_id=None):
    ok = is_success(body, http)
    entry["docs"].append(
        {
            "pass": pass_i,
            "action": action,
            "kind": kind,
            "id": None if doc_id is None else str(doc_id),
            "number": None if number is None else str(number),
            "related_id": None if related_id is None else str(related_id),
            "ok": ok,
            "code": code_of(body),
            "message": message_of(body),
            "http": http,
        }
    )
    return ok


def _rows(body: object, *keys: str) -> list[dict]:
    found: list[dict] = []
    if not isinstance(body, dict):
        return found
    containers = [body]
    for wrap in ("creditnote", "invoice"):
        inner = body.get(wrap)
        if isinstance(inner, dict):
            containers.append(inner)
    for container in containers:
        for key in keys:
            value = container.get(key)
            if isinstance(value, list):
                found.extend(row for row in value if isinstance(row, dict))
            elif isinstance(value, dict):
                found.extend(_rows(value, *keys))
    return found


def application_id(row: dict) -> str | None:
    for key in ("creditnote_invoice_id", "creditnotes_invoice_id", "creditnote_invoiceid"):
        if row.get(key):
            return str(row[key])
    return None


def unapply_creditnote(client: ZohoBooks, entry: dict, pass_i: int, creditnote_id: str, number: str) -> None:
    apps, status, body, http = client.list_collection(
        f"/creditnotes/{creditnote_id}/invoices",
        ("invoices_credited", "invoices"),
    )
    if status == "error":
        record(
            entry,
            pass_i=pass_i,
            action="list",
            kind="creditnote_invoices",
            doc_id=creditnote_id,
            number=number,
            body=body,
            http=http,
        )
        detail, detail_http = client.call("GET", f"/creditnotes/{creditnote_id}")
        if isinstance(detail, dict) and code_of(detail) in (0, "0"):
            apps = _rows(detail, "invoices_credited", "invoices")
        else:
            record(
                entry,
                pass_i=pass_i,
                action="get",
                kind="creditnotes",
                doc_id=creditnote_id,
                number=number,
                body=detail,
                http=detail_http,
            )
    seen: set[str] = set()
    for row in apps:
        app_id = application_id(row)
        invoice_id = str(row["invoice_id"]) if row.get("invoice_id") else ""
        if not app_id or app_id in seen:
            continue
        seen.add(app_id)
        deleted, del_http = client.call("DELETE", f"/creditnotes/{creditnote_id}/invoices/{app_id}")
        ok = record(
            entry,
            pass_i=pass_i,
            action="unapply",
            kind="creditnotes",
            doc_id=creditnote_id,
            number=number,
            body=deleted,
            http=del_http,
            related_id=app_id,
        )
        if ok or not invoice_id:
            continue
        other, other_http = client.call("DELETE", f"/invoices/{invoice_id}/creditsapplied/{app_id}")
        record(
            entry,
            pass_i=pass_i,
            action="unapply",
            kind="invoices",
            doc_id=invoice_id,
            number=row.get("invoice_number") or invoice_id,
            body=other,
            http=other_http,
            related_id=app_id,
        )
    refunds, refund_status, refund_body, refund_http = client.list_collection(
        f"/creditnotes/{creditnote_id}/refunds",
        ("creditnote_refunds", "refunds"),
    )
    if refund_status == "error":
        record(
            entry,
            pass_i=pass_i,
            action="list",
            kind="creditnote_refunds",
            doc_id=creditnote_id,
            number=number,
            body=refund_body,
            http=refund_http,
        )
    for refund in refunds:
        refund_id = refund.get("creditnote_refund_id") or refund.get("refund_id")
        if not refund_id:
            continue
        deleted, del_http = client.call("DELETE", f"/creditnotes/{creditnote_id}/refunds/{refund_id}")
        record(
            entry,
            pass_i=pass_i,
            action="delete",
            kind="creditnote_refunds",
            doc_id=str(refund_id),
            number=number,
            body=deleted,
            http=del_http,
            related_id=creditnote_id,
        )


def unapply_invoice_credits(client: ZohoBooks, entry: dict, pass_i: int, invoice_id: str, number: str) -> None:
    rows, status, body, http = client.list_collection(
        f"/invoices/{invoice_id}/creditsapplied",
        ("credits", "credits_applied"),
    )
    if status == "error":
        record(
            entry,
            pass_i=pass_i,
            action="list",
            kind="invoice_credits",
            doc_id=invoice_id,
            number=number,
            body=body,
            http=http,
        )
        return
    for row in rows:
        app_id = application_id(row)
        if not app_id:
            continue
        deleted, del_http = client.call("DELETE", f"/invoices/{invoice_id}/creditsapplied/{app_id}")
        record(
            entry,
            pass_i=pass_i,
            action="unapply",
            kind="invoices",
            doc_id=invoice_id,
            number=number,
            body=deleted,
            http=del_http,
            related_id=app_id,
        )
        creditnote_id = row.get("creditnote_id")
        if creditnote_id:
            other, other_http = client.call(
                "DELETE", f"/creditnotes/{creditnote_id}/invoices/{app_id}"
            )
            record(
                entry,
                pass_i=pass_i,
                action="unapply",
                kind="creditnotes",
                doc_id=str(creditnote_id),
                number=row.get("creditnotes_number") or row.get("creditnote_number") or str(creditnote_id),
                body=other,
                http=other_http,
                related_id=app_id,
            )


def unlink_invoice_payments(client: ZohoBooks, entry: dict, pass_i: int, invoice_id: str, number: str) -> None:
    rows, status, body, http = client.list_collection(
        f"/invoices/{invoice_id}/payments",
        ("payments",),
    )
    if status == "error":
        record(
            entry,
            pass_i=pass_i,
            action="list",
            kind="invoice_payments",
            doc_id=invoice_id,
            number=number,
            body=body,
            http=http,
        )
        return
    for row in rows:
        payment_id = row.get("invoice_payment_id") or row.get("payment_id")
        if not payment_id:
            continue
        deleted, del_http = client.call("DELETE", f"/invoices/{invoice_id}/payments/{payment_id}")
        record(
            entry,
            pass_i=pass_i,
            action="delete",
            kind="invoice_payments",
            doc_id=str(payment_id),
            number=number,
            body=deleted,
            http=del_http,
            related_id=invoice_id,
        )


def assign_salesperson(client: ZohoBooks, entry: dict, pass_i: int, invoice_id: str, number: str) -> bool:
    """PUT the invoice back with line items and a salesperson, as JSONString.

    A body that is only salesperson_id fails on older paid invoices. If this
    full update fails, the caller voids the invoice and deletes it.
    """
    salesperson = client.salesperson_id()
    if not salesperson:
        record(
            entry,
            pass_i=pass_i,
            action="put_salesperson",
            kind="invoices",
            doc_id=invoice_id,
            number=number,
            body={"code": None, "message": "no salesperson available to assign"},
            http=None,
        )
        return False
    detail, detail_http = client.call("GET", f"/invoices/{invoice_id}")
    invoice = detail.get("invoice") if isinstance(detail, dict) else None
    payload = invoice_salesperson_payload(invoice, salesperson) if isinstance(invoice, dict) else None
    if not payload:
        record(
            entry,
            pass_i=pass_i,
            action="put_salesperson",
            kind="invoices",
            doc_id=invoice_id,
            number=number,
            body=detail if not isinstance(invoice, dict) else {"code": detail_http, "message": "invoice has no editable line items"},
            http=detail_http,
            related_id=salesperson,
        )
        return False
    body, http = client.call("PUT", f"/invoices/{invoice_id}", form_body=payload)
    ok = record(
        entry,
        pass_i=pass_i,
        action="put_salesperson",
        kind="invoices",
        doc_id=invoice_id,
        number=number,
        body=body,
        http=http,
        related_id=f"{salesperson}:jsonstring",
    )
    if ok or not is_json_encoding_error(body):
        return ok
    body, http = client.call("PUT", f"/invoices/{invoice_id}", json_body=payload)
    return record(
        entry,
        pass_i=pass_i,
        action="put_salesperson",
        kind="invoices",
        doc_id=invoice_id,
        number=number,
        body=body,
        http=http,
        related_id=f"{salesperson}:json",
    )


def void_then_delete(client: ZohoBooks, entry: dict, pass_i: int, kind: str, path: str, doc_id: str, number: str) -> bool:
    body, http = client.call("POST", f"{path}/{doc_id}/status/void")
    void_ok = record(
        entry,
        pass_i=pass_i,
        action="void",
        kind=kind,
        doc_id=doc_id,
        number=number,
        body=body,
        http=http,
    ) or is_already_void(body)
    if not void_ok and not is_success(body, http):
        # Still try the delete when Zoho reports the document is already void.
        if not is_already_void(body):
            return False
    deleted, del_http = client.call("DELETE", f"{path}/{doc_id}")
    return record(
        entry,
        pass_i=pass_i,
        action="delete",
        kind=kind,
        doc_id=doc_id,
        number=number,
        body=deleted,
        http=del_http,
    )


def delete_creditnote(client: ZohoBooks, entry: dict, pass_i: int, creditnote_id: str, number: str) -> bool:
    body, http = client.call("DELETE", f"/creditnotes/{creditnote_id}")
    ok = record(
        entry,
        pass_i=pass_i,
        action="delete",
        kind="creditnotes",
        doc_id=creditnote_id,
        number=number,
        body=body,
        http=http,
    )
    if ok or not is_credits_blocked(body):
        if ok:
            return True
        return void_then_delete(client, entry, pass_i, "creditnotes", "/creditnotes", creditnote_id, number)
    unapply_creditnote(client, entry, pass_i, creditnote_id, number)
    body, http = client.call("DELETE", f"/creditnotes/{creditnote_id}")
    ok = record(
        entry,
        pass_i=pass_i,
        action="delete",
        kind="creditnotes",
        doc_id=creditnote_id,
        number=number,
        body=body,
        http=http,
    )
    if ok or not is_credits_blocked(body):
        if ok:
            return True
        return void_then_delete(client, entry, pass_i, "creditnotes", "/creditnotes", creditnote_id, number)
    return void_then_delete(client, entry, pass_i, "creditnotes", "/creditnotes", creditnote_id, number)


def delete_invoice(client: ZohoBooks, entry: dict, pass_i: int, invoice_id: str, number: str) -> bool:
    unapply_invoice_credits(client, entry, pass_i, invoice_id, number)
    body, http = client.call("DELETE", f"/invoices/{invoice_id}")
    ok = record(
        entry,
        pass_i=pass_i,
        action="delete",
        kind="invoices",
        doc_id=invoice_id,
        number=number,
        body=body,
        http=http,
    )
    if ok:
        return True
    if is_credits_blocked(body):
        unapply_invoice_credits(client, entry, pass_i, invoice_id, number)
        body, http = client.call("DELETE", f"/invoices/{invoice_id}")
        ok = record(
            entry,
            pass_i=pass_i,
            action="delete",
            kind="invoices",
            doc_id=invoice_id,
            number=number,
            body=body,
            http=http,
        )
        if ok:
            return True
    if is_payment_blocked(body):
        unlink_invoice_payments(client, entry, pass_i, invoice_id, number)
        body, http = client.call("DELETE", f"/invoices/{invoice_id}")
        ok = record(
            entry,
            pass_i=pass_i,
            action="delete",
            kind="invoices",
            doc_id=invoice_id,
            number=number,
            body=body,
            http=http,
        )
        if ok:
            return True
    if is_salesperson_blocked(body):
        if assign_salesperson(client, entry, pass_i, invoice_id, number):
            body, http = client.call("DELETE", f"/invoices/{invoice_id}")
            ok = record(
                entry,
                pass_i=pass_i,
                action="delete",
                kind="invoices",
                doc_id=invoice_id,
                number=number,
                body=body,
                http=http,
            )
            if ok:
                return True
        return void_then_delete(client, entry, pass_i, "invoices", "/invoices", invoice_id, number)
    if is_credits_blocked(body) or is_payment_blocked(body):
        return void_then_delete(client, entry, pass_i, "invoices", "/invoices", invoice_id, number)
    return False


def _dedupe_docs(pairs: list[tuple[str, str]]) -> list[tuple[str, str]]:
    seen: set[str] = set()
    unique: list[tuple[str, str]] = []
    for doc_id, number in pairs:
        if not doc_id or doc_id in seen:
            continue
        seen.add(doc_id)
        unique.append((doc_id, number or doc_id))
    return unique


def links_from_estimate(estimate: dict) -> tuple[list[tuple[str, str]], list[tuple[str, str]]]:
    """Retainer invoices and invoices referenced by one estimate/quote."""
    retainers: list[tuple[str, str]] = []
    invoices: list[tuple[str, str]] = []
    if not isinstance(estimate, dict):
        return [], []
    for key in ("retainerinvoice_id", "retainer_invoice_id"):
        if estimate.get(key):
            retainers.append((str(estimate[key]), str(estimate.get("retainerinvoice_number") or estimate[key])))
    nested = estimate.get("retainerinvoice")
    if isinstance(nested, dict) and nested.get("retainerinvoice_id"):
        retainers.append(
            (str(nested["retainerinvoice_id"]), str(nested.get("retainerinvoice_number") or nested["retainerinvoice_id"]))
        )
    for key in ("retainerinvoices", "retainer_invoices"):
        for row in estimate.get(key) or []:
            if isinstance(row, dict) and row.get("retainerinvoice_id"):
                retainers.append(
                    (str(row["retainerinvoice_id"]), str(row.get("retainerinvoice_number") or row["retainerinvoice_id"]))
                )
    if estimate.get("invoice_id"):
        invoices.append((str(estimate["invoice_id"]), str(estimate.get("invoice_number") or estimate["invoice_id"])))
    for row in estimate.get("invoices") or []:
        if isinstance(row, dict) and row.get("invoice_id"):
            invoices.append((str(row["invoice_id"]), str(row.get("invoice_number") or row["invoice_id"])))
    return _dedupe_docs(retainers), _dedupe_docs(invoices)


def clear_estimate_blockers(
    client: ZohoBooks, entry: dict, pass_i: int, estimate_id: str, number: str, customer_id: str
) -> None:
    """Void/delete retainers and invoices that make Zoho refuse the quote (code 9208)."""
    detail, detail_http = client.call("GET", f"/estimates/{estimate_id}")
    estimate = detail.get("estimate") if isinstance(detail, dict) else None
    if not isinstance(estimate, dict):
        missing = (
            {"code": None, "message": "estimate payload did not include linked retainers or invoices"}
            if isinstance(detail, dict) and code_of(detail) in (0, "0")
            else detail
        )
        record(
            entry,
            pass_i=pass_i,
            action="get",
            kind="estimates",
            doc_id=estimate_id,
            number=number,
            body=missing,
            http=detail_http,
        )
        retainers: list[tuple[str, str]] = []
        invoices: list[tuple[str, str]] = []
    else:
        retainers, invoices = links_from_estimate(estimate)
    listed, status, list_body, list_http = client.list_collection(
        "/retainerinvoices",
        "retainerinvoices",
        customer_id,
        optional=True,
        extra_query={"filter_by": "Status.All"},
    )
    if status == "error":
        record(
            entry,
            pass_i=pass_i,
            action="list",
            kind="retainerinvoices",
            doc_id=customer_id,
            number=entry.get("contact_number"),
            body=list_body,
            http=list_http,
        )
    for item in listed:
        retainer_id = str(item.get("retainerinvoice_id") or "")
        if retainer_id:
            retainers.append((retainer_id, str(item.get("retainerinvoice_number") or retainer_id)))
    retainers = _dedupe_docs(retainers)
    for invoice_id, invoice_number in invoices:
        delete_invoice(client, entry, pass_i, invoice_id, invoice_number)
    for retainer_id, retainer_number in retainers:
        delete_document(client, entry, pass_i, "retainerinvoices", "/retainerinvoices", retainer_id, retainer_number)


def delete_estimate(
    client: ZohoBooks, entry: dict, pass_i: int, estimate_id: str, number: str, customer_id: str
) -> bool:
    body, http = client.call("DELETE", f"/estimates/{estimate_id}")
    ok = record(
        entry,
        pass_i=pass_i,
        action="delete",
        kind="estimates",
        doc_id=estimate_id,
        number=number,
        body=body,
        http=http,
    )
    if ok or not is_invoice_linked(body):
        return ok
    clear_estimate_blockers(client, entry, pass_i, estimate_id, number, customer_id)
    body, http = client.call("DELETE", f"/estimates/{estimate_id}")
    return record(
        entry,
        pass_i=pass_i,
        action="delete",
        kind="estimates",
        doc_id=estimate_id,
        number=number,
        body=body,
        http=http,
    )


def delete_document(client: ZohoBooks, entry: dict, pass_i: int, kind: str, path: str, doc_id: str, number: str) -> bool:
    body, http = client.call("DELETE", f"{path}/{doc_id}")
    ok = record(
        entry,
        pass_i=pass_i,
        action="delete",
        kind=kind,
        doc_id=doc_id,
        number=number,
        body=body,
        http=http,
    )
    if ok:
        return True
    if kind == "estimates" and is_invoice_linked(body):
        return False
    if kind == "salesorders" and is_invoice_linked(body):
        return False
    if kind in ("salesorders", "retainerinvoices", "customerpayments"):
        if kind == "customerpayments":
            return False
        return void_then_delete(client, entry, pass_i, kind, path, doc_id, number)
    return False


def run_pass(client: ZohoBooks, entry: dict, pass_i: int, customer_id: str) -> dict:
    """One full unlink-then-delete cycle. Returns whether anything remained."""
    stats = {"listed": 0, "list_failed": False, "delete_failures": 0}
    creditnotes, cn_status, cn_body, cn_http = client.list_collection(
        "/creditnotes", "creditnotes", customer_id
    )
    if cn_status == "error":
        stats["list_failed"] = True
        record(
            entry,
            pass_i=pass_i,
            action="list",
            kind="creditnotes",
            doc_id=customer_id,
            number=entry.get("contact_number"),
            body=cn_body,
            http=cn_http,
        )
    elif cn_status == "unsupported":
        record(
            entry,
            pass_i=pass_i,
            action="list",
            kind="creditnotes",
            doc_id=customer_id,
            number=entry.get("contact_number"),
            body=cn_body,
            http=cn_http,
        )
    for creditnote in creditnotes:
        creditnote_id = str(creditnote.get("creditnote_id") or "")
        number = str(creditnote.get("creditnote_number") or creditnote_id)
        if creditnote_id:
            unapply_creditnote(client, entry, pass_i, creditnote_id, number)

    invoices, inv_status, inv_body, inv_http = client.list_collection("/invoices", "invoices", customer_id)
    if inv_status == "error":
        stats["list_failed"] = True
        record(
            entry,
            pass_i=pass_i,
            action="list",
            kind="invoices",
            doc_id=customer_id,
            number=entry.get("contact_number"),
            body=inv_body,
            http=inv_http,
        )
    for invoice in invoices:
        invoice_id = str(invoice.get("invoice_id") or "")
        number = str(invoice.get("invoice_number") or invoice_id)
        if invoice_id:
            unapply_invoice_credits(client, entry, pass_i, invoice_id, number)

    for kind, path, list_key, id_key, num_key, optional in DOC_STEPS:
        extra_query = {"filter_by": "Status.All"} if kind == "retainerinvoices" else None
        items, status, list_body, list_http = client.list_collection(
            path, list_key, customer_id, optional=optional, extra_query=extra_query
        )
        if status == "error":
            stats["list_failed"] = True
            record(
                entry,
                pass_i=pass_i,
                action="list",
                kind=kind,
                doc_id=customer_id,
                number=entry.get("contact_number"),
                body=list_body,
                http=list_http,
            )
        elif status == "unsupported":
            record(
                entry,
                pass_i=pass_i,
                action="list",
                kind=kind,
                doc_id=customer_id,
                number=entry.get("contact_number"),
                body=list_body,
                http=list_http,
            )
            continue
        elif status == "skipped":
            continue
        stats["listed"] += len(items)
        for item in items:
            doc_id = str(item.get(id_key) or "")
            number = str(item.get(num_key) or doc_id)
            if not doc_id:
                continue
            if kind == "creditnotes":
                deleted = delete_creditnote(client, entry, pass_i, doc_id, number)
            elif kind == "invoices":
                deleted = delete_invoice(client, entry, pass_i, doc_id, number)
            elif kind == "estimates":
                deleted = delete_estimate(client, entry, pass_i, doc_id, number, customer_id)
            else:
                deleted = delete_document(client, entry, pass_i, kind, path, doc_id, number)
            if not deleted:
                stats["delete_failures"] += 1
    return stats


def purge_contact(client: ZohoBooks, contact: dict, entry: dict | None = None) -> dict:
    customer_id = str(contact["contact_id"])
    if entry is None:
        entry = {}
    entry.update(
        {
            "contact_number": contact.get("contact_number"),
            "contact_name": contact.get("contact_name"),
            "contact_id": customer_id,
            "passes_run": 0,
            "docs": [],
            "unresolved": [],
            "contact_deleted": False,
            "contact_code": None,
            "contact_message": "",
            "contact_http": None,
        }
    )
    probe, probe_http = client.call("GET", f"/contacts/{customer_id}")
    if is_missing(probe):
        entry["contact_deleted"] = True
        entry["contact_code"] = code_of(probe)
        entry["contact_message"] = message_of(probe) or "contact already absent"
        entry["contact_http"] = probe_http
        record(
            entry,
            pass_i=0,
            action="get",
            kind="contacts",
            doc_id=customer_id,
            number=entry["contact_number"],
            body=probe,
            http=probe_http,
        )
        return entry
    if not (isinstance(probe, dict) and code_of(probe) in (0, "0")):
        record(
            entry,
            pass_i=0,
            action="get",
            kind="contacts",
            doc_id=customer_id,
            number=entry["contact_number"],
            body=probe,
            http=probe_http,
        )

    for pass_i in range(1, MAX_PASSES + 1):
        entry["passes_run"] = pass_i
        stats = run_pass(client, entry, pass_i, customer_id)
        print(
            f"  pass {pass_i} listed={stats['listed']} delete_failures={stats['delete_failures']}"
            f" list_failed={stats['list_failed']}",
            flush=True,
        )
        if stats["listed"] == 0 and not stats["list_failed"]:
            break

    body, http = client.call("DELETE", f"/contacts/{customer_id}")
    entry["contact_deleted"] = is_success(body, http)
    entry["contact_code"] = code_of(body)
    entry["contact_message"] = message_of(body)
    entry["contact_http"] = http
    entry["unresolved"] = unresolved_deletes(entry["docs"])
    return entry


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Delete linked Zoho Books documents, then delete nil-balance contacts."
    )
    parser.add_argument("--contacts", required=True, help="JSON array of contacts to purge")
    parser.add_argument(
        "--env",
        required=True,
        dest="env_path",
        help="Env file with ZOHO_CLIENT_ID, ZOHO_CLIENT_SECRET, ZOHO_REFRESH_TOKEN",
    )
    parser.add_argument("--out", required=True, help="Where to write the JSON results")
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="After skipping already-deleted contacts, process only the first N",
    )
    parser.add_argument(
        "--max-calls",
        type=int,
        default=None,
        help="Stop before the next Books call once this many calls have been made (exit 2)",
    )
    parser.add_argument(
        "--skip-deleted-from",
        default=None,
        help="Previous results JSON; skip contacts already marked contact_deleted",
    )
    args = parser.parse_args(argv)
    if args.limit is not None and args.limit < 1:
        parser.error("--limit must be a positive integer")
    if args.max_calls is not None and args.max_calls < 1:
        parser.error("--max-calls must be a positive integer")
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    env = load_env(Path(args.env_path))
    org_id = env.get("ZOHO_ORG_ID") or DEFAULT_ORG_ID
    contacts = load_contacts(Path(args.contacts))
    skipped_rows: list[dict] = []
    if args.skip_deleted_from:
        prior = load_deleted_contacts(Path(args.skip_deleted_from))
        deleted_ids = {str(row["contact_id"]) for row in prior if row.get("contact_id")}
        deleted_numbers = {str(row.get("contact_number") or "").strip().upper() for row in prior}
        deleted_numbers.discard("")
        kept = []
        for contact in contacts:
            if not contact_is_prior_deleted(contact, deleted_ids, deleted_numbers):
                kept.append(contact)
                continue
            match = next(
                (
                    row
                    for row in prior
                    if (contact.get("contact_id") and str(row.get("contact_id") or "") == str(contact.get("contact_id")))
                    or str(row.get("contact_number") or "").strip().upper() == str(contact.get("contact_number") or "").strip().upper()
                ),
                contact,
            )
            skipped_rows.append(prior_skip_entry(match))
        contacts = kept
        skipped_list = ", ".join(str(row.get("contact_number") or row.get("contact_id")) for row in skipped_rows)
        print(f"skip prior deleted={len(skipped_rows)}: {skipped_list}", flush=True)
    if args.limit is not None:
        contacts = contacts[: args.limit]
    out = Path(args.out)
    payload = {
        "org_id": org_id,
        "started_at": now_iso(),
        "updated_at": None,
        "finished_at": None,
        "results_path": str(out),
        "contacts_requested": len(contacts),
        "skipped_prior": len(skipped_rows),
        "max_calls": args.max_calls,
        "calls_made": 0,
        "stopped": False,
        "stop_reason": None,
        "stop_code": None,
        "results": list(skipped_rows),
        "summary": summarize([], len(contacts)),
    }

    def save() -> None:
        attempted = [row for row in payload["results"] if not row.get("skipped_prior")]
        payload["updated_at"] = now_iso()
        payload["calls_made"] = client.calls_made
        summary = summarize(attempted, payload["contacts_requested"])
        summary["skipped_prior"] = payload["skipped_prior"]
        summary["calls_made"] = client.calls_made
        summary["stopped"] = payload["stopped"]
        summary["stop_reason"] = payload["stop_reason"]
        payload["summary"] = summary
        atomic_write(out, payload)

    client = ZohoBooks(env, org_id)
    client.max_calls = args.max_calls
    client.refresh()
    print(
        f"token ok org={org_id} contacts={len(contacts)} skipped_prior={len(skipped_rows)} "
        f"max_calls={args.max_calls} out={out}",
        flush=True,
    )
    stop: ZohoCallBudgetStop | None = None
    try:
        for index, contact in enumerate(contacts, 1):
            if index == 1 or index % 15 == 0:
                client.refresh_if_stale(force=(index % 15 == 0 and index != 1))
            number = contact.get("contact_number")
            name = contact.get("contact_name")
            print(f"[{index}/{len(contacts)}] {number} {name}", flush=True)
            entry = {
                "contact_number": number,
                "contact_name": name,
                "contact_id": str(contact.get("contact_id")),
                "passes_run": 0,
                "docs": [],
                "unresolved": [],
                "contact_deleted": False,
                "contact_code": None,
                "contact_message": "",
                "contact_http": None,
            }
            payload["results"].append(entry)
            try:
                purge_contact(client, contact, entry)
            except ZohoCallBudgetStop as exc:
                stop = exc
                payload["stopped"] = True
                payload["stop_reason"] = exc.reason
                payload["stop_code"] = code_of(exc.body)
                entry["stopped"] = True
                entry["contact_code"] = code_of(exc.body)
                entry["contact_message"] = exc.reason
                entry["contact_http"] = exc.http
                entry["unresolved"] = unresolved_deletes(entry.get("docs") or [])
                entry["docs"].append(
                    {
                        "pass": entry.get("passes_run") or 0,
                        "action": "stop",
                        "kind": "zoho",
                        "id": entry.get("contact_id"),
                        "number": entry.get("contact_number"),
                        "related_id": None,
                        "ok": False,
                        "code": code_of(exc.body),
                        "message": exc.reason,
                        "http": exc.http,
                    }
                )
                break
            finally:
                save()
            if stop:
                break
            latest: dict[tuple, dict] = {}
            for doc in entry["docs"]:
                if doc.get("action") == "delete":
                    latest[(doc.get("kind"), str(doc.get("id")))] = doc
            docs_ok = sum(1 for doc in latest.values() if doc.get("ok"))
            docs_fail = sum(1 for doc in latest.values() if not doc.get("ok"))
            print(
                f"[{index}/{len(contacts)}] {number} contact_ok={entry['contact_deleted']} "
                f"docs_ok={docs_ok} docs_fail={docs_fail} calls={client.calls_made} "
                f"msg={entry['contact_message']}",
                flush=True,
            )
    finally:
        payload["finished_at"] = now_iso()
        save()

    print_summary(payload)
    if stop:
        return 2
    failed = [entry for entry in payload["results"] if not entry.get("contact_deleted") and not entry.get("skipped_prior")]
    if failed:
        print("STILL BLOCKED:", flush=True)
        for entry in failed:
            bits = []
            for item in (entry.get("unresolved") or [])[:4]:
                bits.append(f"{item.get('kind')} {item.get('number')}: {item.get('message')}")
            extra = " | ".join(bits)
            print(
                f"  {entry.get('contact_number')} | {entry.get('contact_name')} | "
                f"{entry.get('contact_message')} | {extra}",
                flush=True,
            )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
