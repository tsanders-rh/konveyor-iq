# Model Recommendations for Code Generation Evaluation

This document provides recommendations for selecting LLM models to evaluate for application modernization and code generation tasks.

## Quick Start: Recommended Model Lineup

For most evaluation scenarios, start with these 2-5 models:

### Minimal Setup (2 models)
```yaml
models:
  - name: claude-3-5-sonnet-20240620
    provider: anthropic
    api_key: ${ANTHROPIC_API_KEY}
    temperature: 0.7

  - name: gpt-4o
    provider: openai
    api_key: ${OPENAI_API_KEY}
    temperature: 0.7
```

### Recommended Setup (5 models)
```yaml
models:
  # Best overall commercial model
  - name: claude-3-5-sonnet-20240620
    provider: anthropic
    api_key: ${ANTHROPIC_API_KEY}
    temperature: 0.7

  # Best cost/performance
  - name: gpt-4o
    provider: openai
    api_key: ${OPENAI_API_KEY}
    temperature: 0.7

  # Budget option (fast & cheap)
  - name: claude-3-haiku-20240307
    provider: anthropic
    api_key: ${ANTHROPIC_API_KEY}
    temperature: 0.7

  # Google alternative
  - name: gemini-1.5-pro
    provider: google
    api_key: ${GOOGLE_API_KEY}
    temperature: 0.7

  # Reasoning model (if budget allows)
  - name: o1-preview
    provider: openai
    api_key: ${OPENAI_API_KEY}
    # Note: o1 models don't use temperature parameter
```

---

## Tier 1: Must-Have Models (Commercial Leaders)

### OpenAI Models

#### `gpt-4o` (GPT-4 Omni) ⭐ Top Recommendation
- **Best for**: General-purpose code generation with excellent cost/performance balance
- **Strengths**:
  - Very strong at code generation
  - Fast response times
  - Good at pattern replacement and refactoring
  - Excellent reliability
- **Pricing**: ~$2.50 per 1M input tokens, $10 per 1M output tokens
- **Expected Performance**: 80-88% pass rate on Java migrations
- **Cost per 100 tests**: ~$0.15-0.20

#### `gpt-4-turbo`
- **Best for**: Complex refactoring tasks requiring deep understanding
- **Strengths**:
  - Excellent code quality
  - Strong reasoning capabilities
  - Good for multi-file changes
- **Pricing**: ~$10 per 1M input tokens, $30 per 1M output tokens
- **Expected Performance**: 82-87% pass rate
- **Cost per 100 tests**: ~$0.30-0.40

#### `o1-preview` or `o1-mini`
- **Best for**: Complex logic and architectural decisions
- **Strengths**:
  - Uses chain-of-thought reasoning
  - Excellent at solving complex problems
  - Best for challenging refactoring scenarios
- **Pricing**: ~$15 per 1M input tokens, $60 per 1M output tokens
- **Expected Performance**: 90-95% pass rate (when appropriate)
- **Cost per 100 tests**: ~$1.50-2.00
- **Note**: More expensive; use strategically for complex cases

### Anthropic Models

#### `claude-3-5-sonnet-20240620` ⭐ Top Recommendation
- **Best for**: Overall best code generation quality and explanations
- **Strengths**:
  - Superior code explanations
  - Very strong at complex refactoring
  - Excellent at understanding context
  - Best-in-class for application modernization
- **Pricing**: ~$3 per 1M input tokens, $15 per 1M output tokens
- **Expected Performance**: 85-92% pass rate on Java migrations
- **Cost per 100 tests**: ~$0.25-0.30

#### `claude-3-haiku-20240307`
- **Best for**: Budget-conscious evaluations, simple pattern replacements
- **Strengths**:
  - Very fast response times
  - Good quality at low cost
  - Efficient for batch processing
- **Pricing**: ~$0.80 per 1M input tokens, $4 per 1M output tokens
- **Expected Performance**: 70-80% pass rate
- **Cost per 100 tests**: ~$0.05-0.10

---

## Tier 2: Strong Contenders

### Google Models

#### `gemini-1.5-pro`
- **Best for**: Multi-file refactoring, large context windows
- **Strengths**:
  - Very large context window (2M tokens)
  - Competitive with GPT-4 and Claude
  - Good for complex migrations involving many files
  - Strong code understanding
- **Pricing**: ~$1.25 per 1M input tokens, $5 per 1M output tokens
- **Expected Performance**: 78-85% pass rate
- **Cost per 100 tests**: ~$0.12-0.18
- **Setup Required**: Add Google adapter (see Implementation section below)

