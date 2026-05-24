#!/usr/bin/env python3
"""
歌曲信息转换工具 v1.1 - Song Metadata Converter

功能:
  1. 将中文歌曲信息（歌名、专辑名、表演者等）转换成拼音，
     首字母大写，空格分隔每个字符。
  2. 将中文歌曲信息转换成字形相似的日语汉字。
  3. 生成包含原始信息与转换结果的 txt 文件。

支持格式: FLAC / MP3 / AAC (M4A) / WAV

用法:
  python3 convert_metadata.py --dir <音频目录> [--output <输出文件>] [--recursive]
"""

import argparse
import os
import re
import csv
import sys
from datetime import datetime

from pypinyin import pinyin, Style

# 中日汉字映射缓存 (中文 → 日文)，由 load_kanji_mapping() 初始化
_KANJI_MAP = None


def _resource_path(relative_path: str) -> str:
    """获取资源文件的绝对路径，支持开发环境和 PyInstaller 打包模式。"""
    if getattr(sys, 'frozen', False):
        base = sys._MEIPASS  # type: ignore[attr-defined]
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, relative_path)


# ── 支持的音频格式 ─────────────────────────────────────────────────

AUDIO_EXTENSIONS = {'.flac', '.mp3', '.m4a', '.mp4', '.wav'}

# 每种格式使用的 mutagen 读取器
FORMAT_READERS = {}

# 延迟导入，只在真正处理对应格式时加载

def _import_mutagen_for(ext: str):
    """按需导入对应格式的 mutagen 模块。"""
    if ext == '.flac':
        import mutagen.flac
        return mutagen.flac.FLAC
    elif ext == '.mp3':
        import mutagen.easyid3
        import mutagen.mp3
        return mutagen.easyid3.EasyID3
    elif ext in ('.m4a', '.mp4'):
        import mutagen.mp4
        return mutagen.mp4.MP4
    elif ext == '.wav':
        import mutagen.wave
        import mutagen.id3
        return mutagen.wave.WAVE
    return None


# ── 功能 1: 中文 → 拼音 ────────────────────────────────────────────

def to_pinyin(text: str) -> str:
    """将字符串中的汉字转为拼音（无声调），首字母大写，空格分隔；
    非汉字片段原样保留（连续字母数字保持为一个词）。"""
    segments = re.findall(r'[一-鿿]+|[^一-鿿]+', text)
    result_parts = []
    for seg in segments:
        if re.match(r'^[一-鿿]+$', seg):
            chars_py = []
            for ch in seg:
                py = pinyin(ch, style=Style.NORMAL)[0][0]
                chars_py.append(py.capitalize())
            result_parts.append(' '.join(chars_py))
        else:
            stripped = seg.strip()
            if stripped:
                result_parts.append(stripped)
    return ' '.join(result_parts)


# ── 功能 2: 简体中文 → 日语汉字 ──────────────────────────────────


def load_kanji_mapping(csv_path: str | None = None) -> dict[str, str]:
    """从 CSV 加载中日汉字映射字典 (中文 → 日文)。

    默认读取内嵌的 kanji_map.csv；可通过 csv_path 指定外部 CSV。
    CSV 格式：第一列 日文, 第二列 中文（带表头）。
    """
    if csv_path is None:
        csv_path = _resource_path("kanji_map.csv")

    mapping: dict[str, str] = {}
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader, None)  # 跳过表头
        for row in reader:
            if not row or len(row) < 2:
                continue
            jp, cn = row[0].strip(), row[1].strip()
            if not jp or not cn or len(jp) != 1 or len(cn) != 1:
                continue
            if ord(jp) < 0x4E00:
                continue
            mapping[cn] = jp  # Chinese → Japanese
    return mapping


def generate_mapping_template(output_path: str) -> None:
    """从内嵌的默认映射导出 CSV 模板。"""
    mapping = load_kanji_mapping()
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["日文", "中文"])
        for cn, jp in sorted(mapping.items(), key=lambda x: ord(x[0])):
            writer.writerow([jp, cn])
    print(f"映射表模板已生成: {output_path}")


