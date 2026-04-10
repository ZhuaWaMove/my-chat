import sys
import re
from html.parser import HTMLParser

class MyHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text = []
        self.ignore_tags = {'script', 'style', 'meta', 'link', 'head'}
        self.in_ignore = False
        self.current_tag = ''

    def handle_starttag(self, tag, attrs):
        self.current_tag = tag
        if tag in self.ignore_tags:
            self.in_ignore = True

    def handle_endtag(self, tag):
        if tag in self.ignore_tags:
            self.in_ignore = False
        self.current_tag = ''

    def handle_data(self, data):
        if not self.in_ignore and data.strip():
            # 保留段落结构
            if self.current_tag in ['p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'br']:
                self.text.append(data.strip())
            else:
                self.text.append(data.strip())

def extract_text(html_file):
    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()

    # 尝试提取article或main内容区域
    # 查找article标签
    article_pattern = r'<article[^>]*>(.*?)</article>'
    match = re.search(article_pattern, html_content, re.DOTALL | re.IGNORECASE)
    if match:
        html_content = match.group(1)

    # 查找main标签
    main_pattern = r'<main[^>]*>(.*?)</main>'
    match = re.search(main_pattern, html_content, re.DOTALL | re.IGNORECASE)
    if match:
        html_content = match.group(1)

    parser = MyHTMLParser()
    parser.feed(html_content)

    # 合并文本，去除过多空白
    full_text = ' '.join(parser.text)
    full_text = re.sub(r'\s+', ' ', full_text)

    return full_text

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python extract_text.py <html_file>")
        sys.exit(1)

    html_file = sys.argv[1]
    try:
        text = extract_text(html_file)
        print(text[:5000])  # 限制输出长度
    except Exception as e:
        print(f"Error: {e}")