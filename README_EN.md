# Video Analyzer Pro | Video Content Auditing & Smart Classification Tool

<p align="center">
  <a href="README.md">简体中文</a> | <a href="README_EN.md">English</a>
</p>

> **💡 Need Image Processing?** If you need to perform smart sorting, compliance auditing, and automated archiving of massive image collections, please use our sister project: [Image Analyzer Pro](https://github.com/Liu-Bot24/img_analyzer_pro)

Video Analyzer Pro is a high-performance video auditing and full-scenario classification tool based on Vision Large Language Models (VLM). Designed for massive video libraries, it fully automates "content understanding, compliance auditing, automatic classification, and renaming" of videos through highly customizable Prompt logic.

## 🌟 Why Choose It?

- **Industrial-Grade Auditing Accuracy**: Built-in "Visual Content Auditor" instructions accurately identify real-world physical conflicts, traffic disputes, explicit content, and various disturbing scenes, going far beyond simple keyword filtering.
- **Infinite Scenario Expansion**: **Core logic is fully Prompt-driven.** You can instantly turn it into a "Cat Behavior Analyst", "Traffic Violation Auditor", or "Short Video Topic Classifier" simply by modifying the configuration file.
- **Multi-Model Concurrency Matrix**: Supports mounting an infinite number of different (or the same) AI Model Endpoints in the configuration. The program automatically enables multi-threading based on the model list length, breaking through the rate limits (RPM/TPM) of a single API account for multiplied performance.
- **Adaptive Frame Extraction**: Pioneering dynamic stepping algorithm. Whether it's a 5-second short video or a 1-hour movie, the program automatically matches the optimal number of frames to extract, ensuring no key actions are missed while saving your Tokens.
- **Extreme Robustness**: Hot-swapping configuration (no restart required), CSV lock-protection with automatic retry, thread safety locks, and self-healing environment scripts (auto-installs Python/FFmpeg, Windows only).

## 📂 Application Scenarios

1.  **Safety & Compliance Auditing (Core Use Case)**: Automatically screen video libraries to accurately locate and sort out violent assaults, explicit content, or disturbing scenes.
2.  **Traffic Accident Analysis**: Accurately extract specific events such as conflicts, pulling, and collisions from massive dashcam footage using refined Prompts.
3.  **Asset Library Smart Sorting**: Define custom rules like "Natural Scenery, Character Interviews, Industrial Production" to let AI automatically sort messy asset libraries into corresponding folders by theme.
4.  **Digital Tag Management**: Automatically generate precise 15-character titles for each video and aggregate them into a CSV spreadsheet to build a searchable digital video archive.

## 🚀 Quick Start

### 1. Environment Preparation & API Recommendations
- Ensure the system is connected to the internet.
- Prepare an OpenAI-compatible API endpoint that supports Vision capabilities (e.g., [SiliconFlow](https://cloud.siliconflow.cn/i/My0p5Jgs)).
- **Performance Tips**: It is recommended to choose different model tiers in `config.yaml` based on budget and speed requirements, such as `THUDM/GLM-4.1V-9B-Thinking` (free tier supported), `Qwen/Qwen3-VL-32B-Instruct` (higher TPM), `GLM-4.6V`, `Qwen3-VL-30B-A3B`, etc. Please note that different billing models have different **TPM (Tokens Per Minute)** rate limits. For maximum processing speed, it's advised to purchase a dedicated AI model service.

### 2. Configuration & Running
1.  **Edit config.yaml**: Enter your API key and video directory.
2.  **Custom Categories (Optional)**: Modify or add any content you wish to identify under categories (e.g., pet species, action types, etc.).
3.  **Start the Program**:
    - **Windows Environment**: Double-click **run_analyzer.bat**, it will automatically check and deploy the Python/FFmpeg environment before starting the task.
    - **Mac / Linux Environment**: The core logic is fully cross-platform. First run `pip install -r requirements.txt`, then run `python main.py` in the terminal.

## ⚙️ Core Configuration Guide (`config.yaml`)

All core logic and parameters of this project are driven by `config.yaml`, supporting extreme customization:

### [API Core Connection]
| Parameter | Description |
| :--- | :--- |
| `api.key` | API access key (supports major platforms compatible with the OpenAI format). |
| `api.base_url` | Base URL for API requests. |
| `api.endpoints` | **[Core Feature]** Multi-model configuration list. The list contains `key`, `base_url`, `model`. The program will launch as many concurrent threads as there are nodes configured for asynchronous processing. |
| `api.timeout` | Maximum timeout for a single network request (seconds). Prevents hanging on large image transmissions. Recommended: 180s. |
| `api.max_retries` | Number of automatic retries after an interface request failure (e.g., network fluctuation/rate limiting). |
| `api.temperature` | Sampling temperature (0.0-1.0). Lower values (e.g., 0.1) keep classification outputs strict and deterministic. |
| `api.max_tokens` | Maximum Token length allowed for model generation. |

### [Video Preprocessing]
| Parameter | Description |
| :--- | :--- |
| `video.source_dir` | Directory containing the raw videos to be processed (direct pasting of Windows absolute paths is supported). |
| `video.dynamic_frames` | **Fully Customizable Dynamic Stepping**. Format like `[Duration Upper Limit(s), Frames to Extract]`, supports infinite steps. The program auto-calculates video duration and matches the optimal frames. |
| `video.max_dimension` | Upper limit for the long edge scaling of extracted images. Exceeding this pixel value will proportionally scale down the image. |
| `video.extensions` | Whitelist of video file extensions to be scanned (e.g., `.mp4`, `.avi`, etc.). |
| `video.auto_rename` | Switch: Whether to automatically physically rename files based on the "short title" generated by AI. |
| `video.keep_original_name` | **Renaming Strategy**: If `true`, generates `ShortTitle_OriginalFileName.mp4`; if `false`, only keeps `ShortTitle.mp4` (built-in logic prevents overwriting via auto-increment suffixes). |

### [Classification Auditing & Storage Rules]
| Parameter | Description |
| :--- | :--- |
| `categories` | **Fully Customizable Auditing Rule Library**. Contains any number of classification Keys you define (e.g., `violence`, `sex`, etc.), which will be sent to the AI as identification tags. |
| `path` | The target subdirectory where the video will be physically moved when the identification conclusion matches this class. |
| `desc` | **Visual Criteria Sent to AI**. Guides the AI to make accurate classifications through detailed and objective feature descriptions. |

### [System Operation Behavior]
| Parameter | Description |
| :--- | :--- |
| `system.concurrency` | The number of concurrent threads effective when the `api.endpoints` list is not configured. Default is 1, generally 2-4 is safer. |
| `system.csv_file` | The filename for the final recognition results summary spreadsheet. |
| `system.log_file` | The filename for the detailed operation log during execution. |
| `system.prompt_template` | **Core Brain**: The Prompt template sent to the AI, which automatically extracts the `desc` rules above for dynamic injection. |

## 🛠️ Technical Guarantees

- **Resumable Processing**: Supports restarting after interruption, automatically skipping processed files.
- **Collision Protection**: If conflicts occur during renaming, auto-increment suffixes are applied to absolutely prevent file overwriting.
- **Privacy Protection**: Only visual content descriptions are sent to the API, automatically stripping local physical paths.

## 📄 Open Source License
[MIT License](LICENSE)
