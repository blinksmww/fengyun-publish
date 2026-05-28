"""
半角→全角标点替换工具 v3(逐字符扫描)

策略:逐字符遍历正文,prev / next 是中文时,ASCII 标点替换为全角。
保护:frontmatter / 代码块(```) / 行内代码(`) / URL 不动。

双入口(SPEC_ROUND26_HUMAN_GATE_FIX.md 漏洞 B):
- CLI:  python tools/fix_punctuation.py <draft.md>  → 半角化写回 + 备份
- import: fix_punctuation_text(text) -> (str, n_changes)   纯文本转换
          fix_punctuation_file(path) -> (n_changes, skipped) 文件级(切 fm + 跳代码块)
"""
from __future__ import annotations
import sys, re
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# 用显式 unicode codepoint 避免 Claude 写时下意识半角的 bug
PUNCT_MAP = {
    ",": chr(0xFF0C),  # ，
    ";": chr(0xFF1B),  # ；
    ":": chr(0xFF1A),  # ：
    "!": chr(0xFF01),  # ！
    "?": chr(0xFF1F),  # ？
    "(": chr(0xFF08),  # （
    ")": chr(0xFF09),  # ）
}
FULL_PERIOD = chr(0x3002)        # 。
FULL_DQUOTE_OPEN = chr(0x201C)   # "
FULL_DQUOTE_CLOSE = chr(0x201D)  # "
FULL_SQUOTE_OPEN = chr(0x2018)   # '
FULL_SQUOTE_CLOSE = chr(0x2019)  # '

# 句号单独处理(避免 3.14 file.txt)
# 双引号配对处理

# 代码块 / 行内代码 / URL 保护正则(供 stash 用)
_FENCED_RE = re.compile(r"```[\s\S]*?```")
_INLINE_RE = re.compile(r"`[^`\n]+`")
_URL_RE = re.compile(r"https?://[^\s\)]+")


def is_cn(ch):
    return "一" <= ch <= "鿿" or "　" <= ch <= "〿" \
           or "＀" <= ch <= "￯"


def fix_punctuation_text(text: str) -> tuple[str, int]:
    """对一段正文应用 CN 全角标点规则。

    代码块(```)/ 行内代码(`)/ URL 自动保护,转换后原样恢复。
    不处理 frontmatter — 调用方(fix_punctuation_file)负责先切掉。

    Returns:
        (转换后文本, 替换处数)
    """
    # 用占位符保护代码块 / 行内代码 / URL
    placeholders: dict[str, str] = {}
    counter = [0]

    def stash(m):
        key = f"\x00STASH{counter[0]}\x00"
        placeholders[key] = m.group(0)
        counter[0] += 1
        return key

    body = _FENCED_RE.sub(stash, text)
    body = _INLINE_RE.sub(stash, body)
    body = _URL_RE.sub(stash, body)

    # 逐字符扫描
    chars = list(body)
    n_changes = 0
    quote_state = False  # 双引号配对状态

    for i, ch in enumerate(chars):
        # 跳过占位符
        if ch == "\x00":
            quote_state = False
            continue

        # 句号特殊(前一字符是中文,后一字符是中文/空白/句末/标点)
        if ch == ".":
            prev_cn = i > 0 and is_cn(chars[i-1])
            next_ok = (i + 1 >= len(chars)) or chars[i+1] in " \n\t" or is_cn(chars[i+1]) \
                      or chars[i+1] in ",。;:!?「」『』"
            if prev_cn and next_ok:
                chars[i] = FULL_PERIOD
                n_changes += 1
            continue

        # 双引号配对
        if ch == '"':
            line_has_cn = any(
                is_cn(chars[j]) for j in range(max(0, i-30), min(len(chars), i+30))
                if chars[j] != "\x00"
            )
            if line_has_cn:
                chars[i] = FULL_DQUOTE_OPEN if not quote_state else FULL_DQUOTE_CLOSE
                quote_state = not quote_state
                n_changes += 1
            continue

        # 单引号
        if ch == "'":
            prev_alpha = i > 0 and chars[i-1].isalpha() and chars[i-1].isascii()
            next_alpha = (i + 1 < len(chars)) and chars[i+1].isalpha() and chars[i+1].isascii()
            if prev_alpha or next_alpha:
                continue
            line_has_cn = any(
                is_cn(chars[j]) for j in range(max(0, i-30), min(len(chars), i+30))
                if chars[j] != "\x00"
            )
            if line_has_cn:
                chars[i] = FULL_SQUOTE_CLOSE
                n_changes += 1
            continue

        # 一般 ASCII 标点(只在中文上下文里替换)
        if ch in PUNCT_MAP:
            prev_cn = i > 0 and is_cn(chars[i-1])
            next_cn = (i + 1 < len(chars)) and is_cn(chars[i+1])
            # 中文+标点 / 标点+中文 → 全角
            if prev_cn or next_cn:
                chars[i] = PUNCT_MAP[ch]
                n_changes += 1

    result = "".join(chars)

    # 恢复占位符
    for key, val in placeholders.items():
        result = result.replace(key, val)

    return result, n_changes


def fix_punctuation_file(path) -> tuple[int, int]:
    """读取 markdown 文件,切掉 frontmatter,对正文跑 fix_punctuation_text,写回 + 备份。

    Args:
        path: markdown 文件路径(str / Path)

    Returns:
        (替换处数, 跳过的代码块数)
    """
    path = Path(path)
    raw = path.read_text(encoding="utf-8")

    # 切 frontmatter(不参与替换)
    fm = ""
    body = raw
    if raw.startswith("---"):
        parts = raw.split("---", 2)
        if len(parts) >= 3:
            fm = "---" + parts[1] + "---"
            body = parts[2]

    # 跳过的代码块数(供调用方/CLI 报告)
    skipped = len(_FENCED_RE.findall(body))

    new_body, n_changes = fix_punctuation_text(body)
    result = fm + new_body if fm else new_body

    # 备份 + 写入
    backup = path.with_suffix(path.suffix + ".bak")
    backup.write_text(raw, encoding="utf-8")
    path.write_text(result, encoding="utf-8")

    return n_changes, skipped


def main():
    if len(sys.argv) < 2:
        print("用法: python fix_punctuation.py <markdown_path>")
        sys.exit(1)

    path = Path(sys.argv[1])
    n_changes, skipped = fix_punctuation_file(path)
    backup = path.with_suffix(path.suffix + ".bak")

    print(f"Fixed {n_changes} punctuation marks in {path.name} (跳过 {skipped} 个代码块)")
    print(f"  备份: {backup}")


if __name__ == "__main__":
    main()
