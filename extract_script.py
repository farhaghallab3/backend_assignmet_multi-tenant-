import zipfile
import xml.etree.ElementTree as ET
import sys

def extract_docx_text(docx_path):
    try:
        with zipfile.ZipFile(docx_path, 'r') as zip_ref:
            xml_content = zip_ref.read('word/document.xml')
            tree = ET.fromstring(xml_content)
            ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
            
            texts = []
            for node in tree.findall('.//w:t', ns):
                if node.text:
                    texts.append(node.text)
            
            print('\n'.join(texts))
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)

if __name__ == '__main__':
    docx = 'Backend_Python_Developer_Technical_Assignment_Edited.docx'
    extract_docx_text(docx)
