FROM python:3.11-slim

# Install uv
RUN pip install uv

# Set working directory
WORKDIR /app

# Copy project files
COPY pyproject.toml .

# Install dependencies using uv
RUN uv pip install --system --no-cache-dir -e .

# Copy source code after installing dependencies (for better caching)
COPY src/ ./src/
COPY templates/ ./templates/

# Create output directory
RUN mkdir -p output

# Run the script
CMD ["python", "src/generate_calendars.py"]
