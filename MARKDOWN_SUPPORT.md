# Markdown Formatting Support

The chat UI now supports **full markdown rendering** with syntax highlighting for code blocks.

## Supported Features

### 1. **Headings**
```markdown
# Heading 1
## Heading 2
### Heading 3
```

### 2. **Text Formatting**
```markdown
**Bold text**
*Italic text*
~~Strikethrough~~
```

### 3. **Lists**

**Unordered:**
```markdown
- Item 1
- Item 2
  - Nested item
```

**Ordered:**
```markdown
1. First item
2. Second item
3. Third item
```

### 4. **Code**

**Inline code:**
```markdown
Use `inline code` for single line code
```

**Code blocks with syntax highlighting:**
````markdown
```python
def hello_world():
    print("Hello, World!")
```

```javascript
const greeting = () => {
  console.log("Hello, World!");
}
```

```bash
npm install
python server.py
```
````

**Supported languages:**
- Python
- JavaScript/TypeScript
- Java
- C/C++
- Go
- Rust
- Ruby
- PHP
- SQL
- Bash/Shell
- HTML/CSS
- JSON
- YAML
- And many more!

### 5. **Links**
```markdown
[Link text](https://example.com)
```

### 6. **Blockquotes**
```markdown
> This is a blockquote
> It can span multiple lines
```

### 7. **Tables**
```markdown
| Header 1 | Header 2 | Header 3 |
|----------|----------|----------|
| Cell 1   | Cell 2   | Cell 3   |
| Cell 4   | Cell 5   | Cell 6   |
```

### 8. **Horizontal Rules**
```markdown
---
```

### 9. **Images**
```markdown
![Alt text](image-url.jpg)
```

## Example AI Responses

### Research Response
```
## What is Docker?

**Docker** is a platform for developing, shipping, and running applications in containers.

### Key Benefits:
- Consistent environments
- Fast deployment
- Resource efficiency
- Scalability

> Docker containers are lightweight and portable, making them ideal for modern applications.
```

### Code Response
````
## FastAPI Example

Here's a simple REST API:

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/items/{item_id}")
async def read_item(item_id: int):
    return {"item_id": item_id}
```

### Features:
- Automatic API documentation
- Fast performance
- Type hints support
````

### Writing Response
```
# Introduction to Python

Python is a **high-level**, *interpreted* programming language known for its simplicity.

## Why Learn Python?

1. Easy to learn
2. Versatile applications
3. Large community
4. Extensive libraries

### Popular Use Cases:
- Web development
- Data science
- Machine learning
- Automation

> "Python is the second best language for everything." - Anonymous
```

## Styling

The chat UI automatically styles:
- ✅ **Code blocks** with dark theme syntax highlighting
- ✅ **Inline code** with light background
- ✅ **Headings** with different sizes and colors
- ✅ **Lists** with proper indentation
- ✅ **Links** with hover effects
- ✅ **Blockquotes** with left border
- ✅ **Tables** with borders and headers

## Tips for AI Responses

When the AI generates responses, it can freely use:
- Markdown formatting for structure
- Code blocks with language specification
- Tables for comparisons
- Lists for organized information
- Headings for sections

The frontend will automatically render everything beautifully! ✨
