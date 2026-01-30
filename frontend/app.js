// RAG Document Manager Frontend

const API_BASE = '/api';

// DOM Elements
const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');
const uploadForm = document.getElementById('upload-form');
const uploadBtn = document.getElementById('upload-btn');
const hierarchicalSplit = document.getElementById('hierarchical-split');
const uploadStatus = document.getElementById('upload-status');
const documentsList = document.getElementById('documents-list');
const refreshBtn = document.getElementById('refresh-btn');
const detailSection = document.getElementById('detail-section');
const closeDetailBtn = document.getElementById('close-detail-btn');
const documentInfo = document.getElementById('document-info');
const chunksList = document.getElementById('chunks-list');
const searchForm = document.getElementById('search-form');
const searchQuery = document.getElementById('search-query');
const searchLimit = document.getElementById('search-limit');
const searchOffset = document.getElementById('search-offset');
const searchDocument = document.getElementById('search-document');
const searchStatus = document.getElementById('search-status');
const searchResults = document.getElementById('search-results');

let selectedFile = null;

// File Upload Handling
dropZone.addEventListener('click', () => fileInput.click());

dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('drag-over');
});

dropZone.addEventListener('dragleave', () => {
    dropZone.classList.remove('drag-over');
});

dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('drag-over');
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleFileSelect(files[0]);
    }
});

fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        handleFileSelect(e.target.files[0]);
    }
});

function handleFileSelect(file) {
    selectedFile = file;
    dropZone.classList.add('has-file');
    dropZone.querySelector('p').textContent = `Selected: ${file.name}`;
    uploadBtn.disabled = false;
}

uploadForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    if (!selectedFile) return;

    setUploadStatus('loading', 'Uploading and processing...');
    uploadBtn.disabled = true;

    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('hierarchical_split', hierarchicalSplit.checked);

    try {
        const response = await fetch(`${API_BASE}/upload`, {
            method: 'POST',
            body: formData,
        });

        const data = await response.json();

        if (response.ok) {
            setUploadStatus('success', `${data.message}`);
            resetUploadForm();
            loadDocuments();
        } else {
            setUploadStatus('error', `Error: ${data.detail || 'Upload failed'}`);
        }
    } catch (error) {
        setUploadStatus('error', `Error: ${error.message}`);
    }

    uploadBtn.disabled = false;
});

function setUploadStatus(type, message) {
    uploadStatus.className = `status ${type}`;
    uploadStatus.textContent = message;
}

function resetUploadForm() {
    selectedFile = null;
    fileInput.value = '';
    dropZone.classList.remove('has-file');
    dropZone.querySelector('p').textContent = 'Drag & drop a file here or click to select';
    uploadBtn.disabled = true;
}

// Documents List
async function loadDocuments() {
    documentsList.innerHTML = '<p class="loading">Loading documents...</p>';

    try {
        const response = await fetch(`${API_BASE}/documents`);
        const data = await response.json();

        if (data.documents.length === 0) {
            documentsList.innerHTML = '<p class="empty">No documents uploaded yet.</p>';
            return;
        }

        documentsList.innerHTML = data.documents.map(doc => `
            <div class="document-item" data-id="${doc.id}">
                <div class="document-info-brief">
                    <div class="document-name">${escapeHtml(doc.filename)}</div>
                    <div class="document-meta">
                        ${doc.chunk_count} chunks | ${formatDate(doc.created_at)}
                    </div>
                </div>
                <div class="document-actions">
                    <button onclick="viewDocument('${doc.id}')" class="secondary-btn">View</button>
                    <button onclick="deleteDocument('${doc.id}')" class="delete-btn">Delete</button>
                </div>
            </div>
        `).join('');
    } catch (error) {
        documentsList.innerHTML = `<p class="error">Error loading documents: ${error.message}</p>`;
    }
}

