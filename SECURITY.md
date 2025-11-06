# Security Policy for RWC

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability in RWC, please contact us directly via the GitHub security reporting feature. Please provide the following information:

- A description of the vulnerability
- Steps to reproduce the issue
- Potential impact of the vulnerability
- Any possible mitigations

We will respond as soon as possible, typically within 48 hours.

## Security Best Practices for Users

### Model Security
- Keep model files secure and restrict access to authorized users
- Verify the source of any additional models downloaded
- Regularly update to the latest version to receive security patches

### API Security
- When deploying the API, use HTTPS to encrypt data in transit
- Implement authentication/authorization if exposing endpoints publicly
- Validate and sanitize all input data to prevent injection attacks

### Audio Processing
- Validate audio file formats to prevent malicious file processing
- Implement size limits on uploaded audio files to prevent resource exhaustion
- Sanitize output paths to prevent directory traversal attacks