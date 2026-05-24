#!/usr/bin/env python3
"""从 日漢转中汉.xlsx 生成 HTML 对照参考文档。"""

import openpyxl

XLSX_PATH = "日漢转中汉.xlsx"
HTML_PATH = "日漢中汉对照表.html"


def load_mappings(path: str) -> tuple[list[tuple[str, str]], list[tuple[str, str]]]:
    """读取全表 sheet，返回 (相同, 不同) 两组映射。"""
    wb = openpyxl.load_workbook(path)
    ws = wb["全表"]

    same, diff = [], []
    for row in ws.iter_rows(min_row=2, max_row=ws.max_row, values_only=True):
        a, b = str(row[0]) if row[0] is not None else "", str(row[1]) if row[1] is not None else ""
        a, b = a.strip(), b.strip()
        if not a or not b or len(a) != 1 or len(b) != 1:
            continue
        if ord(a) < 0x4E00:
            continue  # 跳过非 CJK 符号
        tup = (a, b)
        if a == b:
            same.append(tup)
        else:
            diff.append(tup)
    return same, diff


def fmt_hex(ch: str) -> str:
    """返回 U+XXXX 格式。"""
    return f"U+{ord(ch):04X}"


def generate_html(same: list, diff: list) -> str:
    """生成完整的 HTML 文档。"""

    # 相异映射表格行
    diff_rows = ""
    for jp, cn in diff:
        diff_rows += f"""
            <tr>
              <td class="char-jp">{jp}</td>
              <td class="code">{fmt_hex(jp)}</td>
              <td class="arrow">→</td>
              <td class="char-cn">{cn}</td>
              <td class="code">{fmt_hex(cn)}</td>
            </tr>"""

    # 相同映射表格行（中日共通汉字）
    same_rows = ""
    for jp, cn in same[:200]:  # 展示前 200 个，避免页面过长
        same_rows += f"""
            <tr>
              <td class="char-common">{jp}</td>
              <td class="code">{fmt_hex(jp)}</td>
              <td class="code">{fmt_hex(cn)}</td>
            </tr>"""

    total_same = len(same)
    total_diff = len(diff)
    same_shown = min(total_same, 200)
    same_hidden = total_same - same_shown

    return f"""<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>日漢 → 中汉 对照表</title>
<style>
  :root {{
    --bg: #fafafa;
    --card: #ffffff;
    --border: #e0e0e0;
    --text: #1a1a1a;
    --accent: #2563eb;
    --accent-light: #eff6ff;
    --jp-color: #b91c1c;
    --cn-color: #047857;
    --diff-bg: #fef2f2;
    --same-bg: #f0fdf4;
  }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: -apple-system, "SF Pro", "Noto Sans CJK SC", "Hiragino Sans", sans-serif;
    background: var(--bg);
    color: var(--text);
    line-height: 1.6;
    padding: 24px;
  }}
  .container {{ max-width: 960px; margin: 0 auto; }}

  /* 页头 */
  header {{
    background: var(--card);
    border-radius: 16px;
    padding: 32px 40px;
    margin-bottom: 24px;
    box-shadow: 0 1px 3px rgba(0,0,0,.08);
  }}
  header h1 {{ font-size: 28px; font-weight: 700; margin-bottom: 4px; }}
  header p {{ color: #666; font-size: 14px; }}
  .stats {{
    display: flex; gap: 16px; margin-top: 16px;
  }}
  .stat {{ padding: 8px 20px; border-radius: 99px; font-size: 14px; font-weight: 600; }}
  .stat-diff {{ background: var(--diff-bg); color: var(--jp-color); }}
  .stat-same {{ background: var(--same-bg); color: var(--cn-color); }}

  /* 搜索 */
  .search-bar {{
    margin-bottom: 24px;
  }}
  .search-bar input {{
    width: 100%;
    padding: 12px 16px;
    font-size: 16px;
    border: 2px solid var(--border);
    border-radius: 12px;
    outline: none;
    transition: border .2s;
  }}
  .search-bar input:focus {{
    border-color: var(--accent);
  }}

  /* 表格卡片 */
  .card {{
    background: var(--card);
    border-radius: 16px;
    overflow: hidden;
    box-shadow: 0 1px 3px rgba(0,0,0,.08);
    margin-bottom: 32px;
  }}
  .card h2 {{
    padding: 20px 24px 0;
    font-size: 20px;
  }}
  .card .subtitle {{
    padding: 4px 24px 16px;
    font-size: 13px;
    color: #888;
  }}

  table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 15px;
  }}
  th {{
    background: #f5f5f5;
    text-align: left;
    padding: 10px 12px;
    font-weight: 600;
    font-size: 13px;
    color: #555;
    position: sticky;
    top: 0;
  }}
  td {{
    padding: 8px 12px;
    border-top: 1px solid var(--border);
  }}
  tr:hover {{ background: #f9f9f9; }}

  /* 字符样式 */
  .char-jp {{ font-size: 28px; text-align: center; color: var(--jp-color); font-weight: 600; }}
  .char-cn {{ font-size: 28px; text-align: center; color: var(--cn-color); font-weight: 600; }}
  .char-common {{ font-size: 24px; text-align: center; color: #555; }}
  .code {{ font-family: "SF Mono", Monaco, monospace; font-size: 12px; color: #999; }}
  .arrow {{ text-align: center; color: #ccc; font-size: 18px; }}

  .diff-table tr {{ background: var(--diff-bg); }}

  /* 中日共通表只显示一部分 + 折叠 */
  .fold-hint {{
    padding: 16px 24px;
    text-align: center;
    color: #999;
    font-size: 13px;
    border-top: 1px solid var(--border);
  }}

  /* 分类标签 */
  .category-tag {{
    display: inline-block;
    padding: 2px 10px;
    border-radius: 99px;
    font-size: 11px;
    font-weight: 600;
    margin-left: 8px;
    vertical-align: middle;
  }}
  .tag-diff {{ background: var(--diff-bg); color: var(--jp-color); }}
  .tag-same {{ background: var(--same-bg); color: var(--cn-color); }}
</style>
</head>
<body>
<div class="container">

<header>
  <h1>日漢 → 中汉 对照表</h1>
  <p>基于「日漢转中汉.xlsx · 全表」生成 · 收录中日汉字映射关系</p>
  <div class="stats">
    <span class="stat stat-diff">🟡 相异 {total_diff} 组</span>
    <span class="stat stat-same">🟢 共通 {total_same} 字</span>
    <span class="stat" style="background:#f5f5f5;color:#666;">合计 {total_same + total_diff} 字</span>
  </div>
</header>

<div class="search-bar">
  <input type="text" id="searchInput" placeholder="搜索日文或中文汉字…" oninput="filterTable()">
</div>

<!-- 相异映射 -->
<div class="card">
  <h2>字形相异 <span class="category-tag tag-diff">{total_diff} 组</span></h2>
  <p class="subtitle">日文汉字（左侧）与中文汉字（右侧）字形不同</p>
  <div style="max-height: 600px; overflow-y: auto;">
  <table class="diff-table" id="diffTable">
    <thead><tr>
      <th>日文</th><th>Unicode</th><th></th><th>中文</th><th>Unicode</th>
    </tr></thead>
    <tbody>
      {diff_rows}
    </tbody>
  </table>
  </div>
</div>

<!-- 相同映射（部分） -->
<div class="card">
  <h2>中日共通 <span class="category-tag tag-same">{total_same} 字</span></h2>
  <p class="subtitle">中日写法相同的汉字（仅展示前 {same_shown} 字）</p>
  <div style="max-height: 400px; overflow-y: auto;">
  <table id="sameTable">
    <thead><tr>
      <th>汉字</th><th>Unicode (日)</th><th>Unicode (中)</th>
    </tr></thead>
    <tbody>
      {same_rows}
    </tbody>
  </table>
  </div>
  {f'<div class="fold-hint">… 另有 {same_hidden} 个共通汉字未显示</div>' if same_hidden > 0 else ''}
</div>

</div><!-- /container -->

<script>
function filterTable() {{
  var q = document.getElementById('searchInput').value.trim();
  var tables = ['diffTable', 'sameTable'];
  tables.forEach(function(tid) {{
    var table = document.getElementById(tid);
    if (!table) return;
    var rows = table.querySelectorAll('tbody tr');
    rows.forEach(function(row) {{
      if (!q) {{
        row.style.display = '';
        return;
      }}
      var text = row.textContent.toLowerCase();
      row.style.display = text.indexOf(q.toLowerCase()) !== -1 ? '' : 'none';
    }});
  }});
}}

/* 支持通过 URL 参数 ?q=xxx 预填充 */
(function() {{
  var params = new URLSearchParams(window.location.search);
  var q = params.get('q');
  if (q) {{
    document.getElementById('searchInput').value = q;
    filterTable();
  }}
}})();
</script>

</body>
</html>"""


if __name__ == "__main__":
    print("读取 Excel...")
    same, diff = load_mappings(XLSX_PATH)
    print(f"  共 {len(same) + len(diff)} 条记录")
    print(f"    相异: {len(diff)}")
    print(f"    共通: {len(same)}")
    print("生成 HTML...")
    html = generate_html(same, diff)
    with open(HTML_PATH, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"已保存: {HTML_PATH}")