#### `gemini-2.0-flash-exp` (Experimental)
- **Best for**: Cutting-edge Google model evaluation
- **Strengths**:
  - Very fast inference
  - Latest Google architecture
  - Good early performance reports
- **Pricing**: Experimental pricing (check current rates)
- **Note**: May have limited availability or unstable API

### Amazon Bedrock Models

#### `amazon.nova-pro-v1:0`
- **Best for**: AWS ecosystem integration
- **Strengths**:
  - Competitive pricing
  - Strong code capabilities
  - Native AWS integration
- **Pricing**: Check AWS Bedrock pricing (varies by region)
- **Setup Required**: AWS credentials and Bedrock adapter

---

## Tier 3: Specialized Code Models

### Mistral

#### `codestral-latest`
- **Best for**: Code-specific tasks, developers familiar with Mistral
- **Strengths**:
  - Specifically trained for code generation
  - Good for code completion
  - Competitive pricing
  - European alternative
- **Pricing**: ~$1 per 1M input tokens, $3 per 1M output tokens
- **Setup Required**: Mistral API key and adapter

### DeepSeek

#### `deepseek-coder-v2`
- **Best for**: Cost-effective code generation, open-source alternative
- **Strengths**:
  - Strong open-source code model
  - Very cost-effective
  - Can run locally or via API
- **Pricing**: Variable (free if self-hosted, API pricing if using their service)
- **Setup Required**: DeepSeek API or local deployment

---

## Tier 4: Open Source / Local Models

These models can be run locally using Ollama, vLLM, or other local inference servers.

### Via Ollama (Local Deployment)

#### `qwen2.5-coder:32b`
- **Best for**: Local evaluation, no API costs
- **Strengths**:
  - Excellent local code model
  - Free to run (GPU costs only)
  - 32B parameter version is very capable
  - Good privacy (all local)
- **Requirements**:
  - GPU with 24GB+ VRAM for 32B version
  - Ollama installed locally
- **Expected Performance**: 70-85% pass rate
- **Cost**: Free (hardware/electricity only)

#### `deepseek-coder-v2:16b`
- **Best for**: Mid-range local deployment
- **Strengths**:
  - Strong local alternative
  - Good balance of quality and speed
  - Lower VRAM requirements than 32B models
- **Requirements**: GPU with 16GB+ VRAM
- **Expected Performance**: 65-80% pass rate

#### `codellama:70b`
- **Best for**: High-end local deployment with maximum quality
- **Strengths**:
  - Meta's code-specific model
  - Solid performance on code tasks
  - Well-documented
- **Requirements**:
  - GPU with 48GB+ VRAM (or multi-GPU setup)
  - Significant compute resources
- **Expected Performance**: 75-85% pass rate

---

## Implementation Guide

### Phase 1: Validate Framework (Start Here)

**Goal**: Validate your framework works correctly with minimal cost

**Models**: 2
```yaml
models:
  - claude-3-5-sonnet-20240620  # Best quality
  - gpt-4o                       # Best value
```

**Expected Cost**: ~$0.50 for 100 test cases
**Timeline**: Day 1

### Phase 2: Comprehensive Comparison

**Goal**: Compare across different model families and price points

**Models**: Add 3 more
```yaml
  - claude-3-haiku-20240307   # Budget option
  - gemini-1.5-pro               # Google alternative
  - o1-preview                   # Reasoning model (optional)
```

**Expected Cost**: ~$2.50 for 100 test cases (all 5 models)
**Timeline**: Week 1

### Phase 3: Deep Dive

**Goal**: Specialized models and edge case testing

**Models**: Add specialized options
```yaml
  - gpt-4-turbo                  # OpenAI premium
  - codestral-latest             # Specialized code model
  - deepseek-coder-v2            # Open source alternative
```

**Expected Cost**: Variable
**Timeline**: Month 1

### Phase 4: Local/Open Source

**Goal**: Cost optimization and privacy

**Models**: Local deployment
```yaml
  - qwen2.5-coder:32b           # Via Ollama
  - deepseek-coder-v2:16b       # Via Ollama
```

**Expected Cost**: Free (GPU costs only)
**Timeline**: As needed

---

## Adding Google Gemini Support

The framework currently supports OpenAI and Anthropic. To add Google Gemini:

### 1. Install Google SDK

Add to `requirements.txt`:
```
google-generativeai>=0.3.0
```

Install:
```bash
pip install google-generativeai
```

### 2. Create Google Adapter

Create `models/google_adapter.py`:

