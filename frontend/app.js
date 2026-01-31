// Straight Retrieve Frontend

const API_BASE = '/api';
const CHUNKS_PER_PAGE = 25;

// DOM Elements
const tabs = document.querySelectorAll('.tab');
const tabContents = document.querySelectorAll('.tab-content');
const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');
const uploadForm = document.getElementById('upload-form');
const uploadBtn = document.getElementById('upload-btn');
const hierarchicalSplit = document.getElementById('hierarchical-split');
const uploadStatus = document.getElementById('upload-status');
const documentsCount = document.getElementById('documents-count');
const documentsList = document.getElementById('documents-list');
const refreshBtn = document.getElementById('refresh-btn');
const detailModal = document.getElementById('detail-modal');
const modalTitle = document.getElementById('modal-title');
const closeModalBtn = document.getElementById('close-modal-btn');
const documentInfo = document.getElementById('document-info');
const chunksList = document.getElementById('chunks-list');
const chunksPagination = document.getElementById('chunks-pagination');
const searchForm = document.getElementById('search-form');
const searchQuery = document.getElementById('search-query');
const searchLimit = document.getElementById('search-limit');
const searchOffset = document.getElementById('search-offset');
const searchDocument = document.getElementById('search-document');
const searchStatus = document.getElementById('search-status');
const searchResults = document.getElementById('search-results');
const documentsSearch = document.getElementById('documents-search');
const documentsPagination = document.getElementById('documents-pagination');

let selectedFiles = [];
let currentChunks = [];
let currentChunkPage = 0;

// Documents pagination state
const DOCS_PER_PAGE = 10;
let documentsPage = 0;
let documentsTotal = 0;
let documentsSearchTerm = '';

// Tab Handling
tabs.forEach(tab => {
    tab.addEventListener('click', () => {
        const tabId = tab.dataset.tab;

        tabs.forEach(t => t.classList.remove('active'));
        tabContents.forEach(c => c.classList.remove('active'));

        tab.classList.add('active');
        document.getElementById(`tab-${tabId}`).classList.add('active');

        if (tabId === 'documents') {
            loadDocuments();
        }
    });
});

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
    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
        handleFileSelect(files);
    }
});

fileInput.addEventListener('change', (e) => {
    const files = Array.from(e.target.files);
    if (files.length > 0) {
        handleFileSelect(files);
    }
});

function handleFileSelect(files) {
    selectedFiles = files;
    dropZone.classList.add('has-file');
    if (files.length === 1) {
        dropZone.querySelector('p').textContent = `Selected: ${files[0].name}`;
    } else {
        dropZone.querySelector('p').textContent = `Selected: ${files.length} files`;
    }
    uploadBtn.disabled = false;
}

uploadForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    if (selectedFiles.length === 0) return;

    uploadBtn.disabled = true;
    const totalFiles = selectedFiles.length;
    let successCount = 0;
    let errorCount = 0;

    for (let i = 0; i < selectedFiles.length; i++) {
        const file = selectedFiles[i];
        setUploadStatus('loading', `Processing ${i + 1}/${totalFiles}: ${file.name}...`);

        const formData = new FormData();
        formData.append('file', file);
        formData.append('hierarchical_split', hierarchicalSplit.checked);

        try {
            const response = await fetch(`${API_BASE}/upload`, {
                method: 'POST',
                body: formData,
            });

            const data = await response.json();

            if (response.ok) {
                successCount++;
            } else {
                errorCount++;
                console.error(`Error uploading ${file.name}:`, data.detail);
            }
        } catch (error) {
            errorCount++;
            console.error(`Error uploading ${file.name}:`, error.message);
        }
    }

    if (errorCount === 0) {
        setUploadStatus('success', `Uploaded ${successCount} file(s) successfully`);
    } else if (successCount === 0) {
        setUploadStatus('error', `Failed to upload all ${errorCount} file(s)`);
    } else {
        setUploadStatus('loading', `Uploaded ${successCount}, failed ${errorCount}`);
    }

    resetUploadForm();
    uploadBtn.disabled = false;
});

