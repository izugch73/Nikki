#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import glob
import re
from datetime import datetime
# import markdown

def simple_markdown_to_html(markdown_text):
    """簡易的なMarkdown→HTML変換"""
    html = markdown_text
    
    # 見出し変換
    html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
    html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
    html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
    
    # リンク変換 [テキスト](URL)
    html = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2" target="_blank">\1</a>', html)
    
    # 段落分け（空行で区切る）
    paragraphs = html.split('\n\n')
    html_paragraphs = []
    
    for para in paragraphs:
        para = para.strip()
        if para:
            # 見出しでない場合はpタグで囲む
            if not (para.startswith('<h') and para.endswith('>')):
                # リスト処理
                if '- ' in para:
                    lines = para.split('\n')
                    list_items = []
                    for line in lines:
                        line = line.strip()
                        if line.startswith('- '):
                            list_items.append(f'<li>{line[2:]}</li>')
                        elif line and not line.startswith('<'):
                            list_items.append(f'<li>{line}</li>')
                    if list_items:
                        para = '<ul>' + ''.join(list_items) + '</ul>'
                else:
                    # 改行を<br>に変換
                    para = para.replace('\n', '<br>')
                    para = f'<p>{para}</p>'
            html_paragraphs.append(para)
    
    return '\n'.join(html_paragraphs)

def read_markdown_files():
    """docs/内の全てのMarkdownファイルを読み込む"""
    md_files = sorted(glob.glob("docs/*.md"))
    articles = []
    
    for md_file in md_files:
        # ファイル名から数値を抽出（4桁以上8桁以下の数字.md形式）
        filename = os.path.basename(md_file)
        match = re.match(r'(\d{4,8})\.md', filename)
        
        if match:
            date_str = match.group(1)
            # 日付はそのまま使用（数値形式）
            formatted_date = date_str
            
            # Markdownファイルを読み込み
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 簡易的なMarkdown→HTML変換
            html_content = simple_markdown_to_html(content)
            
            articles.append({
                'date': formatted_date,
                'content': html_content,
                'raw_date': date_str
            })
    
    # 数値順でソート（0000が先頭、99999999が最後尾）
    articles.sort(key=lambda x: int(x['raw_date']))
    
    return articles

def generate_scroll_logic_func(num_articles):
    """記事数に応じたスクロール位置計算ロジックを生成"""
    if num_articles <= 1:
        return "scrollPosition = 0;"
    
    logic_parts = []
    for i in range(num_articles):
        if i == 0:
            logic_parts.append(f"if (index === {i}) {{")
            logic_parts.append("    scrollPosition = maxScroll;")
        elif i == num_articles - 1:
            logic_parts.append(f"}} else if (index === {i}) {{")
            logic_parts.append("    scrollPosition = 0;")
        else:
            ratio = (num_articles - 1 - i) / (num_articles - 1)
            logic_parts.append(f"}} else if (index === {i}) {{")
            logic_parts.append(f"    scrollPosition = maxScroll * {ratio:.3f};")
    
    logic_parts.append("} else {")
    logic_parts.append("    scrollPosition = 0;")
    logic_parts.append("}")
    
    return "\n            ".join(logic_parts)

