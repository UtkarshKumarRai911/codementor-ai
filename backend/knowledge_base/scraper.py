"""Scraper and data loader for competitive programming editorials."""

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


@dataclass
class Editorial:
    """Represents a competitive programming editorial."""

    title: str
    problem_id: str
    difficulty: str
    tags: list[str] = field(default_factory=list)
    problem_statement: str = ""
    approach: str = ""
    solution_code: str = ""
    complexity_analysis: str = ""
    source: str = ""
    url: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "title": self.title,
            "problem_id": self.problem_id,
            "difficulty": self.difficulty,
            "tags": self.tags,
            "problem_statement": self.problem_statement,
            "approach": self.approach,
            "solution_code": self.solution_code,
            "complexity_analysis": self.complexity_analysis,
            "source": self.source,
            "url": self.url,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Editorial":
        """Create an Editorial from a dictionary."""
        return cls(
            title=data.get("title", ""),
            problem_id=data.get("problem_id", ""),
            difficulty=data.get("difficulty", ""),
            tags=data.get("tags", []),
            problem_statement=data.get("problem_statement", ""),
            approach=data.get("approach", ""),
            solution_code=data.get("solution_code", ""),
            complexity_analysis=data.get("complexity_analysis", ""),
            source=data.get("source", ""),
            url=data.get("url", ""),
        )

    @property
    def full_text(self) -> str:
        """Get the full text representation for indexing."""
        parts = [
            f"# {self.title}",
            f"Difficulty: {self.difficulty}",
            f"Tags: {', '.join(self.tags)}",
        ]
        if self.problem_statement:
            parts.append(f"\n## Problem\n{self.problem_statement}")
        if self.approach:
            parts.append(f"\n## Approach\n{self.approach}")
        if self.solution_code:
            parts.append(f"\n## Solution Code\n```\n{self.solution_code}\n```")
        if self.complexity_analysis:
            parts.append(f"\n## Complexity Analysis\n{self.complexity_analysis}")
        return "\n".join(parts)


class CodeforcesEditorialScraper:
    """Scraper for Codeforces editorial pages."""

    BASE_URL = "https://codeforces.com"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "CodeMentor-AI/1.0 (Educational Purpose)"
        })

    def scrape_editorial(self, contest_id: int, problem_index: str) -> Editorial | None:
        """Scrape a single editorial from Codeforces.

        Args:
            contest_id: Codeforces contest ID
            problem_index: Problem index (A, B, C, etc.)

        Returns:
            Editorial object or None if scraping fails
        """
        url = f"{self.BASE_URL}/blog/entry/{contest_id}"
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            content = soup.find("div", class_="ttypography")

            if not content:
                logger.warning(f"No editorial content found for contest {contest_id}")
                return None

            return Editorial(
                title=f"Contest {contest_id} - Problem {problem_index}",
                problem_id=f"CF{contest_id}{problem_index}",
                difficulty="Unknown",
                source="Codeforces",
                url=url,
                approach=content.get_text(strip=True)[:2000],
            )

        except requests.RequestException as e:
            logger.error(f"Failed to scrape editorial: {e}")
            return None


class EditorialDataLoader:
    """Load editorial data from local JSON files."""

    def __init__(self, data_dir: str | Path | None = None):
        if data_dir is None:
            self.data_dir = Path(__file__).parent / "data"
        else:
            self.data_dir = Path(data_dir)

    def load_sample_editorials(self) -> list[Editorial]:
        """Load sample editorials from the data directory.

        Returns:
            List of Editorial objects
        """
        sample_file = self.data_dir / "sample_editorials.json"

        if not sample_file.exists():
            logger.warning(f"Sample editorials file not found: {sample_file}")
            return []

        try:
            with open(sample_file, "r") as f:
                data = json.load(f)

            editorials = [Editorial.from_dict(item) for item in data]
            logger.info(f"Loaded {len(editorials)} sample editorials")
            return editorials

        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to load sample editorials: {e}")
            return []

    def load_all(self) -> list[Editorial]:
        """Load all available editorials.

        Returns:
            List of all Editorial objects
        """
        all_editorials = []

        # Load from all JSON files in data directory
        if self.data_dir.exists():
            for json_file in self.data_dir.glob("*.json"):
                try:
                    with open(json_file, "r") as f:
                        data = json.load(f)
                    if isinstance(data, list):
                        all_editorials.extend(Editorial.from_dict(item) for item in data)
                except (json.JSONDecodeError, IOError) as e:
                    logger.error(f"Failed to load {json_file}: {e}")

        logger.info(f"Loaded {len(all_editorials)} total editorials")
        return all_editorials
