# OpenAPI operations

The checked-in `spec/openapi.yaml` is the operation catalog. Discover the live
CLI contract instead of relying on a memorized operation count or endpoint.

## Discover

```text
first-step api list [--tag TAG]
first-step api describe OPERATION_ID
```

`list` returns operation IDs, methods, paths, tags, and authentication modes.
Use `--tag` to narrow a domain. `describe` returns the selected operation's
parameters, request-body requirement/content types, response content types, and
authentication mode.

If a request body is required, inspect that operation and its referenced schema
in the same repository's `spec/openapi.yaml`. Do not guess fields from names or
reuse a body from a different operation.

## Call

```text
first-step api call OPERATION_ID \
  [--path NAME=VALUE ...] [--query NAME=VALUE ...] \
  [--header NAME=VALUE ...] [--header-env NAME=ENV_VAR ...] \
  [--body-file FILE] [--output FILE] [--origin URL]
```

- Repeat `--query` for repeated query values.
- Put JSON request bodies in `--body-file`; the CLI validates JSON before the
  request.
- Let the CLI generate a required `Idempotency-Key` unless a workflow requires
  an existing key.
- Pass `X-Upload-Token` only through `--header-env`; direct arguments fail
  closed.
- Use `--output` for CSV and binary responses. It creates a new owner-only file
  and never overwrites an existing path.
- Use `--output` only when an exact JSON response containing an opaque value is
  required by the next protocol step. Standard JSON stdout recursively redacts
  token, secret, and ticket fields.
- HEAD and 204 responses return bounded status/metadata JSON.

## Authentication modes

- `oauth`: require `auth status` and current user permission/RBAC.
- `none`: callable without OAuth, while normal response validation still
  applies.
- `session-only`: cataloged for completeness but intentionally rejected by
  `api call`; use the authenticated Web application when the user's task
  requires that operation.

The catalog covers every declared API operation, but catalog coverage does not
grant permission or weaken authorization, validation, optimistic concurrency,
idempotency, audit, preview/commit, or archive-only lifecycle rules.

## Mutation workflow

1. Describe the exact operation and inspect its schema.
2. Read the current resource and capture its version where applicable.
3. Prepare the smallest valid body with a meaningful change reason.
4. Run preview first when the contract provides preview/commit.
5. Confirm that the user's request authorizes the commit or external side
   effect.
6. Call the operation once and parse its JSON result.
7. Read back the affected resource or status.

Treat validation, permission, conflict, idempotency, and confirmation errors as
typed outcomes. Do not retry them blindly. On `CONFLICT_VERSION`, reload the
resource and reassess the user's intended change rather than substituting the
new version automatically.
