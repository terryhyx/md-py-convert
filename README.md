# 歌曲信息转换工具

从 FLAC / MP3 / M4A / WAV 音频文件中提取歌曲元数据（歌名、专辑名、表演者等），自动进行中文转拼音和中文转日语汉字两种转换，并生成报告。

## 快速开始

```bash
# 直接运行可执行文件
./dist/convert_metadata

# 处理指定目录
./dist/convert_metadata --dir /path/to/music

# 递归搜索子目录
./dist/convert_metadata --dir /path/to/music --recursive
```

输出文件默认为 `metadata_report.txt`。

## 功能

- **中文转拼音** — 每个汉字转换为拼音，首字母大写，空格分隔
- **中文转日语汉字** — 简体中文转换为字形相似的日语汉字（内置 6,443 组对照关系）
- 支持自定义映射表（`--mapping`）和导出映射模板（`--gen-template`）

## 系统要求

- macOS (arm64 / Apple Silicon)
- 无需安装 Python 或其他依赖（使用预编译可执行文件）

## 参数

| 参数 | 说明 |
|------|------|
| `--dir <目录>` | 指定音频文件目录 |
| `--output <文件>` | 指定输出文件路径 |
| `--recursive` | 递归搜索子目录 |
| `--formats <格式>` | 扫描格式（逗号分隔） |
| `--mapping <CSV>` | 指定外部中日汉字映射 CSV 文件 |
| `--gen-template <FILE>` | 生成 CSV 映射模板 |
| `--version` | 显示版本号 |
| `--help` | 显示帮助信息 |

## 构建

```bash
source .venv/bin/activate
pip install pyinstaller
pyinstaller --onefile --name convert_metadata --add-data "kanji_map.csv:." convert_metadata.py
```

## 许可

仅供个人学习使用。