function setUploadStatus(type, message) {
    uploadStatus.className = `status ${type}`;
    uploadStatus.textContent = message;
}

function resetUploadForm() {
    selectedFiles = [];
    fileInput.value = '';
    dropZone.classList.remove('has-file');
    dropZone.querySelector('p').textContent = 'Drag & drop files here or click to select';
    uploadBtn.disabled = true;
}

// Documents List
async function loadDocuments(resetPage = false) {
    if (resetPage) {
        documentsPage = 0;
    }

    documentsList.innerHTML = '<p class="loading">Loading...</p>';
    documentsPagination.innerHTML = '';
    documentsCount.textContent = '';

    const skip = documentsPage * DOCS_PER_PAGE;
    const params = new URLSearchParams({
        skip: skip,
        limit: DOCS_PER_PAGE,
    });
    if (documentsSearchTerm) {
        params.append('search', documentsSearchTerm);
    }

    try {
        const response = await fetch(`${API_BASE}/documents?${params}`);
        const data = await response.json();

        documentsTotal = data.total;

        if (data.total === 0) {
            documentsList.innerHTML = documentsSearchTerm
                ? '<p class="empty">No documents match your search.</p>'
                : '<p class="empty">No documents uploaded yet.</p>';
            documentsCount.textContent = '0 documents';
            return;
        }

        const start = skip + 1;
        const end = Math.min(skip + data.documents.length, data.total);
        documentsCount.textContent = `${start}-${end} of ${data.total}`;

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

        renderDocumentsPagination();
    } catch (error) {
        documentsList.innerHTML = `<p class="error">Error: ${error.message}</p>`;
    }
}

function renderDocumentsPagination() {
    const totalPages = Math.ceil(documentsTotal / DOCS_PER_PAGE);

    if (totalPages <= 1) {
        documentsPagination.innerHTML = '';
        return;
    }

    let html = '';
    html += `<button class="pagination-btn" onclick="goToDocumentsPage(${documentsPage - 1})" ${documentsPage === 0 ? 'disabled' : ''}>&lt;</button>`;

    for (let i = 0; i < totalPages; i++) {
        if (i === 0 || i === totalPages - 1 || (i >= documentsPage - 2 && i <= documentsPage + 2)) {
            html += `<button class="pagination-btn ${i === documentsPage ? 'active' : ''}" onclick="goToDocumentsPage(${i})">${i + 1}</button>`;
        } else if (i === documentsPage - 3 || i === documentsPage + 3) {
            html += '<span class="pagination-ellipsis">...</span>';
        }
    }

    html += `<button class="pagination-btn" onclick="goToDocumentsPage(${documentsPage + 1})" ${documentsPage === totalPages - 1 ? 'disabled' : ''}>&gt;</button>`;
    documentsPagination.innerHTML = html;
}

function goToDocumentsPage(page) {
    const totalPages = Math.ceil(documentsTotal / DOCS_PER_PAGE);
    if (page < 0 || page >= totalPages) return;

    documentsPage = page;
    loadDocuments();
}

async function viewDocument(docId) {
    detailModal.classList.add('active');
    documentInfo.innerHTML = '<p class="loading">Loading...</p>';
    chunksList.innerHTML = '';
    chunksPagination.innerHTML = '';

    try {
        const response = await fetch(`${API_BASE}/documents/${docId}`);
        const data = await response.json();
        const doc = data.document;

        modalTitle.textContent = doc.filename;
        documentInfo.innerHTML = `
            <p><strong>Type:</strong> ${doc.content_type || 'Unknown'}</p>
            <p><strong>Chunks:</strong> ${doc.chunk_count}</p>
            <p><strong>Uploaded:</strong> ${formatDate(doc.created_at)}</p>
            <p><strong>ID:</strong> <code>${doc.id}</code></p>
        `;

        currentChunks = data.chunks;
        currentChunkPage = 0;
        renderChunksPage();
        renderChunksPagination();
    } catch (error) {
        documentInfo.innerHTML = `<p class="error">Error: ${error.message}</p>`;
    }
}

