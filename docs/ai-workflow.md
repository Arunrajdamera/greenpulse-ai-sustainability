# AI, RAG and agentic workflow

1. **Resource Analysis Agent** groups simulated records and produces structured findings.
2. **Knowledge Retrieval Agent** loads Markdown knowledge files, splits paragraphs into chunks and scores word overlap with the question or finding.
3. **Recommendation Agent** maps a finding to a practical, category-appropriate action and attaches a retrieved source when available.
4. **Responsible AI Check** adds a decision-support warning and keeps status as `Suggested / Pending Review`.

For chat, retrieved chunks are composed into a clearly marked **Demo AI Mode** response and source filenames are shown. If no chunk matches, the assistant says so rather than fabricating information. An optional real provider configuration is reserved through environment variables, but is not claimed or required in this prototype.