```python
"""Google Gemini model adapter."""
from typing import Dict, Any
import google.generativeai as genai
from .base import BaseModel


class GoogleModel(BaseModel):
    """Adapter for Google Gemini models."""

    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        genai.configure(api_key=config.get("api_key"))
        self.model = genai.GenerativeModel(name)
        self.generation_config = genai.GenerationConfig(
            temperature=config.get("temperature", 0.7),
            max_output_tokens=config.get("max_tokens", 8192),
        )

    def generate(self, prompt: str) -> str:
        """Generate response from Gemini model."""
        response = self.model.generate_content(
            prompt,
            generation_config=self.generation_config
        )
        return response.text

    def generate_with_timing(self, prompt: str) -> Dict[str, Any]:
        """Generate with timing and usage tracking."""
        import time
        start_time = time.time()

        response = self.model.generate_content(
            prompt,
            generation_config=self.generation_config
        )

        response_time_ms = (time.time() - start_time) * 1000

        # Extract usage metadata
        tokens_used = 0
        if hasattr(response, 'usage_metadata'):
            tokens_used = (
                response.usage_metadata.prompt_token_count +
                response.usage_metadata.candidates_token_count
            )

        # Estimate cost (update with current pricing)
        input_cost = 1.25 / 1_000_000  # $1.25 per 1M input tokens
        output_cost = 5.0 / 1_000_000  # $5.00 per 1M output tokens

        estimated_cost = (
            response.usage_metadata.prompt_token_count * input_cost +
            response.usage_metadata.candidates_token_count * output_cost
        )

        return {
            "response": response.text,
            "response_time_ms": response_time_ms,
            "tokens_used": tokens_used,
            "cost": estimated_cost
        }
```

### 3. Update Main Evaluator

In `evaluate.py`, add Google model support:

```python
from models import OpenAIModel, AnthropicModel, GoogleModel

def _initialize_models(self) -> List[Any]:
    """Initialize LLM models from config."""
    models = []

    for model_config in self.config.get("models", []):
        provider = model_config.get("provider")
        name = model_config.get("name")

        # Expand environment variables in API keys
        if "api_key" in model_config:
            api_key = model_config["api_key"]
            if api_key.startswith("${") and api_key.endswith("}"):
                env_var = api_key[2:-1]
                model_config["api_key"] = os.getenv(env_var)

        if provider == "openai":
            models.append(OpenAIModel(name, model_config))
        elif provider == "anthropic":
            models.append(AnthropicModel(name, model_config))
        elif provider == "google":
            models.append(GoogleModel(name, model_config))
        else:
            print(f"Warning: Unknown provider '{provider}' for model '{name}'")

    return models
```

### 4. Update models/__init__.py

```python
from .openai_adapter import OpenAIModel
from .anthropic_adapter import AnthropicModel
from .google_adapter import GoogleModel

__all__ = ['OpenAIModel', 'AnthropicModel', 'GoogleModel']
```

### 5. Configure in config.yaml

```yaml
models:
  - name: gemini-1.5-pro
    provider: google
    api_key: ${GOOGLE_API_KEY}
    temperature: 0.7
    max_tokens: 8192
```

### 6. Set Environment Variable

```bash
export GOOGLE_API_KEY="your-api-key-here"
```

---

## Expected Performance Summary

Based on industry benchmarks and typical Java EE → Quarkus migration tasks:

| Model | Pass Rate | Cost/100 Tests | Response Time | Best For |
|-------|-----------|----------------|---------------|----------|
| **Claude 3.5 Sonnet** | 85-92% | $0.25-0.30 | Medium | Complex refactoring, best explanations |
| **GPT-4o** | 80-88% | $0.15-0.20 | Fast | General migrations, best value |
| **Claude Haiku** | 70-80% | $0.05-0.10 | Very Fast | Simple patterns, budget option |
| **Gemini 1.5 Pro** | 78-85% | $0.12-0.18 | Medium | Multi-file context, large codebases |
| **o1-preview** | 90-95% | $1.50-2.00 | Slow | Complex logic, challenging cases |
| **GPT-4 Turbo** | 82-87% | $0.30-0.40 | Medium | Premium quality, complex tasks |
| **Qwen 2.5 Coder 32B** | 70-85% | Free | Fast | Local, privacy-focused |
| **Codestral** | 75-83% | $0.08-0.12 | Fast | Code-specific tasks |

---

## Cost Projections

### Small Evaluation (100 test cases)
- **All 5 recommended models**: ~$2.50
- **Minimal 2 models** (Claude + GPT-4o): ~$0.50