def to_japanese_kanji(text: str) -> str:
    """将简体中文转为日语汉字，未找到对应关系的汉字用 '.' 替换。"""
    global _KANJI_MAP
    if _KANJI_MAP is None:
        try:
            _KANJI_MAP = load_kanji_mapping()
        except Exception as e:
            print(f"  ⚠ 无法加载汉字映射表 ({e})，未匹配汉字将替换为 '.'")
            _KANJI_MAP = {}

    result = []
    for c in text:
        if ord(c) >= 0x4E00:
            result.append(_KANJI_MAP.get(c, '.'))
        else:
            result.append(c)
    return ''.join(result)


# ── 查找音频文件 ──────────────────────────────────────────────────

def find_audio_files(directory: str, recursive: bool = False,
                     exts: set | None = None) -> list[str]:
    """查找目录下所有支持的音频文件。

    使用 os.listdir / os.walk 而非 glob，避免路径中含有
    [ ] 等 glob 特殊字符时匹配失败的问题。
    """
    if exts is None:
        exts = AUDIO_EXTENSIONS
    directory = os.path.abspath(directory)
    if not os.path.isdir(directory):
        print(f"错误: 目录不存在 '{directory}'")
        return []

    files = []
    if recursive:
        for root, _dirs, filenames in os.walk(directory):
            for fn in sorted(filenames):
                ext = os.path.splitext(fn)[1].lower()
                if ext in exts:
                    files.append(os.path.join(root, fn))
    else:
        try:
            entries = sorted(os.listdir(directory))
        except PermissionError:
            print(f"错误: 无权限读取目录 '{directory}'")
            return []
        for fn in entries:
            full = os.path.join(directory, fn)
            ext = os.path.splitext(fn)[1].lower()
            if os.path.isfile(full) and ext in exts:
                files.append(full)

    return files


# ── 读取元数据（多格式支持） ─────────────────────────────────────

FIELDS = ["title", "artist", "album", "albumartist", "composer"]
FIELD_CN = {
    "title": "歌曲名",
    "artist": "表演者",
    "album": "专辑",
    "albumartist": "专辑表演者",
    "composer": "作曲者",
}


def read_metadata(filepath: str) -> dict:
    """读取音频文件的元数据，支持 FLAC / MP3 / M4A / WAV。"""
    ext = os.path.splitext(filepath)[1].lower()
    meta = {f: "" for f in FIELDS}
    meta["tracknumber"] = ""
    meta["filename"] = os.path.basename(filepath)
    meta["format"] = ext.lstrip(".").upper()

    try:
        if ext == '.flac':
            _read_flac_meta(filepath, meta)
        elif ext == '.mp3':
            _read_mp3_meta(filepath, meta)
        elif ext in ('.m4a', '.mp4'):
            _read_mp4_meta(filepath, meta)
        elif ext == '.wav':
            _read_wav_meta(filepath, meta)
    except Exception as e:
        print(f"  ⚠ {meta['filename']}: 读取元数据失败 ({e})")

    return meta


def _read_flac_meta(path: str, meta: dict):
    import mutagen.flac
    tags = mutagen.flac.FLAC(path)
    for key in FIELDS:
        vals = tags.get(key)
        if vals:
            meta[key] = vals[0]
    trk = tags.get("tracknumber")
    if trk:
        meta["tracknumber"] = trk[0]


def _read_mp3_meta(path: str, meta: dict):
    import mutagen.easyid3
    try:
        tags = mutagen.easyid3.EasyID3(path)
    except mutagen.id3.ID3NoHeaderError:
        return  # 无 ID3 标签，字段保持默认空值
    for key in FIELDS:
        vals = tags.get(key)
        if vals:
            meta[key] = vals[0]
    trk = tags.get("tracknumber")
    if trk:
        meta["tracknumber"] = trk[0]


def _read_mp4_meta(path: str, meta: dict):
    import mutagen.mp4
    MP4_MAP = {
        "title": "\xa9nam",
        "artist": "\xa9ART",
        "album": "\xa9alb",
        "albumartist": "aART",
        "composer": "\xa9wrt",
    }
    tags = mutagen.mp4.MP4(path)
    for key, atom in MP4_MAP.items():
        vals = tags.tags.get(atom)
        if vals:
            meta[key] = str(vals[0])
    trk = tags.tags.get("trkn")
    if trk:
        meta["tracknumber"] = str(trk[0][0])


