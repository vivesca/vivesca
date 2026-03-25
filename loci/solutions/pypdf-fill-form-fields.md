# Filling PDF Form Fields with pypdf

## Problem

Need to programmatically fill fillable PDF forms (e.g. ISACA Verification of Attendance forms).

## Solution

```python
from pypdf import PdfReader, PdfWriter

reader = PdfReader("template.pdf")
writer = PdfWriter()
writer.append(reader)

# Discover field names
fields = reader.get_form_text_fields()
print(fields)  # {'Name': None, 'Dates': None, ...}

# Fill fields
writer.update_page_form_field_values(writer.pages[0], {
    "Name": "Terry Li",
    "Dates": "2024-01-01",
})

with open("filled.pdf", "wb") as f:
    writer.write(f)
```

## Gotchas

- Field names don't always match labels. E.g. "Title of Program/Course Attended" → field name `"Title of programcourse attended"` (slashes and special chars stripped).
- Use `reader.get_form_text_fields()` to discover actual field names — don't guess from the visual layout.
- `pdftk` not installed on macOS by default; `pypdf` is pip-installable and sufficient for basic form filling.
- Signature fields must be left blank for wet signatures — pypdf can't insert image signatures.
