#!/usr/bin/env python3
"""html-to-markdown.py —— 把文档站的渲染页抓成 Markdown，并把图片下载到本地。

用纯标准库实现（html.parser），不依赖 lxml / BeautifulSoup / requests。

配置用一个 JSON 文件描述，脚本本身不含任何站点或产品常量：

    {
      "base_url": "https://docs.example.com",
      "output_dir": "../.doc/MyBoard",
      "asset_dir": "assets",
      "article_marker": "<div class=\\"theme-doc-markdown markdown\\">",
      "source_label": "官方来源",
      "collect_method": "文档站渲染页 → Markdown",
      "pages": [
        {"slug": "MyBoard", "filename": "01-产品总览.md"},
        {"slug": "MyBoard/Resources", "filename": "02-相关资料.md"}
      ]
    }

用法：
    python html-to-markdown.py --config pages.json [--base-url URL] [--output-dir DIR] [--delay SEC]

注意：
    - 只抓公开页面，只发 GET；每次请求之间 sleep delay 秒（默认 1.0），避免打扰上游。
    - 图片按内容去重后写入 asset_dir，Markdown 里的引用改写为相对路径。
    - 已存在的同名图片不重复下载。
"""

import argparse
import datetime
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser


def escape_md(text):
    """转义会改变 Markdown 结构的特殊字符（正文文本用；代码/表格另行处理）。"""
    return re.sub(r"([\\`*_{}\[\]()#+\-.!|>~])", r"\\\1", text)

USER_AGENT = "Mozilla/5.0 (compatible; reference-archive/1.0)"

SKIP_TAGS = {"script", "style", "svg", "noscript", "button", "nav", "iframe", "form"}

IMAGE_EXTS = ("png", "jpg", "jpeg", "webp", "gif", "svg", "bmp", "avif")

# 站点常见的提示块（admonition）类型 -> 中文标签
ADMONITION_LABELS = {
    "warning": "警告",
    "danger": "危险",
    "note": "注意",
    "info": "信息",
    "tip": "提示",
    "caution": "警告",
}

ZERO_WIDTH = "\u200b\u200c\u200d\ufeff"

# 逐个零宽字符剥离：旧实现用整串 replace，只删得掉四个连续字符。
ZERO_WIDTH_CHARS = frozenset(ZERO_WIDTH)


def strip_zero_width(text):
    """剥离任意位置的零宽/不可见字符，而不要求它们连续出现。"""
    return "".join(ch for ch in text if ch not in ZERO_WIDTH_CHARS)

# 这些标签出现时，之前未闭合的 <p> 会被浏览器隐式闭合
CLOSES_P = {
    "div", "ul", "ol", "li", "table", "thead", "tbody", "tfoot", "tr",
    "blockquote", "pre", "hr", "h1", "h2", "h3", "h4", "h5", "h6",
    "section", "article", "figure", "details", "summary", "dl", "dt", "dd",
}


def fetch(url, retries=3, timeout=40):
    """抓一个 URL，返回 bytes；仅瞬时错误重试，两次之间退避，最后一次失败直接抛出。"""
    last = None
    for attempt in range(retries):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return response.read()
        except urllib.error.HTTPError as exc:
            # 4xx（如 404）是确定性错误，重试只会浪费时间。
            if exc.code < 500:
                raise
            last = exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last = exc
        if attempt < retries - 1:
            time.sleep(2 + attempt * 3)
    raise last