def main():
    """メイン処理"""
    # docs/ディレクトリが存在するかチェック
    if not os.path.exists("docs"):
        print("Error: docs/ ディレクトリが見つかりません")
        return
    
    # Markdownファイルを読み込み
    articles = read_markdown_files()
    
    if not articles:
        print("Warning: docs/ 内にMarkdownファイルが見つかりません")
        # 空のindex.htmlを生成
        html_content = """<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>日記</title>
    <style>
        body {
            margin: 0;
            padding: 0;
            font-family: 'Hiragino Mincho ProN', 'Yu Mincho', serif;
            background-color: #f8f8f8;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
        }
        .empty-message {
            font-size: 24px;
            color: #666;
            text-align: center;
        }
    </style>
</head>
<body>
    <div class="empty-message">まだ日記が書かれていません</div>
</body>
</html>"""
    else:
        print(f"Info: {len(articles)}個の記事を読み込みました")
        # HTMLを生成
        contents_js = []
        for article in reversed(articles):  # 最新が先頭になるように逆順
            escaped_content = article['content'].replace('`', '\\`').replace('${', '\\${')
            contents_js.append(f"""{{
            date: "{article['date']}",
            content: `{escaped_content}`
        }}""")
        
        contents_array = ",\n        ".join(contents_js)
        
        # ドット生成（記事数に応じて）
        dots_html = ""
        for i in range(len(articles)):  # 記事順で生成
            dots_html += f'        <div class="dot" data-index="{i}"></div>\n'
        
        # スクロールロジック生成
        scroll_logic = generate_scroll_logic_func(len(articles))
        
        html_content = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>日記</title>
    <style>
        body {{
            margin: 0;
            padding: 0;
            background-color: #f5f5f5;
            font-family: 'Hiragino Mincho ProN', 'Yu Mincho', serif;
            overflow-y: hidden;
        }}
        
        .container {{
            height: 80vh;
            margin-top: 10vh;
            overflow-x: scroll;
            overflow-y: hidden;
            display: flex;
            flex-direction: row;
            flex-wrap: nowrap;
            padding: 0 20px;
            box-sizing: border-box;
            align-items: center;
        }}
        
        .content {{
            height: 100%;
            margin-right: 60px;
            flex-shrink: 0;
            width: auto;
            writing-mode: vertical-rl;
            text-orientation: mixed;
        }}
        
        .content:last-child {{
            margin-right: 0;
        }}
        
        h2 {{
            font-size: 2.5em;
            margin-bottom: 20px;
            color: #4a3c5a;
            font-family: 'Hiragino Kaku Gothic ProN', 'Yu Gothic', sans-serif;
            font-weight: 700;
            letter-spacing: 0.1em;
        }}
        
        h3 {{
            font-size: 1.4em;
            margin-bottom: 15px;
            color: #444;
            font-family: 'Hiragino Kaku Gothic ProN', 'Yu Gothic', sans-serif;
            font-weight: 700;
        }}
        
        p {{
            line-height: 2;
            font-size: 1.1em;
            color: #444;
            margin-bottom: 1.5em;
            text-align: justify;
            text-indent: 1em;
        }}
        
        ul, ol {{
            margin-bottom: 1.5em;
            padding-right: 1.5em;
        }}
        
        li {{
            margin-bottom: 0.5em;
            line-height: 2;
        }}
        
        code {{
            background-color: #e8e8e8;
            padding: 0.2em 0.4em;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
        }}
        
        pre {{
            background-color: #e8e8e8;
            padding: 1em;
            border-radius: 5px;
            overflow-x: auto;
            margin-bottom: 1.5em;
        }}
        
        pre code {{
            background-color: transparent;
            padding: 0;
        }}
        
        blockquote {{
            border-right: 4px solid #ddd;
            padding-right: 1em;
            margin: 0 0 1.5em 0;
            color: #666;
        }}
        
        a {{
            color: #2e5aa8;
            text-decoration: underline;
        }}
        
        a:hover {{
            color: #1a4080;
        }}
        
        ::-webkit-scrollbar {{
            height: 12px;
        }}
        
        ::-webkit-scrollbar-track {{
            background: #f1f1f1;
        }}
        
        ::-webkit-scrollbar-thumb {{
            background: #888;
            border-radius: 6px;
        }}
        
        ::-webkit-scrollbar-thumb:hover {{
            background: #555;
        }}

        .navigation {{
            position: fixed;
            bottom: 20px;
            left: 50%;
            transform: translateX(-50%);
            display: flex;
            flex-direction: row;
            gap: 10px;
            z-index: 1000;
        }}

        .dot {{
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background-color: #ccc;
            cursor: pointer;
            transition: background-color 0.3s;
        }}

        .dot.active {{
            background-color: #333;
        }}

        .dot:hover {{
            background-color: #666;
        }}
    </style>
</head>
<body>
    <div class="container" id="container">
        <!-- 記事は動的に生成される -->
    </div>

    <div class="navigation" id="navigation">
{dots_html}    </div>

    <script>
        const contents = [
        {contents_array}
        ];

        function generateArticles() {{
            const container = document.getElementById('container');
            
            contents.forEach((article, index) => {{
                const contentDiv = document.createElement('div');
                contentDiv.className = 'content';
                contentDiv.innerHTML = `
                    <h2>${{article.date}}</h2>
                    ${{article.content}}
                `;
                container.appendChild(contentDiv);
            }});
        }}

        function updateActiveDot() {{
            const container = document.getElementById('container');
            const dots = document.querySelectorAll('.dot');
            const contents = document.querySelectorAll('.content');
            const scrollLeft = container.scrollLeft;
            const containerWidth = container.clientWidth;
            
            // 各記事の中央位置を計算して、最も近いものを選択
            let closestIndex = 0;
            let minDistance = Infinity;
            
            contents.forEach((content, index) => {{
                const contentRect = content.getBoundingClientRect();
                const containerRect = container.getBoundingClientRect();
                const contentCenter = contentRect.left + contentRect.width / 2;
                const containerCenter = containerRect.left + containerRect.width / 2;
                const distance = Math.abs(contentCenter - containerCenter);
                
                if (distance < minDistance) {{
                    minDistance = distance;
                    closestIndex = index;
                }}
            }});
            
            // ドットのアクティブ状態を更新
            dots.forEach((dot, dotIndex) => {{
                if (dotIndex === closestIndex) {{
                    dot.classList.add('active');
                }} else {{
                    dot.classList.remove('active');
                }}
            }});
        }}

        function scrollToArticle(index) {{
            const container = document.getElementById('container');
            const contents = document.querySelectorAll('.content');
            
            if (contents[index]) {{
                const targetContent = contents[index];
                const containerRect = container.getBoundingClientRect();
                const targetRect = targetContent.getBoundingClientRect();
                const scrollLeft = targetRect.left - containerRect.left + container.scrollLeft;
                
                container.scrollTo({{
                    left: scrollLeft,
                    behavior: 'smooth'
                }});
            }}
        }}

        // イベントリスナーの設定
        document.addEventListener('DOMContentLoaded', () => {{
            generateArticles();
            
            // 最右端（最新記事）にスクロール
            const container = document.getElementById('container');
            container.scrollTo({{
                left: container.scrollWidth,
                behavior: 'smooth'
            }});
            
            // ドットクリックイベント
            document.querySelectorAll('.dot').forEach((dot, index) => {{
                dot.addEventListener('click', () => {{
                    scrollToArticle(index);
                }});
            }});
            
            // スクロールイベント
            container.addEventListener('scroll', updateActiveDot);
            
            // 初期状態のドット更新
            setTimeout(() => {{
                updateActiveDot();
            }}, 100);
        }});
    </script>
</body>
</html>"""
    
    # index.htmlに書き出し
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print("Success: index.html を生成しました")

if __name__ == "__main__":
    main()