async function viewDocument(docId) {
    detailSection.style.display = 'block';
    documentInfo.innerHTML = '<p class="loading">Loading...</p>';
    chunksList.innerHTML = '';

    try {
        const response = await fetch(`${API_BASE}/documents/${docId}`);
        const data = await response.json();
        const doc = data.document;

        documentInfo.innerHTML = `
            <p><strong>Filename:</strong> ${escapeHtml(doc.filename)}</p>
            <p><strong>Type:</strong> ${doc.content_type || 'Unknown'}</p>
            <p><strong>Chunks:</strong> ${doc.chunk_count}</p>
            <p><strong>Uploaded:</strong> ${formatDate(doc.created_at)}</p>
            <p><strong>ID:</strong> <code>${doc.id}</code></p>
        `;

        chunksList.innerHTML = data.chunks.map((chunk, index) => `
            <div class="chunk-item">
                <div class="chunk-header">
                    <span class="chunk-index">Chunk #${chunk.chunk_index !== null ? chunk.chunk_index : index}</span>
                    <span class="chunk-path">${escapeHtml(chunk.section_path) || 'No section'}</span>
                </div>
                <div class="chunk-content">${escapeHtml(chunk.content)}</div>
            </div>
        `).join('');

        detailSection.scrollIntoView({ behavior: 'smooth' });
    } catch (error) {
        documentInfo.innerHTML = `<p class="error">Error loading document: ${error.message}</p>`;
    }
}

async function deleteDocument(docId) {
    if (!confirm('Are you sure you want to delete this document?')) return;

    try {
        const response = await fetch(`${API_BASE}/documents/${docId}`, {
            method: 'DELETE',
        });

        if (response.ok) {
            loadDocuments();
            if (detailSection.style.display !== 'none') {
                detailSection.style.display = 'none';
            }
        } else {
            const data = await response.json();
            alert(`Error: ${data.detail || 'Delete failed'}`);
        }
    } catch (error) {
        alert(`Error: ${error.message}`);
    }
}

// Utility Functions
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatDate(dateStr) {
    if (!dateStr) return 'Unknown';
    const date = new Date(dateStr);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
}

// Event Listeners
refreshBtn.addEventListener('click', loadDocuments);
closeDetailBtn.addEventListener('click', () => {
    detailSection.style.display = 'none';
});

// Search Handling
searchForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    const query = searchQuery.value.trim();
    if (!query) return;

    setSearchStatus('loading', 'Searching...');
    searchResults.innerHTML = '';

    const requestBody = {
        query: query,
        limit: parseInt(searchLimit.value) || 10,
        offset: parseInt(searchOffset.value) || 0,
    };

    // Add document filter if specified
    const docId = searchDocument.value.trim();
    if (docId) {
        requestBody.filter = { document_id: docId };
    }

    try {
        const response = await fetch(`${API_BASE}/search`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestBody),
        });

        const data = await response.json();

        if (response.ok) {
            if (data.results.length === 0) {
                setSearchStatus('success', 'No results found.');
                searchResults.innerHTML = '<p class="empty">No matching documents.</p>';
            } else {
                setSearchStatus('success', `Found ${data.total} result(s)`);
                displaySearchResults(data.results);
            }
        } else {
            setSearchStatus('error', `Error: ${data.detail || 'Search failed'}`);
        }
    } catch (error) {
        setSearchStatus('error', `Error: ${error.message}`);
    }
});

function setSearchStatus(type, message) {
    searchStatus.className = `status ${type}`;
    searchStatus.textContent = message;
}

function displaySearchResults(results) {
    searchResults.innerHTML = results.map((result, index) => `
        <div class="search-result-item">
            <div class="result-header">
                <span class="result-index">#${index + 1}</span>
                <span class="result-filename">${escapeHtml(result.document_filename)}</span>
                <span class="result-path">${escapeHtml(result.section_path) || 'No section'}</span>
            </div>
            <div class="result-content">${escapeHtml(result.content)}</div>
            <div class="result-meta">
                <span>Chunk: ${result.chunk_id}</span>
                <span>Doc ID: <code>${result.document_id}</code></span>
            </div>
        </div>
    `).join('');
}

// Initial Load
document.addEventListener('DOMContentLoaded', loadDocuments);
