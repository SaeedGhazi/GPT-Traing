#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import hashlib
import json
import re
from pathlib import Path

SEPARATOR_START = "<<<FILE_START:"
SEPARATOR_END   = ">>>"
END_START       = "<<<FILE_END:"
END_END         = ">>>"

ANCHOR_RE = re.compile(r"\{#([A-Za-z0-9_.:-]+)\}")   # مانند {#id7-5.4.2} یا {#id12}
PAGE_RE   = re.compile(r"\[Page:\s*(\d+)\]")         # برای شمارش صفحات از متن

def sha1_of_text(text: str) -> str:
    h = hashlib.sha1()
    h.update(text.encode("utf-8", errors="ignore"))
    return h.hexdigest()

def count_pages(text: str) -> int:
    pages = PAGE_RE.findall(text)
    return max(map(int, pages)) if pages else 0

def normalize_anchors_to_base(text: str, base_id_number: int) -> str:
    """
    همه‌ی لنگرها را به فرم {#id<BASE>-<paragraph>} یکدست می‌کند.
    - اگر لنگر پاراگراف نداشت، به صورت {#id<BASE>-0} در می‌آید.
    - اگر داشت، فقط بخش عددی id را به BASE تغییر می‌دهیم و suffix را نگه می‌داریم.
    """
    def repl(m):
        raw = m.group(1)  # مثل 'id7-5.4.2' یا 'id12' یا حتی چیزهای دیگر
        # اگر الگوی id<number>-suffix را داشت:
        m2 = re.match(r"id(\d+)-(.*)$", raw)
        if m2:
            suffix = m2.group(2).strip()
            # اگر suffix خالی بود (غیرمحتمل اما ایمن):
            if not suffix:
                suffix = "0"
            return "{#id%d-%s}" % (base_id_number, suffix)
        # اگر الگوی فقط id<number> بود:
        m3 = re.match(r"id(\d+)$", raw)
        if m3:
            return "{#id%d-0}" % (base_id_number)
        # سایر شناسه‌ها را دست نمی‌زنیم تا خرابکاری نشود
        return "{#%s}" % raw

    return ANCHOR_RE.sub(repl, text)

def extract_first_anchor_suffix(text: str) -> str | None:
    """
    برای عنوان‌گذاری خوانا، تلاش می‌کند اولین لنگر را بگیرد و suffix پاراگرافش را برگرداند
    تا مثلا عنوان بشود: id23-3.4.2 اگر موجود بود.
    """
    for m in ANCHOR_RE.finditer(text):
        raw = m.group(1)
        m2 = re.match(r"id(\d+)-(.*)$", raw)
        if m2 and m2.group(2).strip():
            return m2.group(2).strip()
    return None

def iter_md_files(root: Path, pattern: str, recursive: bool, exclude_names: set[str]):
    files = sorted(root.rglob(pattern)) if recursive else sorted(root.glob(pattern))
    for p in files:
        if p.name in exclude_names:
            continue
        if p.is_file():
            yield p

def main():
    ap = argparse.ArgumentParser(description="Combine .md files with AI-friendly separators and normalized unique IDs.")
    ap.add_argument("path", nargs="?", default=".", help="پوشه‌ی ورودی (پیش‌فرض: پوشه‌ی جاری)")
    ap.add_argument("-o", "--output", default="combined_output_with_separators.md", help="نام فایل خروجی")
    ap.add_argument("--pattern", default="*.md", help="الگوی جستجو (پیش‌فرض: *.md)")
    ap.add_argument("-R", "--recursive", action="store_true", help="جستجوی بازگشتی در زیرپوشه‌ها")
    ap.add_argument("--id-start", type=int, default=1, help="شماره شروع id (مثلاً 101 برای دستهٔ دوم)")
    args = ap.parse_args()

    root = Path(args.path).resolve()
    out_path = (root / args.output) if not Path(args.output).is_absolute() else Path(args.output)
    exclude = {out_path.name}

    md_files = list(iter_md_files(root, args.pattern, args.recursive, exclude))
    if not md_files:
        print(f"هیچ فایل {args.pattern} در مسیر '{root}' پیدا نشد.")
        return

    lines = []
    lines.append("# Documents Combined\n")
    for idx, p in enumerate(md_files, 1):
        lines.append(f"- {idx}. {p.name}")
    lines.append("")

    current_id = args.id_start  # BASE برای اولین فایل

    for idx, p in enumerate(md_files, 1):
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            print(f"⚠️ خطا در خواندن {p}: {e}")
            continue

        # لنگرهای درون متن را به id<current_id>-<paragraph> یکدست می‌کنیم
        normalized_text = normalize_anchors_to_base(text, current_id)
        pages   = count_pages(normalized_text)
        sha1sum = sha1_of_text(normalized_text)

        # برای نمایش خوانا، اگر suffixِ اولین لنگر را یافتیم، آن را در عنوان می‌آوریم
        suffix  = extract_first_anchor_suffix(normalized_text)
        full_id_for_title = f"id{current_id}" + (f"-{suffix}" if suffix else "")

        header_obj = {
            "index": idx,
            "id": f"id{current_id}",
            "name": p.name,
            "pages": pages,
            "sha1": sha1sum,
            "path": str(p)
        }

        lines.append(f'{SEPARATOR_START}{json.dumps(header_obj, ensure_ascii=False)}{SEPARATOR_END}')
        lines.append(f"## {idx}. {full_id_for_title}: {p.name}\n")

        lines.append(normalized_text.rstrip())
        lines.append(f'{END_START}{json.dumps({"index": idx, "id": f"id{current_id}", "name": p.name}, ensure_ascii=False)}{END_END}')
        lines.append("")

        current_id += 1  # برای فایل بعدی

    out_path.write_text("\n".join(lines), encoding="utf-8")

    last_id = current_id - 1
    print(f"✅ انجام شد. خروجی: {out_path}")
    print(f"🔢 LAST_ID_NUMBER={last_id}")

if __name__ == "__main__":
    main()
