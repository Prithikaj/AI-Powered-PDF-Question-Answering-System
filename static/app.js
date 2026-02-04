document.getElementById('uploadForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  const fileInput = e.target.elements['file'];
  if (!fileInput.files.length) return alert('Select a PDF');
  const fd = new FormData();
  fd.append('file', fileInput.files[0]);
  const res = await fetch('/upload', { method: 'POST', body: fd });
  const j = await res.json();
  if (j.error) {
    document.getElementById('uploadResult').innerText = 'Upload error: ' + j.error;
  } else {
    document.getElementById('uploadResult').innerText = 'Uploaded: ' + j.filename + ' (doc_id=' + j.doc_id + ')';
    document.getElementById('docId').value = j.doc_id;
  }
});

document.getElementById('askForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  const docId = document.getElementById('docId').value;
  const question = document.getElementById('question').value;
  if (!docId) return alert('Enter document id');
  if (!question) return alert('Enter question');
  const fd = new FormData();
  fd.append('doc_id', docId);
  fd.append('question', question);
  const chat = document.getElementById('chat');
  chat.innerHTML += '<div><strong>You:</strong> ' + question + '</div>';
  const res = await fetch('/ask', { method: 'POST', body: fd });
  const j = await res.json();
  if (j.response) {
    chat.innerHTML += '<div><strong>Assistant:</strong><pre>' + escapeHtml(j.response) + '</pre></div>';
  } else if (j.error) {
    chat.innerHTML += '<div><strong>Error:</strong>' + j.error + '</div>';
  }
  chat.scrollTop = chat.scrollHeight;
});

function escapeHtml(str) {
  if (!str) return '';
  return str.replace(/[&<>"]+/g, function (s) {
    return ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[s];
  });
}
