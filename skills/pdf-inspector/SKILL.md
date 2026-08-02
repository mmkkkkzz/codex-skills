---
name: pdf-inspector
description: Inspect PDF type, OCR requirements, layout complexity, tables, columns, and encoding issues, or convert locally extractable PDF text to Markdown with Firecrawl's pdf-inspector CLI. Use when Codex needs to classify a PDF as text-based, scanned, image-based, or mixed; decide whether OCR is needed; extract Markdown; select pages; preserve page markers; produce structured JSON or positioned text items; or inspect PDF layout without uploading the document to a remote service.
---

# PDF Inspector

Use Firecrawl's local `detect-pdf` and `pdf2md` commands. Preserve the source PDF and create derived files only when the user requests output artifacts.

## Check Availability

Verify both commands before working:

```bash
command -v detect-pdf
command -v pdf2md
```

If either is missing, load an existing Rust environment and install the released CLI:

```bash
if ! command -v cargo >/dev/null 2>&1 && [ -f "$HOME/.cargo/env" ]; then
  source "$HOME/.cargo/env"
fi
command -v cargo
cargo install pdf-inspector
```

If `cargo` is still unavailable, install Rust from `https://rustup.rs/`, load `$HOME/.cargo/env`, and retry. Do not use an unverified third-party binary.

Do not use `--help` or `--version` as availability checks; released versions may treat those flags as input filenames.

## Choose The Operation

- Classify a PDF and identify OCR pages: `detect-pdf "input.pdf" --json`
- Include table and column analysis: `detect-pdf "input.pdf" --analyze --json`
- Convert the whole document to Markdown: `pdf2md "input.pdf" "output.md"`
- Reduce token-heavy dot leaders and similar padding: add `--compact`
- Preserve page boundaries as `<!-- Page N -->`: add `--pages`
- Convert selected 1-indexed pages: add `--select-pages "1,3,5-10"`
- Emit result metadata and Markdown as JSON: `pdf2md "input.pdf" --json`
- Emit positioned text items with font and coordinate metadata: `pdf2md "input.pdf" --items-json`
- Print only Markdown to stdout for a pipeline: `pdf2md "input.pdf" --raw`

Put an output filename immediately after the input filename. Put flags after the output filename:

```bash
pdf2md "input.pdf" "output.md" --compact --pages --select-pages "1-5"
```

Use quoted paths. Prefer an explicit output file over shell redirection when the user wants a durable artifact.

## Workflow

1. Resolve the PDF path and confirm it exists.
2. Run `detect-pdf "input.pdf" --json` before extraction when OCR suitability is unknown.
3. Inspect `pdf_type`, `confidence`, `pages_needing_ocr`, and `ocr_reasons_by_page`. Add `--analyze` when tables, columns, or complex layout matter.
4. Run `pdf2md` only for locally extractable content. Use `--compact` by default when the output is primarily for an LLM; use `--pages` when page traceability matters.
5. Verify the command exit status and the output file. Check that expected text exists without dumping a large or sensitive document into the conversation.
6. Report the output path, selected pages or options, classification, OCR gaps, and any encoding or layout warnings.

## Interpretation And Limits

Treat `text_based` as directly extractable and `scanned` or `image_based` as requiring an OCR tool. Treat `mixed` as partial extraction: explicitly report `pages_needing_ocr` rather than implying the entire document was converted.

`pdf-inspector` does not perform OCR. If `ocr_recommended` is true, pages need OCR, or `has_encoding_issues` is true, preserve the partial result and explain the limitation. Do not silently replace missing text with guesses.

The CLI runs locally and does not require uploading the PDF. Do not send confidential PDFs to external services unless the user explicitly authorizes that separate action.

For encrypted PDFs, use `--password` only when the user supplies the password. Avoid echoing or logging it, and note that the CLI accepts it as a process argument.
