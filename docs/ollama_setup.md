# Using Ollama for Local Model Testing

This guide shows you how to set up and use Ollama for running LLMs locally with the Konveyor AI Evaluation Framework.

## What is Ollama?

[Ollama](https://ollama.ai) is a tool that makes it easy to run large language models locally on your machine. Think of it as "Docker for LLMs" - you can pull, run, and manage models with simple commands.

**Benefits**:
- 🆓 **Free**: No API costs (just hardware/electricity)
- 🔒 **Privacy**: Your code never leaves your machine
- ⚡ **Fast**: No network latency (if you have good GPU)
- 🧪 **Experimentation**: Test unlimited variations without cost

**Trade-offs**:
- 📊 Quality: 10-20% lower pass rates than top commercial models (Claude, GPT-4)
- 💻 Hardware: Requires decent GPU (8GB+ VRAM recommended)
- 🔧 Setup: More complex than API keys

---

## Installation

### macOS
```bash
# Download from website
open https://ollama.ai/download

# Or use Homebrew
brew install ollama
```

### Linux
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

### Windows
Download installer from: https://ollama.ai/download

### Verify Installation
```bash
ollama --version
# Should show: ollama version 0.x.x
```

---

## Starting Ollama

Ollama runs as a background service:

```bash
# Start Ollama server
ollama serve
```

**Note**: On macOS/Windows, the app starts the server automatically. On Linux, you may need to run `ollama serve` in a separate terminal or as a systemd service.

---

## Recommended Models for Code Generation

### Best Overall: Qwen 2.5 Coder

```bash
# Download and run (requires ~20GB disk, 16GB+ VRAM for 32B)
ollama pull qwen2.5-coder:32b

# Smaller variant (requires ~8GB disk, 8GB+ VRAM)
ollama pull qwen2.5-coder:7b

# Test it
ollama run qwen2.5-coder:32b "Write a hello world in Java"
```

**Why Qwen 2.5 Coder?**
- Best local code model currently available
- Strong performance on Java and refactoring tasks
- Multiple sizes to fit your hardware
- Expected pass rate: 70-85% (32B version)

### Alternative: DeepSeek Coder V2

```bash
# Download (requires ~9GB disk, 10GB+ VRAM)
ollama pull deepseek-coder-v2:16b

# Smaller variant
ollama pull deepseek-coder-v2:1.3b

# Test it
ollama run deepseek-coder-v2:16b "Refactor this Java code to use CDI"
```

**Why DeepSeek Coder V2?**
- Excellent code understanding
- Good balance of size and quality
- Fast inference
- Expected pass rate: 65-80% (16B version)

### Classic: CodeLlama

```bash
# Download (requires ~38GB disk, 48GB+ VRAM for 70B!)
ollama pull codellama:70b

# More practical size
ollama pull codellama:13b

# Test it
ollama run codellama:13b "Convert @Stateless to @ApplicationScoped"
```

**Why CodeLlama?**
- Well-documented and tested
- Meta's official code model
- Solid baseline for comparison
- Expected pass rate: 60-75% (13B version)

### Comparison Table

| Model | Size | VRAM Needed | Disk Space | Expected Pass Rate | Speed |
|-------|------|-------------|------------|-------------------|-------|
| **qwen2.5-coder:32b** | 32B | 20GB | 20GB | 70-85% | Medium |
| **qwen2.5-coder:7b** | 7B | 8GB | 8GB | 55-70% | Fast |
| **deepseek-coder-v2:16b** | 16B | 12GB | 10GB | 65-80% | Fast |
| **deepseek-coder-v2:1.3b** | 1.3B | 2GB | 1.5GB | 40-55% | Very Fast |
| **codellama:70b** | 70B | 48GB+ | 40GB | 75-85% | Slow |
| **codellama:13b** | 13B | 10GB | 8GB | 60-75% | Medium |

---

## Creating the Ollama Adapter

### 1. Install Ollama Python SDK

Add to `requirements.txt`:
```
ollama>=0.1.0
```

Install:
```bash
pip install ollama
```

### 2. Create the Adapter

Create `models/ollama_adapter.py`:

```python
"""Ollama local model adapter."""
from typing import Dict, Any
import ollama
from .base import BaseModel


class OllamaModel(BaseModel):
    """Adapter for Ollama local models."""

    def __init__(self, name: str, config: Dict[str, Any]):
        """
        Initialize Ollama model.

        Args:
            name: Model name (e.g., 'qwen2.5-coder:32b')
            config: Configuration dictionary
        """
        super().__init__(name, config)
        self.model_name = name
        self.temperature = config.get("temperature", 0.7)
        self.max_tokens = config.get("max_tokens", 8192)
        self.host = config.get("host", "http://localhost:11434")

        # Verify model is available
        try:
            ollama.show(self.model_name)
        except Exception as e:
            print(f"Warning: Model '{name}' not found locally. Run: ollama pull {name}")
            print(f"Error: {e}")

    def generate(self, prompt: str) -> str:
        """Generate response from Ollama model."""
        response = ollama.generate(
            model=self.model_name,
            prompt=prompt,
            options={
                'temperature': self.temperature,
                'num_predict': self.max_tokens,
            }
        )
        return response['response']

    def generate_with_timing(self, prompt: str) -> Dict[str, Any]:
        """Generate with timing and usage tracking."""
        import time
        start_time = time.time()

        response = ollama.generate(
            model=self.model_name,
            prompt=prompt,
            options={
                'temperature': self.temperature,
                'num_predict': self.max_tokens,
            }
        )

        response_time_ms = (time.time() - start_time) * 1000

        # Ollama responses include token counts
        tokens_used = (
            response.get('prompt_eval_count', 0) +
            response.get('eval_count', 0)
        )

        return {
            "response": response['response'],
            "response_time_ms": response_time_ms,
            "tokens_used": tokens_used,
            "cost": 0.0,  # Local models have no API cost
            "model": response.get('model', self.model_name),
            "eval_duration_ms": response.get('eval_duration', 0) / 1_000_000,  # Convert ns to ms
        }

    def extract_code_and_explanation(self, response: str) -> tuple[str, str]:
        """Extract code and explanation from response."""
        # Use base class implementation
        return super().extract_code_and_explanation(response)
```

### 3. Update models/__init__.py

```python
from .openai_adapter import OpenAIModel
from .anthropic_adapter import AnthropicModel
from .ollama_adapter import OllamaModel

__all__ = ['OpenAIModel', 'AnthropicModel', 'OllamaModel']
```

### 4. Update evaluate.py

Add Ollama support to model initialization:

```python
from models import OpenAIModel, AnthropicModel, OllamaModel

def _initialize_models(self) -> List[Any]:
    """Initialize LLM models from config."""
    models = []

    for model_config in self.config.get("models", []):
        provider = model_config.get("provider")
        name = model_config.get("name")

        # Expand environment variables in API keys (for cloud providers)
        if "api_key" in model_config:
            api_key = model_config["api_key"]
            if api_key.startswith("${") and api_key.endswith("}"):
                env_var = api_key[2:-1]
                model_config["api_key"] = os.getenv(env_var)

        if provider == "openai":
            models.append(OpenAIModel(name, model_config))
        elif provider == "anthropic":
            models.append(AnthropicModel(name, model_config))
        elif provider == "ollama":
            models.append(OllamaModel(name, model_config))
        else:
            print(f"Warning: Unknown provider '{provider}' for model '{name}'")

    return models
```

---

## Configuration

### Basic Configuration

Add to your `config.yaml`:

```yaml
models:
  # Local Ollama models
  - name: qwen2.5-coder:32b
    provider: ollama
    temperature: 0.7
    max_tokens: 8192

  - name: deepseek-coder-v2:16b
    provider: ollama
    temperature: 0.7
    max_tokens: 8192
```

### Mixed Configuration (Local + Cloud)

Compare local models against commercial APIs:

```yaml
models:
  # Commercial (for comparison)
  - name: claude-3-7-sonnet-latest
    provider: anthropic
    api_key: ${ANTHROPIC_API_KEY}
    temperature: 0.7

  - name: gpt-4o
    provider: openai
    api_key: ${OPENAI_API_KEY}
    temperature: 0.7

  # Local (free, private)
  - name: qwen2.5-coder:32b
    provider: ollama
    temperature: 0.7

  - name: deepseek-coder-v2:16b
    provider: ollama
    temperature: 0.7
```

### Custom Ollama Host

If running Ollama on a different machine or port:

```yaml
models:
  - name: qwen2.5-coder:32b
    provider: ollama
    host: http://192.168.1.100:11434  # Custom host
    temperature: 0.7
```

---

## Running Your First Local Evaluation

### Step 1: Pull the Model

```bash
# Download Qwen 2.5 Coder (this will take a few minutes)
ollama pull qwen2.5-coder:32b

# Verify it's downloaded
ollama list
```

### Step 2: Test the Model

```bash
# Quick test
ollama run qwen2.5-coder:32b "Convert this Java EE code to Quarkus: @Stateless public class UserService {}"
```

### Step 3: Update config.yaml

```yaml
models:
  - name: qwen2.5-coder:32b
    provider: ollama
    temperature: 0.7
```

### Step 4: Run Evaluation

```bash
python evaluate.py \
  --benchmark benchmarks/test_cases/java-ee-quarkus-migration.yaml \
  --output results/ \
  --format html
```

### Step 5: View Results

```bash
open results/evaluation_report_*.html
```

---

## Hardware Requirements

### Minimal Setup
- **Model**: `qwen2.5-coder:7b` or `deepseek-coder-v2:1.3b`
- **GPU**: 8GB VRAM (NVIDIA RTX 3060, M1 Mac with 8GB unified memory)
- **RAM**: 16GB
- **Disk**: 10GB free
- **Performance**: Fast inference, 55-70% pass rate

### Recommended Setup
- **Model**: `qwen2.5-coder:32b` or `deepseek-coder-v2:16b`
- **GPU**: 16GB+ VRAM (NVIDIA RTX 4080, M1 Max/Ultra with 32GB+)
- **RAM**: 32GB
- **Disk**: 25GB free
- **Performance**: Good inference, 70-85% pass rate

### High-End Setup
- **Model**: `codellama:70b` or `qwen2.5-coder:32b` with optimizations
- **GPU**: 48GB+ VRAM (NVIDIA A100, H100, multi-GPU)
- **RAM**: 64GB+
- **Disk**: 50GB free
- **Performance**: Best local quality, 75-85% pass rate

### Running Without GPU

Ollama can run on CPU, but it's SLOW:

```bash
# Force CPU mode
OLLAMA_NUM_GPU=0 ollama serve

# Expect 10-100x slower inference
```

**Recommendation**: Use smaller models (1.3B-7B) on CPU, or stick with cloud APIs if you don't have a GPU.

---

## Performance Optimization

### Use Quantized Models

Smaller variants use quantization to reduce size:

```bash
# Pull quantized version (smaller, faster, slightly lower quality)
ollama pull qwen2.5-coder:32b-q4_0  # 4-bit quantization
ollama pull qwen2.5-coder:32b-q8_0  # 8-bit quantization
```

### Adjust Context Window

Reduce max_tokens for faster inference:

```yaml
models:
  - name: qwen2.5-coder:32b
    provider: ollama
    temperature: 0.7
    max_tokens: 4096  # Reduced from 8192 for speed
```

### Enable GPU Acceleration

Ensure Ollama is using your GPU:

```bash
# Check GPU usage during generation
nvidia-smi  # Linux/Windows with NVIDIA

# macOS: GPU usage shows in Activity Monitor
```

### Batch Processing

Process multiple test cases in parallel:

```bash
# Use parallel execution
python evaluate.py \
  --benchmark benchmarks/test_cases/java-ee-quarkus-migration.yaml \
  --parallel 4  # Run 4 test cases at once
```

**Note**: Parallel execution with local models is limited by your GPU memory. Start with `--parallel 2` and increase if you have headroom.

---

## Troubleshooting

### Model Not Found

```
Error: Model 'qwen2.5-coder:32b' not found
```

**Solution**:
```bash
ollama pull qwen2.5-coder:32b
```

### Out of Memory

```
Error: CUDA out of memory
```

**Solutions**:
1. Use a smaller model:
   ```bash
   ollama pull qwen2.5-coder:7b
   ```

2. Reduce max_tokens in config:
   ```yaml
   max_tokens: 2048  # Instead of 8192
   ```

3. Reduce parallel execution:
   ```bash
   python evaluate.py --parallel 1  # Sequential instead of parallel
   ```

### Slow Performance

**Check GPU usage**:
```bash
nvidia-smi
# Look for ollama process using GPU
```

**Solutions**:
1. Use quantized models (q4_0, q8_0 variants)
2. Reduce context window
3. Close other GPU-intensive applications
4. Use CPU-optimized models on CPU-only systems

### Ollama Server Not Running

```
Error: connection refused
```

**Solution**:
```bash
# Start Ollama server
ollama serve
```

Or on macOS/Windows, make sure the Ollama app is running.

### Connection Timeout

```
Error: request timeout
```

**Solutions**:
1. Increase timeout in adapter:
   ```python
   # In ollama_adapter.py
   response = ollama.generate(
       model=self.model_name,
       prompt=prompt,
       options={
           'temperature': self.temperature,
           'num_predict': self.max_tokens,
       },
       timeout=300  # 5 minutes instead of default 30s
   )
   ```

2. Use smaller prompts
3. Use faster model

---

## Comparing Local vs Cloud Models

### Run Comparison Evaluation

```yaml
# config.yaml
models:
  # Cloud baseline
  - name: claude-3-5-sonnet-20241022
    provider: anthropic
    api_key: ${ANTHROPIC_API_KEY}

  - name: gpt-4o
    provider: openai
    api_key: ${OPENAI_API_KEY}

  # Local alternatives
  - name: qwen2.5-coder:32b
    provider: ollama

  - name: deepseek-coder-v2:16b
    provider: ollama
```

```bash
python evaluate.py \
  --benchmark benchmarks/test_cases/java-ee-quarkus-migration.yaml \
  --output results/local-vs-cloud/
```

### Example Results

Based on typical Java EE → Quarkus migrations:

| Model | Pass Rate | Cost (100 tests) | Avg Response Time | Notes |
|-------|-----------|------------------|-------------------|-------|
| **Claude 3.5 Sonnet** | 87% | $0.27 | 3,200ms | Best quality |
| **GPT-4o** | 85% | $0.18 | 2,900ms | Best value |
| **Qwen 2.5 Coder 32B** | 78% | $0.00 | 1,800ms* | Best local |
| **DeepSeek Coder V2 16B** | 72% | $0.00 | 1,200ms* | Fast local |
| **Qwen 2.5 Coder 7B** | 65% | $0.00 | 800ms* | Budget local |

*With good GPU (RTX 4080 or M1 Max)

---

## Use Cases for Local Models

### 1. Development & Testing

**Use local models when**:
- Developing new test cases
- Testing framework changes
- Debugging evaluator logic
- Iterating on prompts

**Why**: Free, fast iteration without API costs

### 2. Privacy-Sensitive Code

**Use local models when**:
- Working with proprietary code
- Evaluating unreleased features
- Security-sensitive applications
- Compliance requirements (GDPR, HIPAA, etc.)

**Why**: Code never leaves your machine

### 3. High-Volume Evaluation

**Use local models when**:
- Running continuous evaluation (CI/CD)
- Testing 1000+ scenarios
- Repeated regression testing
- Cost is a primary concern

**Why**: Zero marginal cost per evaluation

### 4. Baseline Comparison

**Use local models to**:
- Establish minimum acceptable quality
- Show ROI of commercial models
- Validate evaluation framework
- Provide reference point

**Example workflow**:
1. Run with free local model (Qwen 7B): 65% pass rate
2. Run with premium API (Claude): 87% pass rate
3. Decision: Pay $0.27/100 for 22% improvement? Probably yes for production.

---

## Advanced: Custom Model Management

### Create Model Variants

Create a custom model with specific system prompts:

```bash
# Create Modelfile
cat > Modelfile <<EOF
FROM qwen2.5-coder:32b

PARAMETER temperature 0.7
PARAMETER num_ctx 8192

SYSTEM """
You are an expert Java developer specializing in application modernization.
You help migrate Java EE applications to Quarkus.
Always provide working, compilable code with clear explanations.
"""
EOF

# Build custom model
ollama create qwen-java-expert -f Modelfile

# Use in config
# models:
#   - name: qwen-java-expert
#     provider: ollama
```

### List Available Models

```bash
# List downloaded models
ollama list

# Show model details
ollama show qwen2.5-coder:32b
```

### Delete Models

```bash
# Free up disk space
ollama rm codellama:70b
```

---

## Integration with Existing Workflow

### Phase 1: Validate with Cloud Models

```bash
# Initial evaluation with Claude + GPT-4o
python evaluate.py \
  --benchmark benchmarks/test_cases/java-ee-quarkus-migration.yaml \
  --config config-cloud.yaml
```

### Phase 2: Add Local Models

```bash
# Download local model
ollama pull qwen2.5-coder:32b

# Run comparison
python evaluate.py \
  --benchmark benchmarks/test_cases/java-ee-quarkus-migration.yaml \
  --config config-mixed.yaml
```

### Phase 3: Optimize Cost

Based on results, decide:
- Use local models for simple rules (70%+ success)
- Use cloud models for complex rules (90%+ success needed)
- Mix and match per rule category

---

## Cost Analysis

### Scenario: 1,000 Test Cases

**Cloud Only (Claude + GPT-4o)**:
- Cost: ~$4.50
- Time: ~1-2 hours (depending on API rate limits)
- Quality: 85-87% pass rate

**Local Only (Qwen 32B)**:
- Cost: $0 (electricity ~$0.10)
- Time: ~30-60 minutes (with RTX 4080)
- Quality: 75-80% pass rate

**Hybrid (Cloud for hard, Local for easy)**:
- 300 complex cases → Cloud: $1.35
- 700 simple cases → Local: $0
- **Total: $1.35 (70% savings)**
- Quality: 80-85% average pass rate

---

## Best Practices

### 1. Start with Cloud, Add Local Later

Validate your framework works with known-good models first:
1. Run with Claude/GPT-4 to establish baseline
2. Add local models for comparison
3. Identify which rules work well with local models
4. Optimize cost by routing appropriately

### 2. Use Right-Sized Models

- **Development**: 7B models (fast iteration)
- **Testing**: 16B models (good balance)
- **Production**: 32B models (best quality) or cloud APIs

### 3. Monitor GPU Usage

```bash
# Keep an eye on GPU memory
watch -n 1 nvidia-smi
```

Don't try to run models that exceed your VRAM.

### 4. Cache Results

The framework already saves results to JSON. Use this to avoid re-running:

```bash
# Generate report from existing results
python reporters/html_reporter.py results/results_20250112.json
```

### 5. Parallel Execution

Local models can handle more parallelism than APIs:

```bash
# Cloud models: Limited by rate limits
python evaluate.py --parallel 2

# Local models: Limited by GPU memory
python evaluate.py --parallel 4  # Or more if you have VRAM
```

---

## Next Steps

1. **Install Ollama**: Follow installation instructions above
2. **Pull a model**: Start with `qwen2.5-coder:7b` or `qwen2.5-coder:32b`
3. **Create adapter**: Copy the code from this guide
4. **Run test evaluation**: Try 10-20 test cases first
5. **Compare results**: Against cloud models to validate quality
6. **Scale up**: Once validated, run full evaluations

---

## Additional Resources

- **Ollama Documentation**: https://github.com/ollama/ollama
- **Ollama Model Library**: https://ollama.ai/library
- **Qwen 2.5 Coder**: https://ollama.ai/library/qwen2.5-coder
- **DeepSeek Coder**: https://ollama.ai/library/deepseek-coder-v2
- **Ollama Python SDK**: https://github.com/ollama/ollama-python

---

## FAQ

### Q: Which local model should I start with?

**A**: `qwen2.5-coder:7b` if you have 8GB VRAM, `qwen2.5-coder:32b` if you have 20GB+ VRAM.

### Q: Can I run Ollama on CPU?

**A**: Yes, but it's very slow. Stick to small models (1.3B-7B) or use cloud APIs instead.

### Q: How does local quality compare to cloud?

**A**: Local 32B models get ~10-20% lower pass rates than Claude/GPT-4. Still very useful for many tasks.

### Q: Can I fine-tune Ollama models?

**A**: Yes, but that's beyond this guide's scope. See Ollama fine-tuning documentation.

### Q: What if I don't have a GPU?

**A**: Use cloud APIs (Claude, GPT-4). Local models on CPU are too slow for practical use.

---

**Last Updated**: 2025-01-12
**Maintained By**: Konveyor AI Evaluation Framework Team
