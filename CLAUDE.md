# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Python-based tool for converting Chinese song metadata from audio files into pinyin and visually similar Japanese kanji.

**Supported formats:** FLAC, MP3, AAC/M4A, WAV  
**Source audio:** album *跳舞的梵谷* (2017) by Stefanie Sun (孙燕姿), 24-bit/96kHz Hi-Res FLAC from mora.jp.

## Scripts & Tools

| File | Description |
|------|-------------|
| [convert_metadata.py](convert_metadata.py) | Main tool: reads audio metadata, converts to pinyin & Japanese kanji, outputs txt report |
| [dist/convert_metadata](dist/convert_metadata) | Standalone executable (macOS arm64, built with PyInstaller, includes embedded kanji mapping) |
| [kanji_map.csv](kanji_map.csv) | Embedded CJK mapping table (6,443 entries from 日漢转中汉.xlsx 全表 sheet) |
| [generate_html_ref.py](generate_html_ref.py) | Generates HTML reference document from the Excel mapping file |
| [USER_MANUAL.md](USER_MANUAL.md) | User manual (Markdown) |
| [usage.html](usage.html) | User manual (HTML version) |

## Build & Run

```bash
# Development — run via venv
source .venv/bin/activate
python3 convert_metadata.py --dir test_data
python3 convert_metadata.py --dir test_data --recursive
python3 convert_metadata.py --dir test_data --formats flac,mp3  # filter by format
python3 convert_metadata.py --dir test_data --output report.txt
python3 convert_metadata.py --gen-template my_map.csv     # export mapping template
python3 convert_metadata.py --dir test_data --mapping my_map.csv  # custom mapping

# Production — standalone executable
./dist/convert_metadata --dir test_data
./dist/convert_metadata --gen-template map_template.csv

# Build new executable (must include kanji_map.csv as data)
source .venv/bin/activate
pip install pyinstaller
pyinstaller --onefile --name convert_metadata --add-data "kanji_map.csv:." convert_metadata.py

# Regenerate HTML reference from Excel
source .venv/bin/activate
python3 generate_html_ref.py
```

## Dependencies

- `mutagen` — reading audio metadata (FLAC Vorbis Comment / MP3 ID3 / MP4 atom / WAV ID3)
- `pypinyin` — Chinese character to pinyin conversion
- `pyinstaller` — (build only) packaging into standalone executable

## Architecture

- **`find_audio_files(dir, recursive, exts)`** — scans directory using `os.listdir`/`os.walk` instead of `glob`, avoiding failures on paths with `[ ]` bracket characters common in Qobuz/mora release directories.
- **`read_metadata(filepath)`** — dispatches to per-format reader (FLAC/MP3/M4A/WAV) based on extension; extracts title, artist, album, albumartist, composer, tracknumber.
- **`to_pinyin(text)`** — segments text into Chinese/non-Chinese runs. Chinese chars → pinyin (no tone marks, first letter capitalized, space-separated). Non-Chinese text preserved as-is.
- **`load_kanji_mapping(csv_path)`** — loads Chinese→Japanese mapping from CSV (default: embedded `kanji_map.csv` with 6,443 entries). Format: `日文,中文` (header row required).
- **`to_japanese_kanji(text)`** — maps each CJK character via the loaded dict. Characters not in the mapping → `.`. Non-CJK text preserved as-is.
- **`generate_report(metadata, output_path)`** — writes formatted txt output.
- **`_resource_path(relative_path)`** — resolves data file path for both development (`os.path.dirname(__file__)`) and PyInstaller frozen mode (`sys._MEIPASS`).

## Data Files

- `kanji_map.csv` — CJK mapping table (6,443 entries, generated from `日漢转中汉.xlsx` 全表 sheet). Bundled into the executable via `--add-data` at build time.
- `日漢转中汉.xlsx` — Source Excel with `全表` sheet (two columns: 日文, 中文). Used by `generate_html_ref.py` and to regenerate `kanji_map.csv`.
- `test_data/` — 10 FLAC files (孙燕姿 - 跳舞的梵谷) for testing.
- mora FLACs may use Shift-JIS encoded tags; mutagen typically handles this transparently.