function closeModal() {
    detailModal.classList.remove('active');
}

closeModalBtn.addEventListener('click', closeModal);
detailModal.addEventListener('click', (e) => {
    if (e.target === detailModal) {
        closeModal();
    }
});

function renderChunksPage() {
    const start = currentChunkPage * CHUNKS_PER_PAGE;
    const end = start + CHUNKS_PER_PAGE;
    const pageChunks = currentChunks.slice(start, end);

    chunksList.innerHTML = pageChunks.map((chunk, index) => `
        <div class="chunk-item">
            <div class="chunk-header">
                <span class="chunk-index">Chunk #${chunk.chunk_index !== null ? chunk.chunk_index : start + index}</span>
                <span class="chunk-path">${escapeHtml(chunk.section_path) || 'No section'}</span>
            </div>
            <div class="chunk-content">${escapeHtml(chunk.content)}</div>
        </div>
    `).join('');
}

function renderChunksPagination() {
    const totalPages = Math.ceil(currentChunks.length / CHUNKS_PER_PAGE);

    if (totalPages <= 1) {
        chunksPagination.innerHTML = '';
        return;
    }

    let paginationHtml = '<div class="pagination">';
    paginationHtml += `<button class="pagination-btn" onclick="goToChunkPage(${currentChunkPage - 1})" ${currentChunkPage === 0 ? 'disabled' : ''}>&lt;</button>`;

    for (let i = 0; i < totalPages; i++) {
        if (i === 0 || i === totalPages - 1 || (i >= currentChunkPage - 2 && i <= currentChunkPage + 2)) {
            paginationHtml += `<button class="pagination-btn ${i === currentChunkPage ? 'active' : ''}" onclick="goToChunkPage(${i})">${i + 1}</button>`;
        } else if (i === currentChunkPage - 3 || i === currentChunkPage + 3) {
            paginationHtml += '<span class="pagination-ellipsis">...</span>';
        }
    }

    paginationHtml += `<button class="pagination-btn" onclick="goToChunkPage(${currentChunkPage + 1})" ${currentChunkPage === totalPages - 1 ? 'disabled' : ''}>&gt;</button>`;
    paginationHtml += '</div>';
    chunksPagination.innerHTML = paginationHtml;
}

function goToChunkPage(page) {
    const totalPages = Math.ceil(currentChunks.length / CHUNKS_PER_PAGE);
    if (page < 0 || page >= totalPages) return;

    currentChunkPage = page;
    renderChunksPage();
    renderChunksPagination();
}

async function deleteDocument(docId) {
    if (!confirm('Delete this document?')) return;

    try {
        const response = await fetch(`${API_BASE}/documents/${docId}`, {
            method: 'DELETE',
        });

        if (response.ok) {
            loadDocuments();
            closeModal();
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
refreshBtn.addEventListener('click', () => loadDocuments(true));

// Documents search with debounce
let searchTimeout = null;
documentsSearch.addEventListener('input', (e) => {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
        documentsSearchTerm = e.target.value.trim();
        loadDocuments(true);
    }, 300);
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
                <span class="result-path">${escapeHtml(result.section_path) || ''}</span>
            </div>
            <div class="result-content">${escapeHtml(result.content)}</div>
            <div class="result-meta">
                <span>Chunk: ${result.chunk_id}</span>
                <span>Doc: <code>${result.document_id}</code></span>
            </div>
        </div>
    `).join('');
}

// Keyboard shortcuts
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        closeModal();
    }
});

// Initial Load
document.addEventListener('DOMContentLoaded', () => {
    // Documents will load when tab is clicked
});
