"""
Question parser - extract structured question data from HTML content.

Supports multiple source formats via registered parsers.
"""
import re
import html
import logging
from dataclasses import dataclass, field
from typing import Optional
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


@dataclass
class ParsedQuestion:
    """Parsed question data structure"""
    content: str
    question_type: str = "single_choice"
    difficulty: str = "medium"
    options: list[dict] = field(default_factory=list)
    explanation: Optional[str] = None
    reference_url: Optional[str] = None
    tags: list[str] = field(default_factory=list)
    source: Optional[str] = None
    external_id: Optional[str] = None


class BaseParser:
    """Base parser class"""

    def can_parse(self, html_content: str, url: str = "") -> bool:
        raise NotImplementedError

    def parse(self, html_content: str, url: str = "") -> list[ParsedQuestion]:
        raise NotImplementedError


class GenericQuestionParser(BaseParser):
    """Generic parser for most exam question websites"""

    CONTAINER_SELECTORS = [
        "div.exam-question", "div.question-body", "div.question-text",
        "div.card-text", "article.question", "div.ques",
        ".exam-body .question", "#questionsList .question-item",
    ]

    def can_parse(self, html_content: str, url: str = "") -> bool:
        soup = BeautifulSoup(html_content, "html.parser")
        text = soup.get_text(" ", strip=True)[:2000].lower()
        keywords = ["question", "exam", "which of the", "select the", "what is", "which aws"]
        return any(kw in text for kw in keywords)

    def _clean_text(self, text: str) -> str:
        text = html.unescape(text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def _detect_type(self, options: list[dict]) -> str:
        correct_count = sum(1 for o in options if o.get("is_correct"))
        return "multi_choice" if correct_count > 1 else "single_choice"

    def _parse_question_block(self, block, url: str) -> Optional[ParsedQuestion]:
        soup = BeautifulSoup(str(block), "html.parser")

        # Extract question text
        question_el = (
            soup.select_one(".question-text, .q-text, .question-title, .ques-title")
            or soup.find("p")
            or soup.find("strong")
        )
        if not question_el:
            return None
        content = self._clean_text(question_el.get_text())
        if len(content) < 10:
            return None

        # Extract options
        option_items = soup.select(
            ".option-item, .choice-item, .answer-option, "
            "li.option, li.choice, div.option, "
            "p.option, span.option"
        )
        if not option_items:
            option_items = []
            for tag in soup.find_all(["p", "div", "li", "span"]):
                text = tag.get_text(strip=True)
                if re.match(r"^[A-D][.)]\s", text):
                    option_items.append(tag)

        options = []
        for opt in option_items:
            text = self._clean_text(opt.get_text())
            m = re.match(r"^([A-D])[.)\s]+(.+)", text)
            if m:
                key = m.group(1)
                option_text = m.group(2)
                is_correct = bool(
                    opt.select_one(".correct, .answer, .right-answer")
                    or any(mark in text for mark in ["[Correct]", "(Correct)", "(True)", "✓", "✅"])
                )
                options.append({"key": key, "content": option_text, "is_correct": is_correct})

        if not options:
            return None

        # Extract explanation
        explanation_el = (
            soup.select_one(".explanation, .answer-desc, .solution, .ques-explanation")
            or soup.find("blockquote")
        )
        explanation = self._clean_text(explanation_el.get_text()) if explanation_el else None

        # Extract tags
        tags = []
        for tag_el in soup.select(".tag, .badge, .topic, .category-label"):
            tag_text = self._clean_text(tag_el.get_text())
            if tag_text and len(tag_text) < 50:
                tags.append(tag_text)

        return ParsedQuestion(
            content=content,
            question_type=self._detect_type(options),
            difficulty="medium",
            options=options,
            explanation=explanation,
            reference_url=url,
            tags=tags,
        )

    def parse(self, html_content: str, url: str = "") -> list[ParsedQuestion]:
        soup = BeautifulSoup(html_content, "html.parser")
        questions = []

        # Strategy 1: Container selectors
        for selector in self.CONTAINER_SELECTORS:
            blocks = soup.select(selector)
            if blocks:
                for block in blocks:
                    q = self._parse_question_block(block, url)
                    if q:
                        questions.append(q)
                if questions:
                    break

        # Strategy 2: <dl> structure
        if not questions:
            for dl in soup.find_all("dl"):
                q = self._parse_question_block(dl, url)
                if q:
                    questions.append(q)

        # Strategy 3: <li> with question class
        if not questions:
            for li in soup.find_all("li", class_=re.compile(r"question|exam|item", re.I)):
                q = self._parse_question_block(li, url)
                if q:
                    questions.append(q)

        logger.info(f"Parser extracted {len(questions)} questions from {url}")
        return questions


class ExamTopicsParser(BaseParser):
    """Specialized parser for examtopics.com"""

    def can_parse(self, html_content: str, url: str = "") -> bool:
        return "examtopics.com" in url.lower()

    def parse(self, html_content: str, url: str = "") -> list[ParsedQuestion]:
        soup = BeautifulSoup(html_content, "html.parser")
        questions = []
        cards = soup.select("div.card")

        for idx, card in enumerate(cards):
            number_el = card.select_one(".card-header .question-number, .badge")
            ext_id = f"examtopics-{number_el.get_text(strip=True)}" if number_el else f"examtopics-{idx}"

            text_el = card.select_one(".card-text, .question-text, p:first-of-type")
            if not text_el:
                continue
            content = text_el.get_text(" ", strip=True)
            if len(content) < 10:
                continue

            options = []
            for li in card.select("ul.choices li, .choice-item, .option-item"):
                opt_text = li.get_text(" ", strip=True)
                m = re.match(r"^([A-D])[.)\s]+(.+)", opt_text)
                if m:
                    is_correct = "correct" in li.get("class", []) or bool(li.select_one(".correct, .vote-answer"))
                    options.append({"key": m.group(1), "content": m.group(2), "is_correct": is_correct})

            expl_el = card.select_one(".explanation, .comment, .answer-description")
            explanation = expl_el.get_text(" ", strip=True) if expl_el else None

            # Fallback: use most-voted answer as correct
            if not any(o["is_correct"] for o in options):
                most_voted = card.select_one(".most-voted-answer, .vote-answer")
                if most_voted:
                    vote_text = most_voted.get_text(strip=True)
                    m = re.match(r"([A-D])", vote_text)
                    if m:
                        for o in options:
                            if o["key"] == m.group(1):
                                o["is_correct"] = True

            if not options:
                continue

            correct_count = sum(1 for o in options if o["is_correct"])
            questions.append(ParsedQuestion(
                content=content,
                question_type="multi_choice" if correct_count > 1 else "single_choice",
                difficulty="medium",
                options=options,
                explanation=explanation,
                reference_url=url,
                external_id=ext_id,
            ))

        logger.info(f"ExamTopics parser: {len(questions)} questions from {url}")
        return questions


class ParserRegistry:
    """Parser registry - auto-selects the right parser"""

    def __init__(self):
        self._parsers: list[BaseParser] = [
            ExamTopicsParser(),
            GenericQuestionParser(),
        ]

    def register(self, parser: BaseParser):
        self._parsers.insert(0, parser)

    def parse(self, html_content: str, url: str = "") -> list[ParsedQuestion]:
        for parser in self._parsers:
            if parser.can_parse(html_content, url):
                return parser.parse(html_content, url)
        logger.warning(f"No parser found for {url}, using GenericQuestionParser")
        return GenericQuestionParser().parse(html_content, url)


parser_registry = ParserRegistry()