def _read_wav_meta(path: str, meta: dict):
    # WAV 通过 ID3 chunk 携带标签，用 EasyID3 方式读取
    import mutagen.id3
    try:
        tags = mutagen.id3.ID3(path)
    except mutagen.id3.ID3NoHeaderError:
        return
    # ID3v2 frame -> field 映射 (只读文本帧)
    WAV_FRAME_MAP = {
        "TIT2": "title",
        "TPE1": "artist",
        "TALB": "album",
        "TPE2": "albumartist",
        "TCOM": "composer",
        "TRCK": "tracknumber",
    }
    for frame_id, field in WAV_FRAME_MAP.items():
        frame = tags.get(frame_id)
        if frame:
            val = str(frame)
            if field == "tracknumber":
                meta[field] = val.split("/")[0]
            else:
                meta[field] = val


# ── 输出 TXT ───────────────────────────────────────────────────────

def generate_report(all_metadata: list[dict], output_path: str) -> None:
    """生成格式化的 txt 报告。"""
    lines = []
    lines.append("=" * 72)
    lines.append("  歌曲信息转换报告")
    lines.append("=" * 72)
    lines.append("")
    lines.append(f"  共处理 {len(all_metadata)} 首曲目")
    lines.append(f"  生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")

    for i, m in enumerate(all_metadata, 1):
        track = m.get("tracknumber") or str(i)
        fmt = m.get("format", "")
        lines.append(f"  {'─' * 68}")
        lines.append(f"  【曲目 {track}】{m['filename']}  ({fmt})")
        lines.append(f"  {'─' * 68}")
        lines.append("")

        for key in FIELDS:
            val = m.get(key, "")
            if not val:
                continue
            cn = FIELD_CN.get(key, key)
            lines.append(f"  ┌ {cn:　<6s}: {val}")
            lines.append(f"  ├ 拼音     : {to_pinyin(val)}")
            lines.append(f"  └ 日语汉字 : {to_japanese_kanji(val)}")
            lines.append("")

    lines.append("=" * 72)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print(f"报告已生成: {output_path}")


# ── 命令行入口 ────────────────────────────────────────────────────

VERSION = "1.1.0"


def main():
    parser = argparse.ArgumentParser(
        description="歌曲信息转换工具 — 中文 → 拼音 / 日语汉字")
    parser.add_argument("--dir", default=".",
                        help="音频文件所在目录（默认当前目录）")
    parser.add_argument("--output", default="metadata_report.txt",
                        help="输出 txt 文件路径（默认 metadata_report.txt）")
    parser.add_argument("--recursive", action="store_true",
                        help="递归搜索子目录")
    parser.add_argument("--version", action="store_true",
                        help="显示版本号")
    parser.add_argument("--formats", default="flac,mp3,m4a,wav",
                        help="扫描的格式（逗号分隔，默认 flac,mp3,m4a,wav）")
    parser.add_argument("--mapping", default=None,
                        help="外部中日汉字映射 CSV 文件（默认使用内嵌映射表）")
    parser.add_argument("--gen-template", metavar="FILE",
                        help="从内嵌映射表生成 CSV 模板文件")
    args = parser.parse_args()

    if args.version:
        print(f"convert_metadata v{VERSION}")
        sys.exit(0)

    if args.gen_template:
        generate_mapping_template(args.gen_template)
        return

    # 过滤格式
    requested_exts = set()
    for fmt in args.formats.split(","):
        clean = fmt.strip().lower().lstrip(".")
        if clean:
            requested_exts.add(f".{clean}")
    valid_exts = {ext for ext in AUDIO_EXTENSIONS if ext in requested_exts}
    if not valid_exts:
        print("错误: 未指定有效的音频格式。")
        sys.exit(1)

    # 加载中日汉字映射
    global _KANJI_MAP
    try:
        _KANJI_MAP = load_kanji_mapping(args.mapping)
    except Exception as e:
        print(f"  ⚠ 无法加载汉字映射表 ({e})，未匹配汉字将替换为 '.'")
        _KANJI_MAP = {}

    audio_files = find_audio_files(args.dir, recursive=args.recursive, exts=valid_exts)

    if not audio_files:
        print(f"在目录 '{args.dir}' 中未找到音频文件。")
        return

    print(f"找到 {len(audio_files)} 个音频文件，正在读取元数据...")

    all_meta = []
    for fpath in audio_files:
        meta = read_metadata(fpath)
        all_meta.append(meta)
        print(f"  ✓ {meta['filename']}")

    generate_report(all_meta, args.output)


if __name__ == "__main__":
    main()
