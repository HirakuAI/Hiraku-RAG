"""
test_processor.py
         _______                   _____                    _____                    _____          
        /::\    \                 /\    \                  /\    \                  /\    \         
       /::::\    \               /::\    \                /::\____\                /::\    \        
      /::::::\    \              \:::\    \              /::::|   |               /::::\    \       
     /::::::::\    \              \:::\    \            /:::::|   |              /::::::\    \      
    /:::/~~\:::\    \              \:::\    \          /::::::|   |             /:::/\:::\    \     
   /:::/    \:::\    \              \:::\    \        /:::/|::|   |            /:::/__\:::\    \    
  /:::/    / \:::\    \             /::::\    \      /:::/ |::|   |           /::::\   \:::\    \   
 /:::/____/   \:::\____\   ____    /::::::\    \    /:::/  |::|___|______    /::::::\   \:::\    \  
|:::|    |     |:::|    | /\   \  /:::/\:::\    \  /:::/   |::::::::\    \  /:::/\:::\   \:::\    \ 
|:::|____|     |:::|    |/::\   \/:::/  \:::\____\/:::/    |:::::::::\____\/:::/  \:::\   \:::\____\
 \:::\    \   /:::/    / \:::\  /:::/    \::/    /\::/    / ~~~~~/:::/    /\::/    \:::\  /:::/    /
  \:::\    \ /:::/    /   \:::\/:::/    / \/____/  \/____/      /:::/    /  \/____/ \:::\/:::/    / 
   \:::\    /:::/    /     \::::::/    /                       /:::/    /            \::::::/    /  
    \:::\__/:::/    /       \::::/____/                       /:::/    /              \::::/    /   
     \::::::::/    /         \:::\    \                      /:::/    /               /:::/    /    
      \::::::/    /           \:::\    \                    /:::/    /               /:::/    /     
       \::::/    /             \:::\    \                  /:::/    /               /:::/    /      
        \::/____/               \:::\____\                /:::/    /               /:::/    /       
         ~~                      \::/    /                \::/    /                \::/    /        
                                  \/____/                  \/____/                  \/____/         
                                                                                                    
Description: test for document processor
Auther: Yiyuan Li
Date: 13 Dec
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.document_processor import DocumentProcessor

def test_processor():
    processor = DocumentProcessor(num_workers=4)

    test_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "test")
    print(f"Processing directory: {test_dir}")

    results = processor.process_directory(test_dir, recursive=True)

    for doc in results:
        print("\n" + "="*50)
        print(f"File: {doc['metadata']['title']}")
        print(f"Type: {doc['metadata']['file_type']}")
        print("-"*50)
        print("Metadata:")
        for key, value in doc['metadata'].items():
            if key not in ['title', 'file_type']:
                print(f"  {key}: {value}")

        print("-"*50)
        print("Content Preview (first 1500 characters):")
        content_preview = doc['content'][:1500] + "..." if len(doc['content']) > 1500 else doc['content']
        print(content_preview)
        print("="*50 + "\n")

if __name__ == "__main__":
    test_processor()
