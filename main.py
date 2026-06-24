from __future__ import annotations

import argparse
import sys
import webbrowser

from api_client import ApiSource
from config import API_ROOT, STORAGE_DIR
from parser import extract_meta, map_document
from renderer import render_all_declarations
from storage import Storage


def _get_or_fetch_document(
    doc_id: str,
    storage: Storage,
    api: ApiSource,
    force_reload: bool,
) -> dict | None:
    if not force_reload:
        cached = storage.find_document(doc_id)
        if cached:
            return cached

    try:
        doc = api.get_document(doc_id)
    except RuntimeError as e:
        if getattr(e, "http_code", None) == 404:
            print(f"Попередження: документ {doc_id} не знайдено в API — пропущено.", file=sys.stderr)
            return None
        print(f"Помилка: {e}", file=sys.stderr)
        sys.exit(1)

    storage.save_cache_document(doc_id, doc)
    meta = extract_meta(doc)
    if meta["user_declarant_id"]:
        storage.save_document(doc_id, meta["user_declarant_id"], map_document(doc))
    return doc


def main() -> None:
    arg_parser = argparse.ArgumentParser(
        description="Аналізатор декларацій НАЗК"
    )
    group = arg_parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "-u", type=int, metavar="USER_ID",
        help="Ідентифікатор декларанта (пріоритет)"
    )
    group.add_argument(
        "-d", metavar="DOC_ID",
        help="UUID декларації НАЗК"
    )
    arg_parser.add_argument(
        "-rd", action="store_true",
        help="Перезавантажити дані (ігноруючи кеш) і перегенерувати HTML"
    )
    arg_parser.add_argument(
        "-rv", action="store_true",
        help="Перегенерувати HTML"
    )
    args = arg_parser.parse_args()

    storage = Storage(STORAGE_DIR)
    api = ApiSource(API_ROOT)

    user_declarant_id: int | None = None

    if args.u is not None:
        user_declarant_id = args.u
    else:
        # step 2: fetch doc → extract user_declarant_id → go to step 1.1
        doc = _get_or_fetch_document(args.d, storage, api, force_reload=args.rd)
        meta = extract_meta(doc)
        user_declarant_id = meta["user_declarant_id"]
        if not user_declarant_id:
            print(
                "Помилка: не вдалося отримати user_declarant_id з документа.",
                file=sys.stderr,
            )
            sys.exit(1)

    if args.rd:
        args.rv = True
    
    # step 1.1: serve existing HTML if available and -rd & -rv not set
    if not args.rd and not args.rv:
        html_path = storage.find_html(user_declarant_id)
        if html_path:
            webbrowser.open(f"file:///{html_path}")
            return

    # step 1.2: get list of doc_ids
    # пріоритет: list-cache → API → storage-файли (fallback)
    doc_ids: list[str] | None = None if args.rd else storage.find_list_cache(user_declarant_id)
    if doc_ids is None:
        try:
            raw_list = api.fetch_list_raw(user_declarant_id)
        except RuntimeError as e:
            print(f"Помилка: {e}", file=sys.stderr)
            sys.exit(1)
        storage.save_cache_list(user_declarant_id, raw_list)
        doc_ids = [item["id"] for item in raw_list.get("data", [])]
    if not doc_ids:
        doc_ids = storage.find_doc_ids_in_storage(user_declarant_id)

    if not doc_ids:
        print("Помилка: список декларацій порожній.", file=sys.stderr)
        sys.exit(1)

    # step 1.3: fetch all documents
    docs: list[dict] = []
    for doc_id in doc_ids:
        doc = _get_or_fetch_document(doc_id, storage, api, force_reload=args.rd)
        if doc is not None:
            docs.append(doc)

    if not docs:
        print("Помилка: жодного документа не вдалося завантажити.", file=sys.stderr)
        sys.exit(1)

    # step 1.4: render combined HTML
    sorted_docs = sorted(docs, key=lambda d: d.get("declaration_year", 0), reverse=True)
    meta = extract_meta(sorted_docs[0])
    fullname = meta["fullname"]

    html = render_all_declarations(user_declarant_id, sorted_docs)
    html_path = storage.save_html(user_declarant_id, fullname, html)

    print(f"Збережено: {html_path}")
    webbrowser.open(f"file:///{html_path}")


if __name__ == "__main__":
    main()
