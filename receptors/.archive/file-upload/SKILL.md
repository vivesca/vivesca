---
name: file-upload
description: Upload local files to websites via JavaScript DataTransfer API, bypassing native file picker.
user_invocable: false
---

# File Upload

Upload local files to websites without triggering native file picker dialogs. Uses JavaScript DataTransfer API to programmatically set files on input elements.

## Trigger

Use when:
- User says "upload [file] to this page", "attach my CV/resume", "upload file to this form"
- User needs to upload a file to a website via browser automation

## Inputs

- **file_path**: Local path to file (e.g., `/Users/terry/Documents/resume.pdf`)
- **target_element** (optional): Specific file input selector if multiple exist

## Workflow

1. **Get file path and target** — Ask user if not provided

2. **Get browser context**:
   - **OpenClaw:** `browser action=snapshot` to see current page
   - **Claude Code:** Use Chrome extension to get current tab

3. **Find file input elements**:
   - Look for `<input type="file">` elements in the page
   - Or upload buttons/dropzones

4. **Read and encode the local file**:
   ```bash
   FILE_PATH="/path/to/file.pdf"
   FILE_NAME=$(basename "$FILE_PATH")
   FILE_SIZE=$(stat -f%z "$FILE_PATH" 2>/dev/null || stat -c%s "$FILE_PATH")

   # Get MIME type
   case "${FILE_NAME##*.}" in
     pdf) MIME_TYPE="application/pdf" ;;
     doc) MIME_TYPE="application/msword" ;;
     docx) MIME_TYPE="application/vnd.openxmlformats-officedocument.wordprocessingml.document" ;;
     txt) MIME_TYPE="text/plain" ;;
     png) MIME_TYPE="image/png" ;;
     jpg|jpeg) MIME_TYPE="image/jpeg" ;;
     *) MIME_TYPE="application/octet-stream" ;;
   esac

   BASE64_CONTENT=$(base64 -i "$FILE_PATH")
   ```

5. **Inject file using JavaScript DataTransfer API**:
   ```javascript
   (async function() {
     const fileName = "FILENAME_HERE";
     const mimeType = "MIME_TYPE_HERE";
     const base64Content = "BASE64_CONTENT_HERE";

     const binaryString = atob(base64Content);
     const bytes = new Uint8Array(binaryString.length);
     for (let i = 0; i < binaryString.length; i++) {
       bytes[i] = binaryString.charCodeAt(i);
     }

     const file = new File([bytes], fileName, { type: mimeType });
     const dataTransfer = new DataTransfer();
     dataTransfer.items.add(file);

     const fileInput = document.querySelector('INPUT_SELECTOR_HERE');
     if (!fileInput) return "ERROR: No file input found";

     fileInput.files = dataTransfer.files;
     fileInput.dispatchEvent(new Event('change', { bubbles: true }));
     fileInput.dispatchEvent(new Event('input', { bubbles: true }));

     return `SUCCESS: Uploaded "${fileName}" (${file.size} bytes)`;
   })();
   ```

6. **Verify upload** — Take screenshot to confirm file was attached

7. **Report result** to user

## Error Handling

- **If multiple file inputs**: Ask user which one to use
- **If no file input found**: Check for drag-drop zones, dispatch drag events instead
- **If file exceeds site limit**: Warn user before attempting
- **If file type not accepted**: Check input's `accept` attribute, warn if mismatch
- **If site rejects upload**: Report failure, suggest manual upload

## Output

- Success message with filename and size
- Screenshot showing file attached
- Next steps (e.g., "Click Submit to complete")

## Common File Paths

- CV: Search for latest `Terry_Li_CV*.pdf` (location may change — check iCloud Drive, Downloads, or Desktop)
- Notes: `/Users/terry/notes/`

## Limitations

- Cannot upload to sites requiring server-side validation before accepting
- Some sites detect programmatic uploads and reject them
- Very large files (>50MB) may cause browser memory issues
- Complex upload widgets (Dropbox Chooser) may not work
