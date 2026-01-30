# Docsend to PDF

A Chrome extension that downloads Docsend presentations as PDF files.

## Features

- One-click download of Docsend presentations
- Preserves original slide quality
- Works with public and email-gated presentations (after entering email)
- Progress indicator during download

## Local Development / Testing

1. Open Chrome and navigate to `chrome://extensions/`
2. Enable "Developer mode" (toggle in top-right corner)
3. Click "Load unpacked"
4. Select the `docsend-pdf-extension` folder
5. Navigate to any Docsend presentation (e.g., `docsend.com/view/xxxxx`)
6. Click the extension icon to download as PDF

## Publishing to Chrome Web Store

### Prerequisites

1. Register as a Chrome Web Store Developer ($5 one-time fee)
   - Go to https://chrome.google.com/webstore/devconsole
   - Complete registration

2. Host the Privacy Policy
   - Upload `PRIVACY_POLICY.md` to a public URL (GitHub Gist works well)
   - Or host on GitHub Pages

### Create Store Package

```bash
# Create zip excluding development files
cd docsend-pdf-extension
zip -r ../docsend-pdf-extension.zip . -x "*.git*" -x "*.DS_Store" -x "README.md"
```

### Submit to Chrome Web Store

1. Go to Chrome Web Store Developer Dashboard
2. Click "New Item"
3. Upload the .zip file
4. Fill in store listing:
   - **Name**: Docsend to PDF
   - **Summary**: Download Docsend presentations as PDF files with one click
   - **Description**: See suggested description below
   - **Category**: Productivity
5. Upload screenshots (1280x800 or 640x400)
6. Add privacy policy URL
7. Submit for review (typically 1-3 days)

### Suggested Store Description

```
Docsend to PDF lets you download any Docsend presentation as a high-quality PDF file.

Features:
- One-click download - just click the extension icon while viewing a Docsend presentation
- High quality - captures slides at their original resolution
- Fast - uses direct image extraction when possible
- Privacy-focused - all processing happens locally, no data sent to external servers

How to use:
1. Navigate to any Docsend presentation
2. Click the extension icon
3. Wait for slides to be captured
4. PDF automatically downloads

Works with public presentations and email-gated presentations (after you've entered your email).

Note: This extension is not affiliated with Docsend or Dropbox.
```

## Technical Details

- Uses Manifest V3 (latest Chrome extension format)
- Primary method: Fetches slide images via Docsend's `page_data` API
- Fallback: Captures screenshots if API method fails
- PDF generation: Uses pdf-lib library for high-quality output

## Permissions Explained

- **activeTab**: Access the current tab when you click the extension
- **scripting**: Inject scripts to detect slides on Docsend pages
- **downloads**: Save the generated PDF to your computer
- **Host permissions**: Access Docsend pages and their CDN (CloudFront)

## License

MIT
