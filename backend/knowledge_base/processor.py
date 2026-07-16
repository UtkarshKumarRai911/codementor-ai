"""Document processor for chunking editorials while respecting code blocks."""

import logging
import re
from typing import Any

from .scraper import Editorial

logger = logging.getLogger(__name__)


class EditorialProcessor:
    """Process editorials into chunks suitable for vector store indexing.

    Implements intelligent chunking that respects code blocks and
    section boundaries to maintain context coherence.
    """

    def __init__(
        self,
        max_chunk_size: int = 1000,
        chunk_overlap: int = 100,
        min_chunk_size: int = 100,
    ):
        """Initialize the processor.

        Args:
            max_chunk_size: Maximum characters per chunk
            chunk_overlap: Number of overlapping characters between chunks
            min_chunk_size: Minimum characters for a valid chunk
        """
        self.max_chunk_size = max_chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size

    def process_editorial(self, editorial: Editorial) -> list[dict[str, Any]]:
        """Process a single editorial into chunks.

        Args:
            editorial: Editorial object to process

        Returns:
            List of chunk dictionaries with content and metadata
        """
        full_text = editorial.full_text
        sections = self._split_into_sections(full_text)

        chunks = []
        for section in sections:
            section_chunks = self._chunk_section(section)
            for i, chunk_text in enumerate(section_chunks):
                if len(chunk_text.strip()) >= self.min_chunk_size:
                    chunks.append({
                        "content": chunk_text,
                        "metadata": {
                            "source": editorial.source or "sample",
                            "title": editorial.title,
                            "problem_id": editorial.problem_id,
                            "difficulty": editorial.difficulty,
                            "tags": ",".join(editorial.tags),
                            "chunk_index": i,
                            "section": section[:50],
                        },
                    })

        logger.debug(f"Processed '{editorial.title}' into {len(chunks)} chunks")
        return chunks

    def process_batch(self, editorials: list[Editorial]) -> list[dict[str, Any]]:
        """Process a batch of editorials.

        Args:
            editorials: List of Editorial objects

        Returns:
            List of all chunk dictionaries
        """
        all_chunks = []
        for editorial in editorials:
            chunks = self.process_editorial(editorial)
            all_chunks.extend(chunks)

        logger.info(f"Processed {len(editorials)} editorials into {len(all_chunks)} chunks")
        return all_chunks

    def _split_into_sections(self, text: str) -> list[str]:
        """Split text into sections based on headers and logical boundaries.

        Args:
            text: Full text to split

        Returns:
            List of section strings
        """
        # Split on markdown headers
        sections = re.split(r"\n(?=#{1,3}\s)", text)
        return [s.strip() for s in sections if s.strip()]

    def _chunk_section(self, section: str) -> list[str]:
        """Chunk a section while respecting code blocks.

        Args:
            section: Section text to chunk

        Returns:
            List of chunk strings
        """
        # If section is small enough, return as-is
        if len(section) <= self.max_chunk_size:
            return [section]

        chunks = []
        # Identify code blocks
        code_block_pattern = re.compile(r"```[\s\S]*?```", re.MULTILINE)
        code_blocks = list(code_block_pattern.finditer(section))

        if not code_blocks:
            # No code blocks - simple paragraph splitting
            return self._split_by_paragraphs(section)

        # Split around code blocks
        last_end = 0
        for match in code_blocks:
            # Text before code block
            pre_text = section[last_end:match.start()].strip()
            if pre_text:
                chunks.extend(self._split_by_paragraphs(pre_text))

            # Code block itself (keep intact if possible)
            code_block = match.group()
            if len(code_block) <= self.max_chunk_size:
                chunks.append(code_block)
            else:
                # Large code block - split by lines
                chunks.extend(self._split_code_block(code_block))

            last_end = match.end()

        # Remaining text after last code block
        remaining = section[last_end:].strip()
        if remaining:
            chunks.extend(self._split_by_paragraphs(remaining))

        return chunks

    def _split_by_paragraphs(self, text: str) -> list[str]:
        """Split text by paragraphs with overlap.

        Args:
            text: Text to split

        Returns:
            List of paragraph chunks
        """
        if len(text) <= self.max_chunk_size:
            return [text]

        paragraphs = text.split("\n\n")
        chunks = []
        current_chunk = ""

        for para in paragraphs:
            if len(current_chunk) + len(para) + 2 <= self.max_chunk_size:
                current_chunk += ("\n\n" + para if current_chunk else para)
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                # Start new chunk with overlap
                if self.chunk_overlap > 0 and current_chunk:
                    overlap = current_chunk[-self.chunk_overlap:]
                    current_chunk = overlap + "\n\n" + para
                else:
                    current_chunk = para

        if current_chunk:
            chunks.append(current_chunk)

        return chunks

    def _split_code_block(self, code_block: str) -> list[str]:
        """Split a large code block by function/class boundaries.

        Args:
            code_block: Code block string including ``` delimiters

        Returns:
            List of code chunk strings
        """
        # Remove delimiters for processing
        lines = code_block.split("\n")
        lang_line = lines[0] if lines else "```"
        code_lines = lines[1:-1] if len(lines) > 2 else lines

        chunks = []
        current_lines = []
        current_size = 0

        for line in code_lines:
            if current_size + len(line) + 1 > self.max_chunk_size - 10:
                if current_lines:
                    chunk = lang_line + "\n" + "\n".join(current_lines) + "\n```"
                    chunks.append(chunk)
                current_lines = [line]
                current_size = len(line)
            else:
                current_lines.append(line)
                current_size += len(line) + 1

        if current_lines:
            chunk = lang_line + "\n" + "\n".join(current_lines) + "\n```"
            chunks.append(chunk)

        return chunks
