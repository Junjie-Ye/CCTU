# CCTU
## CCTU: A Benchmark for Tool Use under Complex Constraints

> Code for the paper [CCTU: A Benchmark for Tool Use under Complex Constraints](https://arxiv.org/abs/2603.15309)

Junjie Ye

jjye23@m.fudan.edu.cn

Mar. 17, 2026

## Introduction

<div>
<center>
<img src=asset/ctu.png>
</div>

<div style="text-align: justify;">
Solving problems through tool use under explicit constraints constitutes a highly challenging yet unavoidable scenario for large language models (LLMs), requiring capabilities such as function calling, instruction following, and self-refinement. However, progress has been hindered by the absence of dedicated evaluations. To address this, we introduce CCTU, a benchmark for evaluating LLM tool use under complex constraints. CCTU is grounded in a taxonomy of 12 constraint categories spanning four dimensions (i.e., resource, behavior, toolset, and response). The benchmark comprises 200 carefully curated and challenging test cases across diverse tool-use scenarios, each involving an average of seven constraint types and an average prompt length exceeding 4,700 tokens. To enable reliable evaluation, we develop an executable constraint validation module that performs step-level validation and enforces compliance during multi-turn interactions between models and their environments. We evaluate nine state-of-the-art LLMs in both thinking and non-thinking modes. Results indicate that when strict adherence to all constraints is required, no model achieves a task completion rate above 20%. Further analysis reveals that models violate constraints in over 50% of cases, particularly in the resource and response dimensions. Moreover, LLMs demonstrate limited capacity for self-refinement even after receiving detailed feedback on constraint violations, highlighting a critical bottleneck in the development of robust tool-use agents.
</div>

## What's New

- **[2026/03/17]** Release the [data](https://huggingface.co/datasets/Junjie-Ye/CCTU/) and code for SceIF.
- **[2026/03/17]** Paper available on [Arxiv](https://arxiv.org/abs/xxxx.xxxxx).

## Leaderboard

### Thinking Mode

|Models| Single-Hop | Single-Hop| Parallel Single-Hop | Parallel Single-Hop | Multi-Hop| Multi-Hop | Parallel Multi-Hop| Parallel Multi-Hop | Overall | Overall |
|---|---|---|---|---|---|---|---|---|---|---|
||*SR* |*PSR*|*SR* |*PSR*|*SR* |*PSR*|*SR* |*PSR*|*SR* |*PSR*|
| GPT-5.2 | 32.67 | **24.67** | 24.67 | **17.33** | 25.33 | 20.67 | 15.33 | 10.00 | 24.50 | **18.17** |
| GPT-5.1 | 25.33 | 20.00 | 20.67 | 16.00 | 22.67 | 20.67 | 22.67 | 9.33 | 22.83 | 16.50 |
| Claude Opus 4.6 | **34.67** | 10.00 | **30.67** | 13.33 | **38.67** | **23.33** | **32.67** | **12.67** | **34.17** | 14.83 |
| Seed-2.0-Pro | 22.67 | 19.33 | 20.67 | 12.67 | 22.67 | 18.67 | 15.33 | 8.67 | 20.33 | 14.83 |
| Qwen3.5-Plus | 20.67 | 5.33 | 23.33 | 8.00 | 32.00 | 21.33 | 23.33 | 8.00 | 24.83 | 10.67 |
| Gemini 3 Pro | 23.33 | 12.00 | 28.00 | 16.00 | 14.67 | 11.33 | 11.33 | 2.67 | 19.33 | 10.50 |
| DeepSeek-V3.2 | 15.33 | 6.67 | 22.67 | 12.00 | 26.00 | 16.67 | 8.00 | 0.67 | 18.00 | 9.00 |
| OpenAI o3 | 22.67 | 17.33 | 7.33 | 4.00 | 13.33 | 10.00 | 4.00 | 1.33 | 11.83 | 8.17 |
| Kimi K2.5 | 22.67 | 4.67 | 26.00 | 10.67 | 20.00 | 10.67 | 16.67 | 4.67 | 21.33 | 7.67 |

### Non-Thinking Mode

|Models| Single-Hop | Single-Hop| Parallel Single-Hop | Parallel Single-Hop | Multi-Hop| Multi-Hop | Parallel Multi-Hop| Parallel Multi-Hop | Overall | Overall |
|---|---|---|---|---|---|---|---|---|---|---|
||*SR* |*PSR*|*SR* |*PSR*|*SR* |*PSR*|*SR* |*PSR*|*SR* |*PSR*|
| GPT-5.2 | 28.00 | **24.00** | 19.33 | 15.33 | 17.33 | 14.00 | 16.67 | 10.67 | 20.33 | **16.00** |
| Claude Opus 4.6 | **38.00** | 12.00 | **29.33** | 13.33 | **38.00** | **23.33** | **32.67** | **13.33** | **34.50** | 15.50 |
| GPT-5.1 | 22.67 | 19.33 | 19.33 | **16.67** | 16.67 | 14.00 | 14.00 | 6.67 | 18.17 | 14.17 |
| Kimi K2.5 | 19.33 | 6.67 | 29.33 | 14.00 | 25.33 | 15.33 | 16.67 | 6.67 | 22.67 | 10.67 |
| Gemini 3 Pro | 22.67 | 12.67 | 26.67 | 14.67 | 16.00 | 11.33 | 10.67 | 2.00 | 19.00 | 10.17 |
| Seed-2.0-Pro | 20.00 | 13.33 | 20.00 | 10.00 | 20.00 | 13.33 | 12.67 | 3.33 | 18.17 | 10.00 |
| OpenAI o3 | 24.00 | 18.67 | 9.33 | 4.67 | 10.67 | 7.33 | 2.00 | 1.33 | 11.50 | 8.00 |
| Qwen3.5-Plus | 20.67 | 4.00 | 20.00 | 6.67 | 28.67 | 14.67 | 16.00 | 6.67 | 21.33 | 7.00 |
| DeepSeek-V3.2 | 20.00 | 6.67 | 17.33 | 6.00 | 20.67 | 12.00 | 10.00 | 1.33 | 17.00 | 6.50 |

## Usage

### Requirement

- Python 3.8+

- Run the command to install the packages required.
  ```bash
  pip install -r requirements.txt
  ```

### Evaluation for LLMs

- Download [input_data.jsonl](https://huggingface.co/datasets/Junjie-Ye/CCTU) and put it under the `data` folder.

- Run the command to evaluate various LLMs.
    ```bash
    bash evaluation.sh --model $MODEL --user $USER --api_key $API_KEY --base_url $BASE_URL --output_dir $OUTPUT_DIR [--thinking]
    ```

## License

The code is licensed under the [Apache License 2.0](LICENSE).

## Citation

If you find this project useful in your research, please cite:

```bibtex
@article{CCTU,
  title        = {CCTU: A Benchmark for Tool Use under Complex Constraints}, 
  author       = {Junjie Ye and Guoqiang Zhang and Wenjie Fu and Tao Gui and Qi Zhang and Xuanjing Huang},
  journal      = {CoRR},
  volume       = {abs/2603.15309},
  year         = {2026},
  url          = {https://doi.org/10.48550/arXiv.2603.15309},
  doi          = {10.48550/ARXIV.2603.15309},
  eprinttype    = {arXiv},
  eprint       = {2603.15309}
}
```