class DocParser(HTMLParser):
    """把渲染后的文章正文转成 Markdown。

    处理点：
      - HTML5 可选结束标签：<td>/<th>/<tr>/<p>/<li> 常常不闭合，必须自己补上
      - 提示块（admonition）-> 引用块，标题写成 ``> **警告**｜标题``
      - 锚点：保留链接文字；页内锚点丢弃零宽占位
      - 图片：保留 alt 与 src，稍后本地化；图片在链接里时不另起一行
      - 表格：首行自动作为表头
    """

    def __init__(self, base_url):
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self.out = []
        self.skip_depth = 0
        self.in_code = 0
        self.in_pre = 0
        self.list_stack = []
        self.in_anchor = False
        self.href = ""
        self.anchor_text = []
        # 表格状态
        self.row = []
        self.cell = None
        self.cell_buf = []
        self.head_rows = 0
        self.in_row = False
        # 段落 / 列表状态
        self.open_p = False
        self.li_depth = 0
        # 提示块（栈式，支持嵌套；旧单槽实现里内层 note 会覆盖外层 warning）
        self.admon_stack = []
        self.admon = None  # 当前栈顶，兼容其余读取处
        self.admon_buffer_stack = []
        self.admon_buffer = None

    # ---------- 输出 ----------

    def w(self, text):
        """写一段内联内容。"""
        if not text:
            return
        if self.admon is not None and self.admon["heading_depth"] is not None:
            # 提示块标题：只收纯文本，不加粗体标记
            self.admon["title"] += text
            return
        if self.in_code:
            self.out.append(text)
        elif self.in_anchor:
            self.anchor_text.append(text)
        elif self.cell is not None:
            self.cell_buf.append(text)
        else:
            self.out.append(text)

    def nl(self, count=1):
        """换行。count>=2 表示「块级分隔」，保证空行。"""
        if self.in_code:
            self.out.append("\n" * count)
        elif self.in_anchor:
            pass
        elif self.cell is not None:
            self.cell_buf.append(" ")
        elif count >= 2:
            self.block_break()
        else:
            self.out.append("\n")

    def block_break(self):
        """保证当前位置是一个空行（块级元素之间必须隔开，否则 Markdown 会把后一段并进前一项）。"""
        if not self.out:
            return
        newlines = 0
        for chunk in reversed(self.out):
            if not chunk:
                continue
            stripped = chunk.rstrip("\n")
            newlines += len(chunk) - len(stripped)
            if stripped:
                break
        if newlines < 2:
            self.out.append("\n" * (2 - newlines))

    def ensure_newline(self):
        """只在当前行还没结束时才换行（避免列表被空行打断）。"""
        if self.out and self.out[-1] and not self.out[-1].endswith("\n"):
            self.out.append("\n")

    # ---------- HTML5 可选结束标签 ----------

    def close_cell(self):
        """闭合当前单元格（<td>/<th>）。"""
        if self.cell is None:
            return
        text = re.sub(r"\s+", " ", "".join(self.cell_buf)).strip()
        self.row.append(text)
        self.cell = None
        self.cell_buf = []

    def emit_row(self):
        """输出当前行。"""
        self.close_cell()
        if not self.row:
            return
        cells = [c.replace("|", "\\|").replace("\n", " ").strip() for c in self.row]
        if self.head_rows == 0:
            self.out.append("| " + " | ".join(cells) + " |\n")
            self.out.append("| " + " | ".join(["---"] * len(cells)) + " |\n")
            self.head_rows = 1
        else:
            self.out.append("| " + " | ".join(cells) + " |\n")
        self.row = []

    def close_p(self):
        """闭合未结束的 <p>。"""
        if self.open_p:
            self.open_p = False
            if self.li_depth == 0:
                self.nl(2)

    # ---------- 提示块 ----------

    def flush_admonition(self):
        """把当前提示块渲染成引用块并写回外层输出（栈式，内层 admonition 先 flush 并入外层正文）。"""
        admon = self.admon_stack.pop()
        body = "".join(self.out)
        self.out = self.admon_buffer_stack.pop() if self.admon_buffer_stack else []
        body = re.sub(r"[ \t]+\n", "\n", body)
        body = re.sub(r"\n{3,}", "\n\n", body).strip()
        title = re.sub(r"\s+", " ", admon["title"]).strip()
        label = admon["type"]
        if title == label:
            title = ""
        lines = []
        if title:
            lines.append("> **{}**｜{}".format(label, title))
        else:
            lines.append("> **{}**".format(label))
        lines.append(">")
        for line in body.split("\n"):
            lines.append(">" if not line.strip() else "> " + line)
        self.out.append("\n\n" + "\n".join(lines) + "\n\n")
        self.admon = self.admon_stack[-1] if self.admon_stack else None
        self.admon_buffer = self.out

    # ---------- 标签 ----------

    def handle_starttag(self, tag, attrs):
        attributes = {k: (v if v is not None else "") for k, v in attrs}
        classes = attributes.get("class", "")

        if tag in SKIP_TAGS:
            if tag in ("svg", "iframe"):
                self.skip_depth += 1
            return
        if self.skip_depth:
            return

        # --- 提示块 ---
        if tag == "div" and "theme-admonition" in classes:
            kind = ""
            for key in ADMONITION_LABELS:
                if "theme-admonition-{}".format(key) in classes:
                    kind = key
                    break
            admon = {
                "type": ADMONITION_LABELS.get(kind, "提示"),
                "title": "",
                "depth": 1,
                "heading_depth": None,
            }
            self.admon_stack.append(admon)
            self.admon = admon
            self.admon_buffer_stack.append(self.out)
            self.admon_buffer = self.out
            self.out = []
            return
        if self.admon is not None and tag == "div":
            self.admon["depth"] += 1
            if "admonitionHeading" in classes and self.admon["heading_depth"] is None:
                self.admon["heading_depth"] = self.admon["depth"]
            return

        # --- HTML5 隐式闭合 ---
        if tag in ("td", "th"):
            self.close_cell()
            self.cell = tag
            self.cell_buf = []
            return
        if tag == "tr":
            self.close_cell()
            self.emit_row()
            self.in_row = True
            return
        if tag in ("thead", "tbody", "tfoot"):
            self.close_cell()
            self.emit_row()
            return
        if tag == "p":
            self.close_p()
            if self.li_depth > 0:
                # 上一个 <li> 未闭合就来了 <p>：HTML5 会隐式结束列表项，
                # 渲染也必须断开，否则段落被并进 "- 项目" 那一行。
                self.ensure_newline()
                self.block_break()
            self.open_p = True
            return
        if tag == "li":
            self.close_cell()
            if self.li_depth > 0:
                self.ensure_newline()
            self.li_depth += 1
            self.ensure_newline()
            level = max(0, len(self.list_stack) - 1)
            indent = "  " * level
            if self.list_stack and self.list_stack[-1]["type"] == "ol":
                self.list_stack[-1]["counter"] += 1
                self.w("{}{}. ".format(indent, self.list_stack[-1]["counter"]))
            else:
                self.w("{}- ".format(indent))
            return
        if tag in CLOSES_P:
            self.close_p()

        if tag == "pre":
            self.block_break()
            self.in_pre += 1
            self.in_code += 1
            self.out.append("```\n")
            return
        if tag == "code" and not self.in_pre:
            self.in_code += 1
            self.w("`")
            return
        if tag in ("strong", "b"):
            self.w("**")
            return
        if tag in ("em", "i"):
            self.w("*")
            return
        if tag in ("del", "s"):
            self.w("~~")
            return
        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            level = int(tag[1])
            self.nl(2)
            self.w("#" * level + " ")
            return
        if tag == "br":
            self.nl()
            return
        if tag == "hr":
            self.nl(2)
            self.w("---")
            self.nl(2)
            return
        if tag == "a":
            self.in_anchor = True
            self.href = attributes.get("href", "")
            self.anchor_text = []
            return
        if tag == "img":
            src = attributes.get("src") or attributes.get("data-src") or ""
            alt = attributes.get("alt", "")
            if src.startswith("data:"):
                # 内联 base64 图标：没有可落盘的来源，写成占位文字
                self.w("（{}）".format(alt.strip() or "图标"))
                return
            if not self.in_anchor:
                self.ensure_newline()
            self.w("![{}]({})".format(alt, src))
            return
        if tag in ("ul", "ol"):
            self.list_stack.append({"type": tag, "counter": 0})
            return
        if tag == "table":
            self.head_rows = 0
            self.nl(2)
            return
        if tag == "blockquote":
            self.nl(2)
            self.w("> ")
            return

    def handle_endtag(self, tag):
        if tag in SKIP_TAGS:
            if tag in ("svg", "iframe") and self.skip_depth:
                self.skip_depth -= 1
            return
        if self.skip_depth:
            return

        # --- 提示块收尾 ---
        if self.admon is not None and tag == "div":
            self.admon["depth"] -= 1
            if self.admon["depth"] == 0:
                self.flush_admonition()
            elif self.admon["heading_depth"] is not None and self.admon["depth"] < self.admon["heading_depth"]:
                # 标题 div 已闭合，后续内容回到正文
                self.admon["heading_depth"] = None
            return

        # --- 表格 ---
        if tag in ("td", "th"):
            self.close_cell()
            return
        if tag == "tr":
            self.close_cell()
            self.emit_row()
            self.in_row = False
            return
        if tag in ("thead", "tbody", "tfoot", "table"):
            self.close_cell()
            self.emit_row()
            if tag == "table":
                self.nl(2)
            return

        if tag == "p":
            self.close_p()
            return

        if tag == "pre":
            # 关闭围栏前必须换行：<code>line1\nline2</code> 时末行不带换行，
            # 直接追加 ``` 会把围栏贴到代码后面（旧 bug）。
            self.ensure_newline()
            self.out.append("```\n")
            self.in_pre = max(0, self.in_pre - 1)
            self.in_code = max(0, self.in_code - 1)
            self.block_break()
            return
        if tag == "code" and not self.in_pre:
            self.w("`")
            self.in_code = max(0, self.in_code - 1)
            return
        if tag in ("strong", "b"):
            self.w("**")
            return
        if tag in ("em", "i"):
            self.w("*")
            return
        if tag in ("del", "s"):
            self.w("~~")
            return
        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self.nl(2)
            return
        if tag == "a":
            text = "".join(self.anchor_text).strip()
            href = self.href
            self.in_anchor = False
            self.anchor_text = []
            visible = strip_zero_width(text).strip()
            if href.startswith("#"):
                if visible:
                    self.w(visible)
            else:
                # 只忽略 data:/javascript:/mailto: 等非页面链接；
                # 相对路径（./other/page）交给 urljoin，根目录 /abs 拼 base_url。
                absolute = urllib.parse.urljoin(self.base_url + "/", href)
                scheme = urllib.parse.urlparse(absolute).scheme
                if scheme not in ("http", "https"):
                    if visible:
                        self.w(text)
                else:
                    self.w("[{}]({})".format(text, absolute))
            return
        if tag in ("ul", "ol"):
            if self.list_stack:
                self.list_stack.pop()
            # 列表嵌套在列表项里时不加空行，否则会打断外层列表
            self.nl(2 if self.li_depth == 0 else 1)
            return
        if tag == "li":
            self.li_depth = max(0, self.li_depth - 1)
            return
        if tag == "blockquote":
            self.nl(2)
            return

    def handle_data(self, data):
        if self.skip_depth:
            return
        if self.in_pre:
            self.out.append(data)
            return
        if not data.strip():
            if self.in_code:
                return
            if self.out and self.out[-1] and not self.out[-1].endswith(" ") and not self.out[-1].endswith("\n"):
                self.w(" ")
            return
        text = re.sub(r"\s+", " ", data)
        text = strip_zero_width(text)
        self.w(escape_md(text))

    def result(self):
        text = "".join(self.out)
        text = re.sub(r"[ \t]+\n", "\n", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return "\n".join(line.rstrip() for line in text.split("\n"))


def extract_article(html, marker):
    """截出文章正文。marker 命中就从它所在的开标签配对，否则回退到 <article>。

    旧实现无论从哪种标签开始都只数 <div>，回退 <article> 时会在首个 </div>
    处截断（甚至切在 '<' 上），把正文腰斩。这里按实际起始标签名分派配对，
    并跳到每个标签的 '>' 之后再继续扫描。
    """
    start = html.find(marker) if marker else -1
    if start < 0:
        start = html.find("<article")
    if start < 0:
        raise RuntimeError("article body not found — 检查配置里的 article_marker")

    # marker 可能落在标签内部，回退到最近的 '<' 以拿到完整开标签
    tag_start = html.rfind("<", 0, start + 1)
    if tag_start < 0:
        tag_start = start
    opening = re.match(r"<([A-Za-z][A-Za-z0-9]*)", html[tag_start:])
    tag = opening.group(1).lower() if opening else "div"
    start = tag_start

    gt = html.find(">", start)
    if gt < 0:
        raise RuntimeError("article marker 开标签未闭合")

    pattern = re.compile(r"<(/?){}\b".format(re.escape(tag)), re.I)
    depth = 1
    cursor = gt + 1
    while cursor < len(html) and depth > 0:
        match = pattern.search(html, cursor)
        if not match:
            break
        depth += -1 if match.group(1) else 1
        end = html.find(">", match.end())
        cursor = end + 1 if end >= 0 else match.end()
    return html[start:cursor]


def safe_name(relative):
    """把站点路径尾段变成安全的文件名，查询串编码进文件名以免不同版本互相覆盖。"""
    parsed = urllib.parse.urlsplit(relative)
    tail = parsed.path.split("/")[-1]
    stem, dot, ext = tail.rpartition(".")
    if not dot:
        stem, ext = tail, ""
    stem = re.sub(r"[^A-Za-z0-9._-]", "_", stem) or "image"
    ext = re.sub(r"[^A-Za-z0-9]", "", ext).lower()
    if parsed.query:
        query = re.sub(r"[^A-Za-z0-9]", "_", parsed.query)[:40]
        stem = "{}_{}".format(stem, query)
    return stem + ("." + ext if ext else ".bin")


def find_images(body):
    """找出正文里的图片路径。站点的 img 标签属性常常不加引号，两种写法都要认。"""
    pattern = re.compile(
        r"""\b(?:src|data-src)\s*=\s*(?:"([^"]+)"|'([^']+)'|([^\s>]+))""", re.I
    )
    found = []
    for match in pattern.finditer(body):
        value = match.group(1) or match.group(2) or match.group(3) or ""
        if not value or value.startswith("data:"):
            continue
        # 扩展名看 path，去重键保留查询串：?v=2 与 ?v=9 是两张不同的图。
        path = urllib.parse.urlsplit(value).path
        if not path.lower().endswith(tuple("." + e for e in IMAGE_EXTS)):
            continue
        if value not in found:
            found.append(value)
    return sorted(found)


def rewrite_markdown_target(markdown, old, new):
    """只改写 Markdown 图片/链接语法里的目标，不碰正文中恰好含该子串的 URL。"""
    pattern = re.compile(
        r"(!?\[[^\]]*\]\()(" + re.escape(old) + r")(\s+(?:\"[^\"]*\"|'[^']*'))?(\))"
    )
    return pattern.sub(
        lambda m: "{}{}{}{}".format(m.group(1), new, m.group(3) or "", m.group(4)),
        markdown,
    )


def localize_images(markdown, body, base_url, asset_dir, asset_root, delay):
    """下载正文里的图片，返回改写后的 Markdown 与图片清单。"""
    candidates = find_images(body)
    manifest = []
    used_names = {}
    for relative in candidates:
        name = safe_name(relative)
        if name in used_names:
            # 不同来源的文件名撞车：加来源短哈希，避免后者覆盖前者的错图。
            suffix = hashlib.md5(relative.encode("utf-8")).hexdigest()[:8]
            stem, dot, ext = name.rpartition(".")
            name = "{}_{}{}".format(stem, suffix, "." + ext if dot else "")
            counter = 1
            while name in used_names:
                stem, dot, ext = name.rpartition(".")
                name = "{}_{}{}".format(stem, suffix + str(counter), "." + ext if dot else "")
                counter += 1
        used_names[name] = relative

        destination = os.path.join(asset_dir, name)
        if not os.path.exists(destination):
            url = relative if relative.lower().startswith(("http://", "https://")) else base_url + relative
            try:
                data = fetch(url)
                with open(destination, "wb") as handle:
                    handle.write(data)
                digest = hashlib.md5(data).hexdigest()
            except Exception as exc:  # noqa: BLE001
                print("  IMAGE FAIL {}: {}".format(relative, exc))
                continue
        else:
            with open(destination, "rb") as handle:
                digest = hashlib.md5(handle.read()).hexdigest()
        manifest.append({"file": name, "md5": digest, "bytes": os.path.getsize(destination)})
        markdown = rewrite_markdown_target(
            markdown, relative, "{}/{}".format(asset_root, name)
        )
        time.sleep(delay)
    return markdown, manifest


def strip_leading_title(markdown, title):
    """正文首个 H1 与文件标题重复时去掉，正文里再出现一个 H1 就是噪音。"""
    lines = markdown.split("\n")
    index = 0
    while index < len(lines) and not lines[index].strip():
        index += 1
    if index < len(lines) and lines[index].strip() == "# {}".format(title):
        return "\n".join(lines[index + 1:]).lstrip("\n")
    return markdown


def build_header(title, url, config, asset_root):
    source_label = config.get("source_label", "官方来源")
    method = config.get("collect_method", "文档站渲染页 → Markdown")
    collected = config.get("collect_time") or datetime.date.today().isoformat()
    return (
        "# {title}\n\n"
        "> {source_label}：<{url}>\n"
        "> 采集时间：{collected} ｜ 采集方式：{method}\n"
        "> 本文件为原页面正文存档，内容未做增删改写；图片已下载到同目录 `{asset_root}/`。\n\n"
    ).format(title=title, url=url, source_label=source_label, collected=collected,
             method=method, asset_root=asset_root)


def main():
    parser = argparse.ArgumentParser(description="抓文档站渲染页 -> Markdown（图片本地化）")
    parser.add_argument("--config", required=True, help="JSON 配置（base_url / pages / article_marker ...）")
    parser.add_argument("--base-url", default=None, help="覆盖配置里的 base_url")
    parser.add_argument("--output-dir", default=None, help="覆盖配置里的 output_dir")
    parser.add_argument("--delay", type=float, default=1.0, help="每次请求之间的间隔秒，默认 1.0")
    args = parser.parse_args()

    with open(args.config, encoding="utf-8") as handle:
        config = json.load(handle)

    base_url = (args.base_url or config["base_url"]).rstrip("/")
    output_dir = args.output_dir or config["output_dir"]
    asset_root = config.get("asset_dir", "assets")
    asset_dir = os.path.join(output_dir, asset_root)
    marker = config.get("article_marker", "")

    os.makedirs(asset_dir, exist_ok=True)
    summary = []
    for page in config["pages"]:
        slug = page["slug"]
        filename = page["filename"]
        if os.path.basename(filename) != filename or filename in (".", ".."):
            sys.exit("错误: 配置里的 filename 不能含路径分隔符或 ..：{!r}".format(filename))
        url = "{}/{}/".format(base_url, slug)
        print("FETCH", url, flush=True)
        html = fetch(url).decode("utf-8", "replace")
        body = extract_article(html, marker)
        parser_obj = DocParser(base_url)
        parser_obj.feed(body)
        markdown = parser_obj.result()

        title_match = re.search(r"<h1[^>]*>(.*?)</h1>", body, re.S)
        title = re.sub(r"<[^>]+>", "", title_match.group(1)).strip() if title_match else filename
        markdown = strip_leading_title(markdown, title)

        markdown, images = localize_images(markdown, body, base_url, asset_dir, asset_root, args.delay)

        header = build_header(title, url, config, asset_root)
        destination = os.path.join(output_dir, filename)
        with open(destination, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(header + markdown.strip() + "\n")

        summary.append({
            "filename": filename,
            "title": title,
            "url": url,
            "chars": len(markdown),
            "images": len(images),
        })
        print("  OK {} chars={} images={}".format(filename, len(markdown), len(images)), flush=True)
        time.sleep(args.delay)

    print("DONE {} pages".format(len(summary)))
    for item in summary:
        print("  {filename}  chars={chars}  images={images}  {url}".format(**item))
    return 0


if __name__ == "__main__":
    sys.exit(main())
