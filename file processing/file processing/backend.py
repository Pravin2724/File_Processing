from flask import Flask, request, jsonify, send_file, render_template_string
import pyodbc
import io

app = Flask(__name__)

# ✅ Update your connection string here
CONN_STR = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=localhost;"          # or your server name e.g. DESKTOP-XXXX\SQLEXPRESS
    "DATABASE=AadhaarDB;"
    "Trusted_Connection=yes;"   # Windows Auth — remove if using SQL login
    # "UID=your_username;"      # Uncomment for SQL login
    # "PWD=your_password;"      # Uncomment for SQL login
)

def get_conn():
    return pyodbc.connect(CONN_STR)


HTML_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Aadhaar File Vault</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;700;800&family=DM+Sans:wght@300;400;500&display=swap');

  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  :root {
    --bg: #0d0f14;
    --card: #161a23;
    --border: #2a2f3d;
    --accent: #4f8ef7;
    --accent2: #a78bfa;
    --text: #e8eaf0;
    --muted: #6b7280;
    --success: #34d399;
    --error: #f87171;
  }

  body {
    background: var(--bg);
    color: var(--text);
    font-family: 'DM Sans', sans-serif;
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 2rem;
  }

  .container {
    width: 100%;
    max-width: 560px;
  }

  h1 {
    font-family: 'Syne', sans-serif;
    font-weight: 800;
    font-size: 2rem;
    letter-spacing: -0.03em;
    background: linear-gradient(135deg, var(--accent), var(--accent2));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0.25rem;
  }

  .subtitle {
    color: var(--muted);
    font-size: 0.9rem;
    margin-bottom: 2.5rem;
  }

  .card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 1.75rem;
    margin-bottom: 1.25rem;
  }

  .card h2 {
    font-family: 'Syne', sans-serif;
    font-size: 0.75rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: var(--accent);
    margin-bottom: 1.25rem;
  }

  label {
    display: block;
    font-size: 0.8rem;
    font-weight: 500;
    color: var(--muted);
    margin-bottom: 0.4rem;
    margin-top: 1rem;
  }
  label:first-of-type { margin-top: 0; }

  input[type="text"], input[type="file"] {
    width: 100%;
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 0.65rem 0.9rem;
    color: var(--text);
    font-family: 'DM Sans', sans-serif;
    font-size: 0.95rem;
    outline: none;
    transition: border-color 0.2s;
  }

  input[type="text"]:focus, input[type="file"]:focus {
    border-color: var(--accent);
  }

  input[type="file"] {
    padding: 0.5rem;
    cursor: pointer;
  }

  button {
    margin-top: 1.25rem;
    width: 100%;
    padding: 0.75rem;
    border: none;
    border-radius: 8px;
    font-family: 'Syne', sans-serif;
    font-weight: 700;
    font-size: 0.9rem;
    letter-spacing: 0.03em;
    cursor: pointer;
    transition: opacity 0.2s, transform 0.1s;
  }
  button:hover { opacity: 0.88; }
  button:active { transform: scale(0.98); }

  .btn-upload { background: linear-gradient(135deg, var(--accent), #3b6fd4); color: #fff; }
  .btn-fetch  { background: linear-gradient(135deg, var(--accent2), #7c3aed); color: #fff; }

  .msg {
    margin-top: 1rem;
    font-size: 0.85rem;
    padding: 0.6rem 0.9rem;
    border-radius: 7px;
    display: none;
  }
  .msg.success { background: #0d2e23; color: var(--success); border: 1px solid #1a4a38; display: block; }
  .msg.error   { background: #2e1515; color: var(--error);   border: 1px solid #4a2020; display: block; }

  #fileResult {
    margin-top: 1.25rem;
    display: none;
  }
  #fileResult iframe {
    width: 100%;
    height: 420px;
    border: 1px solid var(--border);
    border-radius: 8px;
    background: #fff;
  }
  #fileResult .download-link {
    display: inline-block;
    margin-top: 0.75rem;
    font-size: 0.85rem;
    color: var(--accent);
    text-decoration: none;
  }
  #fileResult .download-link:hover { text-decoration: underline; }
</style>
</head>
<body>
<div class="container">
  <h1>Aadhaar Vault</h1>
  <p class="subtitle">Securely upload &amp; retrieve files by Aadhaar number</p>

  <!-- UPLOAD CARD -->
  <div class="card">
    <h2>📤 Upload File</h2>
    <label>Aadhaar Number</label>
    <input type="text" id="uploadAadhaar" maxlength="12" placeholder="12-digit Aadhaar number">
    <label>Select File</label>
    <input type="file" id="uploadFile">
    <button class="btn-upload" onclick="uploadFile()">Upload &amp; Store</button>
    <div id="uploadMsg" class="msg"></div>
  </div>

  <!-- FETCH CARD -->
  <div class="card">
    <h2>🔍 Fetch File</h2>
    <label>Aadhaar Number</label>
    <input type="text" id="fetchAadhaar" maxlength="12" placeholder="12-digit Aadhaar number">
    <button class="btn-fetch" onclick="fetchFile()">Fetch &amp; Display</button>
    <div id="fetchMsg" class="msg"></div>

    <div id="fileResult">
      <iframe id="fileFrame" src=""></iframe><br>
      <a id="downloadLink" class="download-link" href="#" download>⬇ Download file</a>
    </div>
  </div>
</div>

<script>
  async function uploadFile() {
    const aadhaar = document.getElementById('uploadAadhaar').value.trim();
    const file    = document.getElementById('uploadFile').files[0];
    const msgEl   = document.getElementById('uploadMsg');

    msgEl.className = 'msg';
    msgEl.textContent = '';

    if (!/^\\d{12}$/.test(aadhaar)) {
      msgEl.className = 'msg error';
      msgEl.textContent = 'Please enter a valid 12-digit Aadhaar number.';
      return;
    }
    if (!file) {
      msgEl.className = 'msg error';
      msgEl.textContent = 'Please select a file to upload.';
      return;
    }

    const formData = new FormData();
    formData.append('aadhaar_number', aadhaar);
    formData.append('file', file);

    try {
      const res  = await fetch('/upload', { method: 'POST', body: formData });
      const data = await res.json();
      if (res.ok) {
        msgEl.className = 'msg success';
        msgEl.textContent = '✅ ' + data.message;
      } else {
        msgEl.className = 'msg error';
        msgEl.textContent = '❌ ' + data.error;
      }
    } catch (e) {
      msgEl.className = 'msg error';
      msgEl.textContent = '❌ Network error. Is Flask running?';
    }
  }

  async function fetchFile() {
    const aadhaar  = document.getElementById('fetchAadhaar').value.trim();
    const msgEl    = document.getElementById('fetchMsg');
    const resultEl = document.getElementById('fileResult');

    msgEl.className = 'msg';
    msgEl.textContent = '';
    resultEl.style.display = 'none';

    if (!/^\\d{12}$/.test(aadhaar)) {
      msgEl.className = 'msg error';
      msgEl.textContent = 'Please enter a valid 12-digit Aadhaar number.';
      return;
    }

    try {
      const res = await fetch('/fetch/' + aadhaar);
      if (!res.ok) {
        const data = await res.json();
        msgEl.className = 'msg error';
        msgEl.textContent = '❌ ' + data.error;
        return;
      }

      const blob        = await res.blob();
      const url         = URL.createObjectURL(blob);
      const filename    = res.headers.get('X-Filename') || 'file';

      document.getElementById('fileFrame').src    = url;
      document.getElementById('downloadLink').href = url;
      document.getElementById('downloadLink').download = filename;

      resultEl.style.display = 'block';
      msgEl.className = 'msg success';
      msgEl.textContent = '✅ File found: ' + filename;
    } catch (e) {
      msgEl.className = 'msg error';
      msgEl.textContent = '❌ Network error. Is Flask running?';
    }
  }
</script>
</body>
</html>
"""


@app.route("/")
def index():
    return render_template_string(HTML_PAGE)


@app.route("/upload", methods=["POST"])
def upload():
    aadhaar = request.form.get("aadhaar_number", "").strip()
    file    = request.files.get("file")

    if not aadhaar or len(aadhaar) != 12 or not aadhaar.isdigit():
        return jsonify({"error": "Invalid Aadhaar number (must be 12 digits)."}), 400
    if not file or file.filename == "":
        return jsonify({"error": "No file provided."}), 400

    filename  = file.filename
    file_data = file.read()

    try:
        conn   = get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO AadhaarFiles (aadhaar_number, filename, file_data) VALUES (?, ?, ?)",
            aadhaar, filename, pyodbc.Binary(file_data)
        )
        conn.commit()
        conn.close()
        return jsonify({"message": f"File '{filename}' uploaded successfully."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/fetch/<aadhaar>", methods=["GET"])
def fetch(aadhaar):
    if len(aadhaar) != 12 or not aadhaar.isdigit():
        return jsonify({"error": "Invalid Aadhaar number."}), 400

    try:
        conn   = get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT TOP 1 filename, file_data FROM AadhaarFiles WHERE aadhaar_number = ? ORDER BY uploaded_at DESC",
            aadhaar
        )
        row = cursor.fetchone()
        conn.close()

        if not row:
            return jsonify({"error": "No file found for this Aadhaar number."}), 404

        filename, file_data = row
        return send_file(
            io.BytesIO(file_data),
            download_name=filename,
            as_attachment=False,
            mimetype="application/octet-stream"
        ), 200, {"X-Filename": filename}

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
