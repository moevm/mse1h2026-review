Return ONLY a valid JSON array of inline review comments.

Format:

[
  {
    "file": "<relative_file_path>",
    "line": <line_number>,
    "message": "<короткое сообщение-ревью на русском языке, содержащее ошибку или исправление>",
    "suggestion": "<replacement code block, without markdown, or null if not applicable>"
    "error_type": "<тип ошибки, возможные типы перечислены далее>",
    "error_topic": "<тема ошибки, возможные темы перечислены далее>"
  }
]


Rules:

"file" must exactly match the file path in the diff.
"line" must be an integer from the new version of the file.
"message" must be a short, clear, and actionable explanation(1-3 sentences). Только на русском языке
"suggestion" must contain ONLY the code to replace the line(s), without markdown or comments.
"error_type" must be one from these: Syntax Error, Logical Error, Performance Error, Style Error, Security Error, Memory Error
"error_topic" must be one from these: Algorithms, Databases, File Operations, Testing, Input/Output, Optimization, Logging, Documentation, Dependencies
Use correct indentation from the file.
If no concrete replacement is appropriate, set "suggestion" to null.
Do not include anything outside the JSON array.
If no issues are found, return [].

Не более 5-7 комментариев.


