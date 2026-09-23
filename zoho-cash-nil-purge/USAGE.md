# Zoho Cash nil-customer purge

Deletes linked documents, then the contact, for nil-balance customers in Zoho Books Cash org **698806983** (VLIGHTS). The contact list is `remaining_54.json` (54 contacts, `CUS-60` through `CUS-460`).

This script only talks to Zoho when you run it locally. It does not contain credentials.

## Env file

Create a file that is **not** committed (for example `/home/box/agent-data/shared-secrets/zoho-vlights-cash.env`):

```bash
ZOHO_CLIENT_ID=your_client_id
ZOHO_CLIENT_SECRET=your_client_secret
ZOHO_REFRESH_TOKEN=your_refresh_token
```

Optional:

| Variable | Default |
|---|---|
| `ZOHO_ORG_ID` | `698806983` |
| `ZOHO_ACCOUNTS_URL` | `https://accounts.zoho.com` |
| `ZOHO_BOOKS_BASE` | `https://www.zohoapis.com/books/v3` |
| `ZOHO_REQUEST_PAUSE_SECONDS` | `0.2` |

`ZOHO_ACCOUNTS_URL` may be the accounts host or the full `.../oauth/v2/token` URL. Quotes and a leading `export ` are accepted. Lines starting with `#` are ignored.

## Run the remaining 54

From the repo root:

```bash
python3 zoho-cash-nil-purge/purge_remaining.py \
  --contacts zoho-cash-nil-purge/remaining_54.json \
  --env /home/box/agent-data/shared-secrets/zoho-vlights-cash.env \
  --out zoho-cash-nil-purge/purge_results.json
```

Try a short run first:

```bash
python3 zoho-cash-nil-purge/purge_remaining.py \
  --contacts zoho-cash-nil-purge/remaining_54.json \
  --env /home/box/agent-data/shared-secrets/zoho-vlights-cash.env \
  --out /tmp/purge_limit5.json \
  --limit 5
```

Contacts are processed in ascending `CUS-` number. `--limit` applies after `--skip-deleted-from`.

Exit status:

| Code | Meaning |
|---|---|
| `0` | Every selected contact was deleted, or was already gone |
| `1` | The run finished, and one or more contacts remain |
| `2` | Hard stop: Zoho code 45 (org call cap) or `--max-calls` |

A token or file error exits before the run. Progress is printed per contact. Results are rewritten after each contact.

## Resume after a partial run

CUS-60, CUS-107, and CUS-157 were deleted before the org cap. Point `--skip-deleted-from` at that results file (it must contain `"contact_deleted": true` for each finished contact). Those contacts are copied into the new results as already deleted and are not sent to Zoho. `--limit` then counts only the contacts still to do.

```bash
python3 zoho-cash-nil-purge/purge_remaining.py \
  --contacts zoho-cash-nil-purge/remaining_54.json \
  --env /home/box/agent-data/shared-secrets/zoho-vlights-cash.env \
  --out zoho-cash-nil-purge/purge_results.json \
  --skip-deleted-from /path/to/previous_purge_results.json \
  --max-calls 1500
```

`--max-calls` stops **before** the next Books call once that many calls have been made, so the run can stay under Zoho's 2,000 cap. The same path may be used for `--out` and `--skip-deleted-from`; the skip file is read into memory before it is rewritten.

## Call cap (Zoho code 45)

Zoho code 45, message like `maximum call rate limit of 2,000`, is the organization cap. The script pauses once (15 seconds, or `Retry-After` if longer), retries that single call, and if the cap is still in effect it **stops the process**. It does not walk the rest of the contacts. HTTP 429 and 5xx still use pause-and-backoff retries. Those are not code 45.

The results file and stdout both get a `SUMMARY` with `stopped`, `stop_reason`, `calls_made`, and how many contacts were deleted. Exit status is `2`. Resume later with `--skip-deleted-from` on that results file.

## What each contact does

Up to three passes. A pass stops early when a later pass finds nothing left.

1. List credit notes. Delete each invoice application (`DELETE /creditnotes/{id}/invoices/{creditnote_invoice_id}`). If that fails, delete the same application from the invoice (`DELETE /invoices/{id}/creditsapplied/{id}`). Delete credit-note refunds.
2. List invoices and delete any credits still applied.
3. Delete customer payments.
4. Delete credit notes. If Zoho still reports applied credits or refunds (code `1040`), unapply again and retry, then void and delete.
5. Delete invoices. If credits or payments are still attached, unapply and retry. If delete returns `Salesperson cannot be empty` (code `120104`), GET the invoice and `PUT` it back as `JSONString` with `salesperson_id` **and** its `line_items` (a salesperson id alone fails on older paid invoices). If that update fails, or the delete still fails, void the invoice and delete it. Credits that survive unapply are voided and then deleted (void detaches credits).
6. Delete retainer invoices (quotes can be blocked by these; a missing retainer module is skipped).
7. Delete sales orders. If an invoice still exists, leave the sales order for the next pass.
8. Delete estimates/quotes. Code `9208` (invoice or retainer still linked) waits for the next pass, after invoices are gone.

Then `DELETE /contacts/{contact_id}`.

The access token is refreshed at startup, every 15 contacts, when it is older than 30 minutes, and after an HTTP 401. HTTP 429 and 5xx responses are retried with pause backoff. Code 45 is not: after one backoff retry the run hard-stops.

## Results file

`purge_results.json` looks like:

```json
{
  "org_id": "698806983",
  "contacts_requested": 54,
  "summary": {"deleted": 0, "failed": 0},
  "results": [
    {
      "contact_number": "CUS-60",
      "contact_id": "2056712000000441001",
      "contact_deleted": false,
      "contact_message": "",
      "passes_run": 3,
      "docs": [
        {
          "pass": 1,
          "action": "unapply",
          "kind": "creditnotes",
          "id": "2056...",
          "number": "CN-02792",
          "ok": true,
          "code": 0,
          "message": "Credits applied to an invoice have been deleted."
        }
      ],
      "unresolved": []
    }
  ]
}
```

`docs` is every mutation attempt (unapply, refund delete, salesperson update, void, delete), including retries. `unresolved` is the latest failed delete per document. `summary.top_delete_failures` is the tally of those remaining failures.
