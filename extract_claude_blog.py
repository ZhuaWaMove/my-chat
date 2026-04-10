import sys
import re
from html.parser import HTMLParser

class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text_parts = []
        self.inside_script = False
        self.inside_style = False
        self.inside_noscript = False
        self.ignore_tags = {'script', 'style', 'noscript', 'meta', 'link', 'head'}
        self.current_tag = ''

    def handle_starttag(self, tag, attrs):
        self.current_tag = tag
        if tag in self.ignore_tags:
            if tag == 'script':
                self.inside_script = True
            elif tag == 'style':
                self.inside_style = True
            elif tag == 'noscript':
                self.inside_noscript = True

    def handle_endtag(self, tag):
        if tag in self.ignore_tags:
            if tag == 'script':
                self.inside_script = False
            elif tag == 'style':
                self.inside_style = False
            elif tag == 'noscript':
                self.inside_noscript = False
        self.current_tag = ''

    def handle_data(self, data):
        if not self.inside_script and not self.inside_style and not self.inside_noscript:
            stripped = data.strip()
            if stripped:
                # 检查是否可能是文章内容（包含句子或段落）
                if len(stripped) > 20 and (' ' in stripped or '.' in stripped):
                    self.text_parts.append(stripped)

def extract_blog_content(html_file):
    with open(html_file, 'r', encoding='utf-8', errors='ignore') as f:
        html_content = f.read()

    # 首先尝试查找包含博客内容的特定区域
    # 查找常见的博客内容容器
    patterns = [
        r'<article[^>]*>(.*?)</article>',
        r'<main[^>]*>(.*?)</main>',
        r'<div[^>]*class="[^"]*blog[^"]*"[^>]*>(.*?)</div>',
        r'<div[^>]*class="[^"]*content[^"]*"[^>]*>(.*?)</div>',
        r'<div[^>]*class="[^"]*post[^"]*"[^>]*>(.*?)</div>',
        r'<div[^>]*class="[^"]*richtext[^"]*"[^>]*>(.*?)</div>'
    ]

    extracted_content = None
    for pattern in patterns:
        match = re.search(pattern, html_content, re.DOTALL | re.IGNORECASE)
        if match:
            extracted_content = match.group(1)
            print(f"Found content with pattern: {pattern[:50]}...")
            break

    # 如果没有找到特定区域，使用整个HTML
    if not extracted_content:
        print("No specific content region found, using entire HTML")
        extracted_content = html_content

    # 使用解析器提取文本
    parser = TextExtractor()
    parser.feed(extracted_content)

    # 合并文本，去除过多空白
    full_text = ' '.join(parser.text_parts)
    full_text = re.sub(r'\s+', ' ', full_text)

    return full_text

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python extract_claude_blog.py <html_file>")
        sys.exit(1)

    html_file = sys.argv[1]
    try:
        text = extract_blog_content(html_file)

        # 写入输出文件
        output_file = html_file.replace('.html', '_extracted.txt')
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(text)

        print(f"Extracted text saved to: {output_file}")
        print(f"\nFirst 2000 characters:")
        print(text[:2000])

        # 统计
        print(f"\nTotal characters: {len(text)}")
        print(f"Total words: {len(text.split())}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()