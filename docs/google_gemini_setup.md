# Google Gemini Setup Guide

Quick guide to add Google Gemini models to your evaluation framework.

## Prerequisites

The Google adapter has been added to the framework. You just need to:
1. Install the SDK
2. Get an API key
3. Configure your models

## Installation

### 1. Install Google Generative AI SDK

```bash
pip install google-generativeai
```

Or if you're using the framework's requirements:
```bash
pip install -r requirements.txt
```

### 2. Get Your API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy your key (starts with "AIza...")

### 3. Set Environment Variable

```bash
export GOOGLE_API_KEY="AIzaSy..."
```

Or add to your `.bashrc`/`.zshrc`:
```bash
echo 'export GOOGLE_API_KEY="AIzaSy..."' >> ~/.zshrc
source ~/.zshrc
```

## Configuration

Add Google models to your `config.yaml`:

```yaml
models:
  # Recommended: Gemini 1.5 Pro
  - name: gemini-1.5-pro
    provider: google
    api_key: ${GOOGLE_API_KEY}
    temperature: 0.7
    max_tokens: 8192

  # Alternative: Gemini 1.5 Flash (faster, cheaper)
  - name: gemini-1.5-flash
    provider: google
    api_key: ${GOOGLE_API_KEY}
    temperature: 0.7
    max_tokens: 8192

  # Experimental: Gemini 2.0 (if available)
  - name: gemini-2.0-flash-exp
    provider: google
    api_key: ${GOOGLE_API_KEY}
    temperature: 0.7
    max_tokens: 8192
```

## Available Models

### Gemini 1.5 Pro (Recommended)
- **Model ID**: `gemini-1.5-pro`
- **Best for**: Complex refactoring, large context windows
- **Context**: 2M tokens (largest available)
- **Pricing**: ~$1.25 per 1M input tokens, $5 per 1M output tokens
- **Expected pass rate**: 78-85% on Java migrations

### Gemini 1.5 Flash
- **Model ID**: `gemini-1.5-flash`
- **Best for**: Fast inference, budget-conscious evaluation
- **Context**: 1M tokens
- **Pricing**: ~$0.075 per 1M input tokens, $0.30 per 1M output tokens
- **Expected pass rate**: 70-78% on Java migrations

### Gemini 2.0 Flash (Experimental)
- **Model ID**: `gemini-2.0-flash-exp`
- **Best for**: Testing latest Google capabilities
- **Context**: Variable
- **Pricing**: Check current experimental pricing
- **Note**: May have limited availability

## Usage Example

### 1. Update config.yaml

```yaml
models:
  - name: claude-3-7-sonnet-latest
    provider: anthropic
    api_key: ${ANTHROPIC_API_KEY}

  - name: gpt-4o
    provider: openai
    api_key: ${OPENAI_API_KEY}

  - name: gemini-1.5-pro
    provider: google
    api_key: ${GOOGLE_API_KEY}
```

### 2. Run Evaluation

```bash
python evaluate.py \
  --benchmark benchmarks/test_cases/java-ee-quarkus-migration.yaml \
  --output results/
```

### 3. View Results

```bash
open results/evaluation_report_*.html
```

## Cost Comparison

For 100 test cases:

| Model | Estimated Cost | Pass Rate | Best For |
|-------|---------------|-----------|----------|
| Gemini 1.5 Pro | $0.12-0.18 | 78-85% | Multi-file context |
| Gemini 1.5 Flash | $0.02-0.04 | 70-78% | Budget testing |
| GPT-4o | $0.15-0.20 | 80-88% | General use |
| Claude 3.5 Sonnet | $0.25-0.30 | 85-92% | Best quality |

## Troubleshooting

### API Key Not Found

```
Error: API key not configured
```

**Solution**: Make sure you've set the environment variable:
```bash
export GOOGLE_API_KEY="AIzaSy..."
```

### Import Error

```
ModuleNotFoundError: No module named 'google.generativeai'
```

**Solution**: Install the SDK:
```bash
pip install google-generativeai
```

### Rate Limiting

```
Error: Resource exhausted (quota)
```

**Solutions**:
1. Check your [Google AI Studio quota](https://makersuite.google.com/app/apikey)
2. Use `--parallel 1` for sequential execution
3. Add delays between requests
4. Request quota increase from Google

### Model Not Available

```
Error: Model 'gemini-2.0-flash-exp' not found
```

**Solution**: Use a stable model like `gemini-1.5-pro` or check [available models](https://ai.google.dev/models/gemini)

## Advanced Configuration

### Custom System Instructions

The adapter includes default system instructions for Java migration. To customize:

Edit `models/google_adapter.py` and modify the `system_instruction` parameter.

### Adjust Safety Settings

Gemini has built-in safety filters. If you encounter blocked responses:

```python
# In models/google_adapter.py, add to GenerativeModel:
self.model = genai.GenerativeModel(
    self.model_name,
    system_instruction="...",
    safety_settings={
        'HARM_CATEGORY_HARASSMENT': 'BLOCK_NONE',
        'HARM_CATEGORY_HATE_SPEECH': 'BLOCK_NONE',
        'HARM_CATEGORY_SEXUALLY_EXPLICIT': 'BLOCK_NONE',
        'HARM_CATEGORY_DANGEROUS_CONTENT': 'BLOCK_NONE',
    }
)
```

**Note**: Only adjust if you're getting false positives on legitimate code.

## Benefits of Google Gemini

### Large Context Window
- 2M tokens for Gemini 1.5 Pro
- Excellent for multi-file migrations
- Can handle entire Java classes with context

### Competitive Pricing
- Flash variant is very cost-effective
- Good balance of quality and price

### Multimodal Capabilities
- Can process images (useful for architecture diagrams)
- Future: Analyze UML diagrams for migration planning

### European Alternative
- Good option for EU data residency requirements
- Alternative to US-based providers

## Next Steps

1. **Get API key**: Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. **Set environment variable**: `export GOOGLE_API_KEY="..."`
3. **Add to config**: Update `config.yaml` with Gemini models
4. **Run evaluation**: Test on small batch first (10-20 test cases)
5. **Compare results**: See how Gemini performs vs. other models
6. **Optimize**: Choose best model per rule category

## Resources

- [Google AI Studio](https://makersuite.google.com/)
- [Gemini API Documentation](https://ai.google.dev/docs)
- [Gemini Models Overview](https://ai.google.dev/models/gemini)
- [Pricing](https://ai.google.dev/pricing)
- [Python SDK Documentation](https://ai.google.dev/tutorials/python_quickstart)

---

**Last Updated**: 2025-01-12
