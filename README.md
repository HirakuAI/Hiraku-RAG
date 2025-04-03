# Hiraku (ヒラク)

```
██╗  ██╗██╗██████╗  █████╗ ██╗  ██╗██╗   ██╗    
██║  ██║██║██╔══██╗██╔══██╗██║ ██╔╝██║   ██║    
███████║██║██████╔╝███████║█████╔╝ ██║   ██║    
██╔══██║██║██╔══██╗██╔══██║██╔═██╗ ██║   ██║    
██║  ██║██║██║  ██║██║  ██║██║  ██╗╚██████╔╝    
╚═╝  ╚═╝╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝     
```


Hiraku is an advanced RAG (Retrieval-Augmented Generation) system that combines document processing, vector storage, and LLM capabilities to provide intelligent document analysis and question answering.

## Features

### Core Capabilities
- Advanced document processing pipeline using LlamaIndex
- Multi-format support (PDF, TXT, CSV, DOCX, etc.)
- Intelligent document chunking and metadata extraction
- Vector-based similarity search
- Integration with Llama 2 via Ollama
- Real-time query processing
- Source attribution for answers

### Technical Features
- ChromaDB vector storage
- GPU-accelerated embeddings
- Concurrent document processing
- Custom JSON document handling
- Comprehensive error handling and logging
- SQLite metadata storage

## Prerequisites

- Python 3.8+
- Ollama (installed and running)
- Linux/MacOS X
- CUDA-compatible GPU (optional, for acceleration)

## Installation

1. Install Ollama:
```bash
curl https://ollama.ai/install.sh | sh
```

2. Pull the Llama 3.2 model:
```bash
ollama pull llama3.2 # main model
ollama pull nomic-embed-text # embedding model
```

3. Clone the repository:
```bash
git clone https://github.com/HirakuAI/Hiraku-RAG.git
cd Hiraku-RAG
```

4. Create and activate virtual environment:
```bash
chmod +x start_env.sh
source ./start_env.sh
```

5. Install dependencies:
```bash
pip install -r requirements.txt
```

5. Run the application
make sure ollama is running
```bash
ollama serve
```

run the script
```bash
chmod +x run
./run
```

## Project Structure

```
.
├── src/
│   ├── app.py              # Flask API server
│   ├── rag_system.py       # Core RAG implementation
│   ├── document_processor.py # Document processing logic
│   └── ollama_client.py    # Ollama API client
├── frontend/              # React frontend
├── tests/                # Test cases
├── data/                 # Sample data and tests
└── private/             # Runtime data (ignored by git)
    ├── uploads/         # Uploaded documents
    ├── vectordb/       # ChromaDB storage
    └── rag.db          # SQLite metadata
```

## API Endpoints

### Query Endpoint
- **POST** `/api/query`
- Accepts JSON with `question` field
- Returns answer and sources

### Upload Endpoint
- **POST** `/api/upload`
- Accepts multipart form data with `file` field
- Supports multiple document formats

## Development

### Frontend Development
```bash
cd frontend
npm install
npm start
```

### Backend Development
```bash
python src/app.py
```

## Supported File Formats

- Text files (.txt)
- PDFs (.pdf)
- CSVs (.csv)
- Microsoft Office (.docx, .doc, .pptx)
- Images (.jpg, .jpeg, .png)
- Markdown (.md)
- JSON (.json)
- EPub (.epub)

## Performance Notes

- Parallel document processing with configurable workers
- Optimized chunk size (1024 tokens, 200 token overlap)
- GPU acceleration for embeddings when available
- Persistent vector storage with ChromaDB
- Efficient metadata management via SQLite

## Security Considerations

- Local-only Ollama API access
- Secure file upload handling
- Input sanitization
- Private storage for sensitive data
- No external API dependencies