### Medium Evaluation (500 test cases)
- **All 5 recommended models**: ~$12.50
- **Minimal 2 models**: ~$2.50

### Large Evaluation (2,000 test cases)
- **All 5 recommended models**: ~$50
- **Minimal 2 models**: ~$10

### Cost-Saving Strategies

1. **Start small**: Validate with 2 models on 50-100 test cases first
2. **Use budget models**: Claude Haiku for simple pattern testing
3. **Parallel execution**: Run multiple test cases simultaneously (doesn't increase cost, just faster)
4. **Local models**: Use Ollama for development/testing, commercial APIs for production evaluation
5. **Filter test cases**: Focus on representative samples rather than exhaustive testing

---

## Model Selection Decision Tree

```
Do you need the absolute best quality?
├─ YES → Claude 3.5 Sonnet
└─ NO
   ├─ Is cost your primary concern?
   │  ├─ YES → Claude Haiku or local models (Qwen, DeepSeek)
   │  └─ NO → GPT-4o (best balance)
   │
   ├─ Do you need reasoning capabilities?
   │  └─ YES → o1-preview or o1-mini
   │
   ├─ Working with very large codebases?
   │  └─ YES → Gemini 1.5 Pro (2M context window)
   │
   ├─ Need local/private deployment?
   │  └─ YES → Qwen 2.5 Coder 32B or DeepSeek Coder v2
   │
   └─ Want European/open alternative?
      └─ YES → Codestral or Mistral models
```

---

## API Key Setup

### OpenAI
```bash
export OPENAI_API_KEY="sk-..."
```
Get your key at: https://platform.openai.com/api-keys

### Anthropic
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```
Get your key at: https://console.anthropic.com/

### Google
```bash
export GOOGLE_API_KEY="AIza..."
```
Get your key at: https://makersuite.google.com/app/apikey

### Mistral
```bash
export MISTRAL_API_KEY="..."
```
Get your key at: https://console.mistral.ai/

---

## Frequently Asked Questions

### Q: Which single model should I start with?

**A**: Claude 3.5 Sonnet (20241022). It's the current best overall for code generation and provides excellent explanations that help understand why fixes work or fail.

### Q: What if I'm on a tight budget?

**A**:
1. Start with just **GPT-4o** (best value)
2. Add **Claude Haiku** for comparison (very cheap)
3. Consider local models like **Qwen 2.5 Coder** (free after hardware)

### Q: Should I use o1-preview for everything?

**A**: No. o1 models are expensive and slower. Use them strategically:
- Complex architectural decisions
- Difficult logic transformations
- Cases where other models consistently fail

For simple pattern replacements (80% of migrations), stick with GPT-4o or Claude Sonnet.

### Q: How do local models compare?

**A**: Local models (Qwen, DeepSeek, CodeLlama) are:
- **Quality**: 10-20% lower pass rates than top commercial models
- **Cost**: Free after hardware investment
- **Privacy**: Complete control over your data
- **Speed**: Can be faster with good GPU hardware

Best for: Development, testing, privacy-sensitive code, high-volume evaluation after validating with commercial models.

### Q: Can I mix models for different rules?

**A**: Yes! This is actually recommended:
- Use Claude Sonnet for complex refactoring rules
- Use GPT-4o for general pattern replacements
- Use Claude Haiku for simple annotation changes

The framework's reports will help you identify which model works best for which rule types.

### Q: How often should I re-evaluate?

**A**:
- **Models update frequently** (every 1-3 months)
- Re-evaluate when:
  - New model versions are released
  - You add new test cases
  - You update your Konveyor rules
  - Every quarter for continuous monitoring

---

## Next Steps

1. **Choose your starting models** (recommend: Claude 3.5 Sonnet + GPT-4o)
2. **Set up API keys** in your environment
3. **Update config.yaml** with your model selection
4. **Run a small evaluation** (10-20 test cases) to validate setup
5. **Analyze results** and decide if you need additional models
6. **Scale up** to full evaluation once validated

---

## Additional Resources

- [OpenAI Models Documentation](https://platform.openai.com/docs/models)
- [Anthropic Claude Documentation](https://docs.anthropic.com/claude/docs)
- [Google Gemini Documentation](https://ai.google.dev/docs)
- [Mistral Models](https://docs.mistral.ai/)
- [Ollama Model Library](https://ollama.ai/library)

---

**Last Updated**: 2025-01-12
**Maintained By**: Konveyor AI Evaluation Framework Team
