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


## Project TODO List

### Core Features (Priority)
- [ ] Implement Multi-Model Support **(WIP)**
  - ~~Add Ollama integration (default local server)~~
  - Add OpenAI API integration
  - Add Claude API integration
  - Create model configuration UI
  - Allow users to use custom API keys/servers
  - Implement model fallback logic
  - Add model switching interface
  - If the user's question is not in the files, inform the user and provide an answer based on the model's training data or online resources.

- [ ] Add Internet Search Integration
  - Add real-time web search capability
  - Merge web results with file-based answers
  - Add search provider configuration
  - Implement search result caching
  - Add source citations for web results

- [ ] Implement Multi-User System
  - Add user authentication
  - Create isolated user workspaces
  - Setup secure API key storage
  - Add user preferences
  - Implement workspace sharing

- [ ] Enhance Document Processing
  - Using LamaParse/LamaIndex for document processing
  - Add support for tables
  - Add support for images
  - Implement better PDF parsing
  - Add batch processing
  - Improve metadata extraction
  - Add document versioning

### User Interface
- [ ] Add File Management Features
  - File upload progress
  - File list/grid view
  - Delete/update documents
  - Folder organization
  - Tag/label system
  - Search functionality

- [ ] Improve Chat Interface
  - Add loading states
  - Better error messages
  - Source citations display
  - Conversation history
  - Context management
  - Message threading

- [ ] Add Settings Interface
  - Model provider selection
  - API key management
  - User preferences
  - Theme customization
  - Language settings
  - Export/import settings

### Security & Privacy
- [ ] Implement Security Features
  - User authentication system
  - API key encryption
  - Rate limiting
  - Input validation
  - File scanning
  - Access logging

- [ ] Add Privacy Controls
  - Data retention settings
  - Workspace isolation
  - Usage analytics opt-out
  - Data export
  - Account deletion

### Testing & Documentation
- [ ] Add Comprehensive Testing
  - Unit tests for core functions
  - Integration tests for API
  - Frontend component tests
  - Security testing
  - Performance testing
  - Load testing

- [ ] Complete Documentation
  - Setup guide
  - API documentation
  - User manual
  - Developer guide
  - Security guidelines
  - Contribution guidelines

### Performance Optimization
- [ ] Optimize System Performance
  - Implement caching
  - Add request queuing
  - Optimize database queries
  - Improve search speed
  - Reduce memory usage
  - Add performance monitoring

### Deployment
- [ ] Setup Deployment Pipeline
  - Docker containerization
  - CI/CD setup
  - Environment configuration
  - Backup systems
  - Monitoring setup
  - Error tracking

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
ollama pull llama3.2
```

3. Clone the repository:
```bash
git clone https://github.com/yuann3/FYP-Prototype.git
cd FYP-Prototype
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
