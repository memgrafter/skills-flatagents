---
url: https://simonwillison.net/2024/Dec/19/one-shot-python-tools/
title: "Building Python tools with a one-shot prompt using uv run and Claude Projects"
scraped_at: 2026-01-30T17:09:42.741567+00:00
word_count: 853
raw_file: 2026-01-30_building-python-tools-with-a-one-shot-prompt-using-uv-run-an.txt
---

# Summary of "Building Python tools with a one-shot prompt using uv run and Claude Projects"

This article discusses the author's experience in creating Python utilities using a one-shot prompt approach with Claude Projects and the `uv run` tool. The author shares specific examples of how to leverage these tools for efficient script generation and execution.

## Key Points

- **One-Shot Prompt Definition**: The term refers to a prompt that produces the complete desired result on the first attempt.
  
- **Example of Tool Creation**:
  - The author faced an issue with accessing a file on Amazon S3 and prompted Claude to generate a Python CLI tool using Click and boto3.
  - The generated script helped debug the 404 error for the S3 URL.
  - Command to run the script: 
    ```bash
    uv run debug_s3_access.py https://test-public-bucket-simonw.s3.us-east-1.amazonaws.com/0f550b7b28264d7ea2b3d360e3381a95.jpg
    ```

- **Inline Dependencies**:
  - The script includes a magic comment for inline dependencies, allowing `uv run` to create a temporary virtual environment automatically.
  - Example comment for dependencies:
    ```python
    # /// script # requires-python = ">=3.12" # dependencies = [ # "click", # "boto3", # "urllib3", # "rich", # ] # ///
    ```

- **Running Scripts from URLs**: Users can execute scripts directly from URLs, provided they trust the source.

- **Custom Instructions for Claude Projects**:
  - The author has set up a Claude Project with specific instructions to guide the model in generating Python tools that utilize inline dependencies effectively.
  - Example prompt for generating a Starlette web app to strip HTML tags using BeautifulSoup.

- **Custom Instructions for HTML/JavaScript Tools**: Similar custom instructions are used for creating single-page HTML and JavaScript tools, emphasizing minimal dependencies and specific coding styles.

## Notable Takeaways

- The integration of Claude Projects with `uv run` allows for rapid development of Python tools with minimal setup.
- Custom instructions can enhance the capabilities of LLMs, enabling them to produce code that adheres to specific patterns and requirements.
- This approach significantly streamlines the process of creating functional scripts and applications.

## Action Items

- Explore using `uv run` for your own Python projects to simplify dependency management.
- Consider setting up custom instructions in Claude Projects to tailor the output to your specific needs.
- Experiment with generating scripts for common tasks to improve efficiency in your workflow.