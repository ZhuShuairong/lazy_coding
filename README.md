# Online Judge Code Submission Automation

This project automates the process of solving coding problems on online judge platforms using AI-powered code generation and iterative improvement. It uses Selenium for browser automation and integrates with AI models (DeepSeek API or Ollama) to generate, submit, and refine code solutions based on test case feedback.

## Features

- **Automated Login and Navigation**: Handles authentication and navigation to assignment pages
- **Problem Scraping**: Extracts problem requirements and initial code from web pages
- **AI-Powered Code Generation**: Uses DeepSeek or Ollama models to generate Python solutions
- **Iterative Improvement**: Analyzes test results and rewrites code based on feedback
- **Multiple Attempts**: Supports configurable number of submission attempts
- **Detailed Feedback Analysis**: Parses test case results, memory usage, and execution times
- **CodeMirror Integration**: Properly handles code editor interactions

## Supported AI Models

### DeepSeek Integration (`idontliketocode_deepseek.py`)
- Uses DeepSeek's chat API for code generation
- Requires API key configuration
- Optimized for performance and accuracy

### Ollama Integration (`idontliketocode_ollama.py`)
- Uses local Ollama models for offline operation
- Supports multiple models (Llama2, CodeLlama, DeepSeek-Coder, etc.)
- No API keys required - runs entirely locally

## Prerequisites

- Python 3.7+
- Google Chrome browser
- For Ollama version: Ollama installed and running locally
- For DeepSeek version: Valid DeepSeek API key

## Installation

1. Clone or download the project files
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### For Ollama Version
1. Install Ollama: https://ollama.ai/
2. Pull a coding model:
   ```bash
   ollama pull codellama
   # or
   ollama pull deepseek-coder
   # or
   ollama pull llama2
   ```
3. Start Ollama server:
   ```bash
   ollama serve
   ```

## Usage

### DeepSeek Version
```bash
python idontliketocode_deepseek.py
```

### Ollama Version
```bash
python idontliketocode_ollama.py
```

### Input Requirements
The script will prompt for:
- Username and password for the online judge platform
- Assignment URL
- Maximum number of attempts (1-10 recommended)

## How It Works

1. **Login**: Authenticates with the online judge platform
2. **Problem Extraction**: Scrapes problem description and any initial code
3. **Code Generation**: Uses AI to generate a complete Python solution
4. **Submission**: Automatically submits the code to the judge
5. **Result Analysis**: Parses test case results and feedback
6. **Iteration**: If tests fail, analyzes feedback and generates improved code
7. **Completion**: Continues until solution passes or max attempts reached

## Supported Platforms

Currently configured for:
- University of Macau Online Judge (oj-cds.sicc.um.edu.mo)
- Can be adapted for other platforms with similar structure

## Configuration

### DeepSeek API Key
In `idontliketocode_deepseek.py`, update the API key:
```python
self.api_key = "your_deepseek_api_key_here"
```

### Browser Options
To run headless (without GUI):
```python
options.add_argument("--headless")
```

### Timeouts and Delays
Adjust timeouts in the code as needed for slower connections:
- Login timeout: 20 seconds
- Page load timeout: 10 seconds
- Submission evaluation: 30 seconds

## Dependencies

- `selenium`: Browser automation
- `webdriver-manager`: Automatic ChromeDriver management
- `ollama`: Local AI model integration (Ollama version only)
- `openai`: DeepSeek API client (DeepSeek version only)
- `requests`: HTTP requests (included for compatibility)

## Troubleshooting

### Common Issues

1. **ChromeDriver Issues**: webdriver-manager should handle this automatically
2. **Login Failures**: Verify credentials and platform availability
3. **AI Model Errors**: 
   - For Ollama: Ensure model is pulled and server is running
   - For DeepSeek: Verify API key and credits
4. **Timeout Errors**: Increase timeout values for slower connections
5. **CodeMirror Issues**: The script includes multiple fallback methods for code input

### Debug Mode
Remove the comment from the headless option to see browser interactions:
```python
options.add_argument("--headless")  # Remove comment for headless mode
```

## Ethical Considerations

This tool is intended for educational purposes and automated testing of coding assignments. Users should:
- Only use on platforms where automation is permitted
- Respect rate limits and submission policies
- Not use for academic dishonesty

## License

This project is for educational purposes. Use responsibly and in accordance with platform terms of service.

## Contributing

Feel free to submit issues or pull requests for improvements and additional platform support.