# OiMA - Oii my asshole (prototype name)
```


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
                                                                                                    
```
OiMA - Oii my asshole (prototype name)

i hate to write readme and im an asshole so i just throw my code and requirement to gpt and it give me this shit below

but it works and useful so what can i say.....

-- YY

## Current Status

### Implemented Features
- Document processing pipeline using LlamaIndex
- Support for multiple file formats
- Metadata extraction
- Document chunking
- Custom JSON document handling
- Basic error handling and logging
- Test framework for document processing

### TODO

#### High Priority
- [ ] Implement Llama 2 integration via Ollama
- [ ] Create vector storage for document embeddings
- [ ] Develop query processing pipeline
- [ ] Add document retrieval mechanism
- [ ] Create simple CLI interface

#### Medium Priority
- [ ] Enhance error handling for specific file types
- [ ] Add document preprocessing filters
- [ ] Implement caching mechanism
- [ ] Add support for concurrent processing
- [ ] Create basic monitoring and logging dashboard

#### Low Priority
- [ ] Optimize chunking parameters
- [ ] Add support for more file formats
- [ ] Implement document update mechanism
- [ ] Add basic security features
- [ ] Create user authentication system

## Prerequisites

- Python 3.8+
- Ollama (installed)
- Linux/MacOS X

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd <repository-name>
```

2. Run the script to create/start virtual environment:
```bash
chmod +x start_env.sh
./start_env.sh
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Project Structure

```
.
├── src/
│   ├── document_processor.py   # Main document processing logic
│   └── ...                    # Future modules
├── tests/
│   ├── test_processor.py      # Test cases
│   └── ...                    # Future tests
├── data/
│   └── test/                  # Test data directory
└── requirements.txt           # Project dependencies
```

## Usage

Currently, you can test the document processor:

```python
from src.document_processor import DocumentProcessor

processor = DocumentProcessor()
results = processor.process_directory("path/to/your/documents")
```

## Technical Notes

### Document Processing
- Uses LlamaIndex's `SimpleDirectoryReader` for base functionality
- Implements custom JSON handling via CustomJSONReader
- Chunks documents using SimpleNodeParser (1024 tokens with 200 token overlap)

### Supported File Formats
- Text files (.txt)
- PDFs (.pdf)
- CSVs (.csv)
- Microsoft Office files (.docx, .doc, .pptx, .ppt)
- Images (.jpg, .jpeg, .png)
- Markdown (.md, .markdown)
- JSON (.json)
- EPub (.epub)

## Performance Notes

- Parallel processing supported via num_workers parameter
- Default chunk size optimized for most use cases
- Memory usage scales with document size and number

## Roadmap

### Phase 1: Core RAG Implementation
- Integrate Llama 2 model
- Implement basic query processing
- Add vector storage
