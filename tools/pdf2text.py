#!/usr/bin/env python3
"""
PDF to Text — AI From Zero Skill
用法: python3 pdf2text.py <PDF文件路径>

从PDF中提取文字并输出到终端。
支持从Windows路径（C:\\...）和WSL路径（/mnt/c/...）读取。
"""

import sys
import os
import re

def extract_text(pdf_path):
    """从PDF提取文字"""
    import pdfplumber
    
    # 如果是Windows路径，转换为WSL路径
    if re.match(r'^[A-Za-z]:\\', pdf_path):
        drive = pdf_path[0].lower()
        wsl_path = '/mnt/' + drive + pdf_path[2:].replace('\\', '/')
        pdf_path = wsl_path
    
    if not os.path.exists(pdf_path):
        return f"❌ 文件不存在: {pdf_path}"
    
    text_parts = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)
            for i, page in enumerate(pdf.pages, 1):
                page_text = page.extract_text() or ""
                tables = page.extract_tables()
                
                if page_text.strip():
                    text_parts.append(f"--- 第{i}页 ---\n{page_text}")
                
                # 提取表格
                for table in tables:
                    for row in table:
                        row_text = " | ".join([str(c or "") for c in row])
                        if row_text.strip():
                            text_parts.append(row_text)
        
        result = "\n\n".join(text_parts)
        return result
    
    except Exception as e:
        return f"❌ PDF读取失败: {e}"


def main():
    if len(sys.argv) < 2:
        print("用法: python3 pdf2text.py <PDF文件路径>")
        print("示例: python3 pdf2text.py C:\\Users\\lenovo\\Desktop\\paper.pdf")
        print("示例: python3 pdf2text.py /mnt/c/Users/lenovo/Desktop/paper.pdf")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    result = extract_text(pdf_path)
    
    # 统计信息
    lines = result.split('\n')
    chars = len(result)
    
    print("=" * 60)
    print(f"📄 PDF文字提取结果")
    print(f"📊 共 {chars} 字符, {len(lines)} 行")
    print("=" * 60)
    print()
    print(result)
    print()
    print("=" * 60)
    print("✅ 提取完成，可以直接复制上面的文字")


if __name__ == "__main__":
    main()
