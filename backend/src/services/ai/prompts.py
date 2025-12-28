"""
Prompt Templates for AI-Powered Learning Document Generation.

This module provides structured prompt templates for generating 7-chapter
educational content via Google Gemini API. All prompts are designed to
produce beginner-friendly explanations following the platform constitution.

Requirements:
- FR-026 through FR-034: 7-chapter document structure
- FR-035: Explanations for zero programming knowledge
- FR-036: Technical terms explained with everyday language
- FR-037: Real-life analogies for abstract concepts

Usage:
    from backend.src.services.ai.prompts import PromptBuilder

    builder = PromptBuilder(
        code="def hello(): print('Hello')",
        language="Python",
        filename="hello.py"
    )
    system_instruction = builder.get_system_instruction()
    full_prompt = builder.build_document_prompt()
"""

from dataclasses import dataclass
from typing import Any


# System instruction for all educational content generation (Korean)
SYSTEM_INSTRUCTION_DOCUMENT = """당신은 프로그래밍 지식이 전혀 없는 완전 초보자를 위한 교육 콘텐츠를 만드는 전문 프로그래밍 강사입니다.

절대 규칙:
1. 독자가 프로그래밍 개념을 전혀 모른다고 가정하세요
2. 기술 용어를 사용하기 전에 반드시 일상 언어로 먼저 설명하세요
3. 추상적인 개념에는 반드시 실생활 비유를 포함하세요
4. 짧고 간단한 문장을 사용하세요 (중학생 수준의 읽기 난이도)
5. 전문 용어를 피하고, 꼭 써야 한다면 즉시 쉬운 말로 설명하세요

대상 독자:
- 코드를 단 한 줄도 작성해본 적 없는 사람
- AI로 코드를 생성했지만 그게 무엇을 하는지 이해하지 못하는 사람
- 단순히 복사-붙여넣기가 아니라 진정으로 이해하고 싶어하는 호기심 많은 학습자

교수 스타일:
- 격려하고 인내심을 가지세요
- 작은 성취도 축하하고 "왜 이것이 중요한지" 설명하세요
- 친숙한 실생활 예시를 사용하세요 (요리, 블록 쌓기, 일상 물건 등)
- 복잡한 아이디어를 작고 소화하기 쉬운 조각으로 나누세요

언어:
- 모든 설명은 한국어로 작성하세요
- 코드 주석도 한국어로 작성해도 됩니다
- 따뜻하고 친근하게, 마치 프로그래밍을 처음 접하는 똑똑한 친구에게 설명하듯이
"""

SYSTEM_INSTRUCTION_PRACTICE = """당신은 완전 초보자를 위한 연습 문제를 만드는 인내심 있는 프로그래밍 튜터입니다.

규칙:
1. 문제는 반드시 학습 문서에 있는 개념만으로 풀 수 있어야 합니다
2. 난이도를 점진적으로 높이세요 (따라하기 → 새로 만들기)
3. 정답을 바로 알려주지 않고 방향을 안내하는 힌트를 제공하세요
4. 모범 답안은 코드만 보여주지 말고 왜 그렇게 했는지 설명하세요

문제 유형 (난이도 순서):
1. 따라하기: 정확히 같은 코드를 타이핑해서 손에 익히기
2. 빈칸 채우기: 작동하는 코드의 빈 부분 완성하기
3. 코드 수정: 기존 코드를 약간 다르게 동작하도록 변경하기
4. 디버그: 의도적으로 넣은 오류 찾아서 고치기
5. 새로 만들기: 배운 개념을 사용해서 새 코드 작성하기

언어:
- 모든 설명과 문제는 한국어로 작성하세요
"""

SYSTEM_INSTRUCTION_QA = """당신은 완전 초보자의 질문에 답변하는 인내심 있는 프로그래밍 튜터입니다.

규칙:
1. 먼저 간단하고 직접적으로 답한 후 자세히 설명하세요
2. 도움이 될 때는 항상 실생활 비유를 제공하세요
3. 코드를 언급할 때는 구체적인 줄 번호를 말하세요
4. 더 알아보면 좋을 관련 개념을 제안하세요
5. 격려하세요 - 바보 같은 질문은 없습니다

답변 형식:
1. 직접적인 답변 (1-2문장)
2. 비유를 포함한 쉬운 설명
3. 관련 코드 예시 (필요한 경우)
4. 더 알아볼 관련 개념

언어:
- 모든 답변은 한국어로 작성하세요
"""


@dataclass
class PromptBuilder:
    """
    Builder for constructing AI prompts for document generation.

    Attributes:
        code: The source code to analyze and explain
        language: Programming language (e.g., "Python", "JavaScript")
        filename: Optional original filename for context
        additional_context: Optional extra context about the code
        file_structure: Optional folder structure for multi-file uploads
    """

    code: str
    language: str
    filename: str | None = None
    additional_context: str | None = None
    file_structure: dict[str, Any] | None = None

    def get_system_instruction(self) -> str:
        """Get the system instruction for document generation."""
        return SYSTEM_INSTRUCTION_DOCUMENT

    def build_document_prompt(self) -> str:
        """
        Build the complete prompt for 7-chapter document generation.

        Returns:
            str: The formatted prompt for Gemini API
        """
        file_context = f" (파일명: '{self.filename}')" if self.filename else ""
        folder_info = self._format_folder_structure() if self.file_structure else ""
        extra_context = f"\n\n추가 정보:\n{self.additional_context}" if self.additional_context else ""

        return f"""다음 {self.language} 코드{file_context}를 분석하고 완전 초보자를 위한 7장 구성의 학습 문서를 만들어주세요.

{folder_info}

## 소스 코드

```{self.language.lower()}
{self.code}
```
{extra_context}

## 작성 과제

아래의 정확한 구조를 따라 7장의 학습 문서를 생성하세요. 각 장에는 반드시 지켜야 할 요구사항이 있습니다.

---

### 1장: 이 코드가 하는 일 (요약)
**요구사항:**
- 이 코드가 무엇을 하는지 한 문장으로 설명하세요
- 기술 용어 없이 일상적인 말로 쓰세요
- 완전 초보자가 이 문장을 이해할 수 있어야 합니다
- "어떻게"가 아닌 "무엇을"에 초점을 맞추세요

**예시:**
"이 코드는 두 숫자를 받아서 그 합을 알려주는 계산기 같은 것입니다."

---

### 2장: 시작하기 전에 (사전 지식)
**요구사항:**
- 이 코드를 이해하는 데 필요한 가장 중요한 개념 5개를 나열하세요
- 각 개념에 대해 다음을 제공하세요:
  1. **이름**: 개념 이름 (예: "변수")
  2. **쉬운 설명**: 일상 언어로 1-2문장 설명
  3. **실생활 비유**: 친숙한 것과 비교
  4. **코드 예시**: 이 개념만 보여주는 간단한 예시
  5. **활용 사례**: 실제 프로그램에서 어디에 쓰이는지

**최대 5개 개념만.** 가장 핵심적인 것을 선택하세요.

---

### 3장: 코드 구조 (시각적 개요)
**요구사항:**
- 실행 흐름을 보여주는 ASCII 또는 Mermaid 다이어그램을 만드세요
- 여러 파일인 경우 파일 구조를 분석하세요
- 서로 다른 부분이 어떻게 연결되는지 보여주세요
- 각 부분에 목적을 표시하세요

**포함할 내용:**
1. 시각적 흐름도 (ASCII 아트 또는 Mermaid)
2. 파일/섹션별 설명
3. 각 부분이 어떻게 함께 작동하는지

---

### 4장: 줄별 설명
**요구사항:**
- 각 중요한 줄 또는 코드 블록을 설명하세요
- 각 줄/블록에 대해 다음을 제공하세요:
  1. **줄 번호**: 어떤 줄인지 (예: "1-3줄")
  2. **코드**: 설명하는 실제 코드
  3. **하는 일**: 무슨 기능인지 간단한 설명
  4. **문법 분석**: 각 기호와 키워드 설명
  5. **실생활 비유**: 일상 상황과 비교
  6. **다른 방법**: 같은 것을 다르게 쓰는 방법
  7. **주의사항**: 흔한 실수나 팁

---

### 5장: 실행 과정 (실행 흐름)
**요구사항:**
- 코드가 단계별로 어떻게 실행되는지 시뮬레이션하세요
- 프로그램을 통해 데이터가 어떻게 흐르는지 보여주세요
- 각 단계마다 다음을 표시하세요:
  1. **단계 번호**
  2. **일어나는 일**: 쉬운 말로 설명
  3. **현재 값**: 이 시점에 변수들이 가진 값
  4. **왜 중요한지**: 이 단계의 목적

**택배가 배송 시스템을 통과하는 것을 추적하는 것처럼 생각하세요.**

---

### 6장: 배운 핵심 개념
**요구사항:**
- 이 코드에서 배운 핵심 프로그래밍 개념을 정리하세요
- 각 개념에 대해:
  1. **무엇인지**: 쉬운 말로 정의
  2. **왜 쓰는지**: 어떤 문제를 해결하는지
  3. **어디에 쓰이는지**: 실제 활용 사례
  4. **이 코드에서**: 분석한 코드에서 어떻게 나타나는지

---

### 7장: 흔한 실수 피하기
**요구사항:**
- 이런 종류의 코드에서 초보자가 자주 하는 실수 3-5개를 나열하세요
- 각 실수에 대해:
  1. **실수 내용**: 초보자가 자주 하는 잘못
  2. **잘못된 코드**: 틀린 코드 예시
  3. **올바른 코드**: 수정된 버전
  4. **왜 중요한지**: 이 실수의 결과
  5. **고치는 방법**: 수정하고 예방하는 단계

---

## 출력 형식

다음 정확한 구조의 유효한 JSON 객체로 응답하세요:

```json
{{
  "chapter1": {{
    "title": "이 코드가 하는 일",
    "summary": "쉬운 말로 한 문장 요약"
  }},
  "chapter2": {{
    "title": "시작하기 전에",
    "concepts": [
      {{
        "name": "개념 이름",
        "explanation": "쉬운 1-2문장 설명",
        "analogy": "실생활 비유",
        "example": "def example(): pass",
        "use_cases": "주로 쓰이는 곳"
      }}
    ]
  }},
  "chapter3": {{
    "title": "코드 구조",
    "flowchart": "ASCII 또는 Mermaid 다이어그램 문자열",
    "file_breakdown": {{
      "main_section": "주요 코드 구조 설명",
      "components": [
        {{"name": "구성요소 이름", "purpose": "하는 일"}}
      ]
    }},
    "connections": "각 부분이 함께 작동하는 방식"
  }},
  "chapter4": {{
    "title": "줄별 설명",
    "explanations": [
      {{
        "lines": "1-3",
        "code": "실제 코드",
        "what_it_does": "간단한 설명",
        "syntax_breakdown": {{
          "키워드": "키워드 설명",
          "기호": "기호 설명"
        }},
        "analogy": "실생활 비유",
        "alternatives": "다른 작성 방법",
        "notes": "중요한 팁이나 주의사항"
      }}
    ]
  }},
  "chapter5": {{
    "title": "실행 과정",
    "steps": [
      {{
        "step_number": 1,
        "what_happens": "이 단계에서 일어나는 일",
        "current_values": {{"변수명": "현재 값"}},
        "why_it_matters": "이 단계의 목적"
      }}
    ]
  }},
  "chapter6": {{
    "title": "배운 핵심 개념",
    "concepts": [
      {{
        "name": "개념 이름",
        "what_it_is": "쉬운 정의",
        "why_used": "해결하는 문제",
        "where_applied": "실제 활용 사례",
        "in_this_code": "이 코드에서 어떻게 나타나는지"
      }}
    ]
  }},
  "chapter7": {{
    "title": "흔한 실수 피하기",
    "mistakes": [
      {{
        "mistake": "초보자가 자주 하는 잘못",
        "wrong_code": "틀린 코드 예시",
        "right_code": "수정된 버전",
        "why_it_matters": "결과",
        "how_to_fix": "수정 단계"
      }}
    ]
  }}
}}
```

중요:
- JSON 객체만 응답하고 추가 텍스트는 넣지 마세요
- 모든 JSON이 올바르게 이스케이프되었는지 확인하세요
- 설명은 간단하고 초보자 친화적으로 유지하세요
- 가능한 곳마다 실생활 비유를 포함하세요
- 모든 텍스트는 한국어로 작성하세요
"""

    def _format_folder_structure(self) -> str:
        """Format folder structure for multi-file uploads."""
        if not self.file_structure:
            return ""

        lines = ["## 파일 구조", ""]
        for file_path, info in self.file_structure.items():
            lines.append(f"- `{file_path}`: {info.get('description', '소스 파일')}")

        return "\n".join(lines)


@dataclass
class PracticePromptBuilder:
    """
    Builder for constructing AI prompts for practice problem generation.

    Attributes:
        code: The source code that was analyzed
        language: Programming language
        document_summary: Summary from the learning document (Chapter 1)
        concepts: List of concepts from the document (Chapter 2)
    """

    code: str
    language: str
    document_summary: str
    concepts: list[dict[str, str]]

    def get_system_instruction(self) -> str:
        """Get the system instruction for practice generation."""
        return SYSTEM_INSTRUCTION_PRACTICE

    def build_practice_prompt(self) -> str:
        """
        Build the complete prompt for practice problem generation.

        Returns:
            str: The formatted prompt for generating 5 practice problems
        """
        concepts_text = "\n".join([
            f"- {c.get('name', '알 수 없음')}: {c.get('explanation', '')}"
            for c in self.concepts
        ])

        return f"""이 코드와 학습 문서를 바탕으로 5개의 연습 문제를 생성하세요.

## 원본 코드
```{self.language.lower()}
{self.code}
```

## 문서 요약
{self.document_summary}

## 다룬 개념
{concepts_text}

## 작성 과제

난이도가 점점 올라가는 5개의 연습 문제를 만드세요:

1. **따라하기** (가장 쉬움): 학습자가 코드의 일부를 정확히 타이핑하게 하기
2. **빈칸 채우기**: 핵심 부분이 빈칸인 코드 제공하기
3. **코드 수정**: 코드를 약간 다르게 동작하도록 변경하게 하기
4. **디버그**: 1-2개의 의도적 버그가 있는 코드 제시하기
5. **새로 만들기** (가장 어려움): 배운 개념으로 새 코드 작성하게 하기

## 요구사항

각 문제에 대해:
- **problem_type**: [follow_along, fill_blanks, modify, debug, create] 중 하나
- **problem_statement**: 무엇을 해야 하는지 명확한 설명
- **learning_objective**: 이 문제가 테스트하는 기술
- **starter_code**: 시작 코드 (해당되는 경우)
- **hints**: 3개의 점진적 힌트 배열 (모호한 것 → 구체적인 것)
- **model_solution**: 완전한 해답 코드
- **expected_output**: 코드가 생성해야 할 결과
- **explanation**: 왜 이 해답이 맞는지 설명

## 출력 형식

유효한 JSON 객체로 응답하세요:

```json
{{
  "problems": [
    {{
      "problem_number": 1,
      "problem_type": "follow_along",
      "problem_statement": "다음 코드를 타이핑하세요...",
      "learning_objective": "...에 대한 근육 기억 형성",
      "starter_code": "",
      "hints": [
        "힌트 1: 모호한 힌트",
        "힌트 2: 조금 더 구체적",
        "힌트 3: 거의 답을 알려주는"
      ],
      "model_solution": "def example(): pass",
      "expected_output": "출력되거나 반환되어야 할 것",
      "explanation": "이것이 작동하는 이유..."
    }}
  ]
}}
```

중요:
- 문제는 반드시 문서의 개념만으로 풀 수 있어야 합니다
- 새로운 개념을 도입하지 마세요
- 난이도 진행을 부드럽게 유지하세요
- 힌트는 "더 열심히 해보세요"가 아니라 진짜 도움이 되게 하세요
- 모든 텍스트는 한국어로 작성하세요
"""


@dataclass
class QAPromptBuilder:
    """
    Builder for constructing AI prompts for Q&A responses.

    Attributes:
        question: The user's question
        code_context: Relevant code snippet (if user selected code)
        document_context: Relevant parts of the learning document
        conversation_history: Previous Q&A exchanges
        language: Programming language of the code
    """

    question: str
    code_context: str | None = None
    document_context: str | None = None
    conversation_history: list[dict[str, str]] | None = None
    language: str = "Unknown"

    def get_system_instruction(self) -> str:
        """Get the system instruction for Q&A responses."""
        return SYSTEM_INSTRUCTION_QA

    def build_qa_prompt(self) -> str:
        """
        Build the complete prompt for Q&A response generation.

        Returns:
            str: The formatted prompt for answering the question
        """
        # Build context sections
        code_section = ""
        if self.code_context:
            code_section = f"""
## 코드 맥락 (사용자가 선택한 코드)
```{self.language.lower()}
{self.code_context}
```
"""

        doc_section = ""
        if self.document_context:
            doc_section = f"""
## 관련 문서
{self.document_context}
"""

        history_section = ""
        if self.conversation_history:
            history_lines = []
            for entry in self.conversation_history[-5:]:  # Last 5 exchanges
                q = entry.get("question", "")
                a = entry.get("answer", "")
                history_lines.append(f"**이전 질문:** {q}")
                history_lines.append(f"**이전 답변:** {a}")
                history_lines.append("")
            history_section = f"""
## 대화 기록
{chr(10).join(history_lines)}
"""

        return f"""완전 초보자의 다음 질문에 답변하세요.
{code_section}
{doc_section}
{history_section}

## 질문
{self.question}

## 답변 작성

다음을 포함하는 초보자 친화적인 답변을 제공하세요:

1. **직접적인 답변** (1-2문장): 질문에 간단하고 직접적으로 답하기

2. **비유를 포함한 설명**: 실생활 비교를 사용해서 설명하기

3. **코드 예시** (관련 있는 경우): 간단한 코드 예시 보여주기

4. **관련 개념**: 더 알아보면 좋을 1-2개 관련 주제 제안하기

## 출력 형식

유효한 JSON 객체로 응답하세요:

```json
{{
  "direct_answer": "질문에 대한 간단하고 직접적인 답변",
  "explanation": "실생활 비유를 포함한 자세한 설명",
  "code_example": {{
    "code": "관련 있다면 예시 코드",
    "explanation": "코드가 보여주는 것"
  }},
  "related_concepts": [
    {{
      "concept": "관련 주제",
      "why_relevant": "왜 이것을 배우면 좋은지"
    }}
  ],
  "encouragement": "선택적인 격려 메시지"
}}
```

기억하세요:
- 사용자는 프로그래밍에 대해 아무것도 모릅니다
- 모든 것을 처음 듣는 것처럼 설명하세요
- 인내심을 갖고 격려하세요
- 질문이 불분명하면 최선의 해석으로 답변하세요
- 모든 텍스트는 한국어로 작성하세요
"""


# Template strings for specific use cases
DOCUMENT_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "chapter1": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "summary": {"type": "string"}
            },
            "required": ["title", "summary"]
        },
        "chapter2": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "concepts": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "explanation": {"type": "string"},
                            "analogy": {"type": "string"},
                            "example": {"type": "string"},
                            "use_cases": {"type": "string"}
                        },
                        "required": ["name", "explanation", "analogy"]
                    },
                    "maxItems": 5
                }
            },
            "required": ["title", "concepts"]
        },
        "chapter3": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "flowchart": {"type": "string"},
                "file_breakdown": {"type": "object"},
                "connections": {"type": "string"}
            },
            "required": ["title", "flowchart"]
        },
        "chapter4": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "explanations": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "lines": {"type": "string"},
                            "code": {"type": "string"},
                            "what_it_does": {"type": "string"},
                            "syntax_breakdown": {"type": "object"},
                            "analogy": {"type": "string"},
                            "alternatives": {"type": "string"},
                            "notes": {"type": "string"}
                        },
                        "required": ["lines", "code", "what_it_does"]
                    }
                }
            },
            "required": ["title", "explanations"]
        },
        "chapter5": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "steps": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "step_number": {"type": "integer"},
                            "what_happens": {"type": "string"},
                            "current_values": {"type": "object"},
                            "why_it_matters": {"type": "string"}
                        },
                        "required": ["step_number", "what_happens"]
                    }
                }
            },
            "required": ["title", "steps"]
        },
        "chapter6": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "concepts": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "what_it_is": {"type": "string"},
                            "why_used": {"type": "string"},
                            "where_applied": {"type": "string"},
                            "in_this_code": {"type": "string"}
                        },
                        "required": ["name", "what_it_is"]
                    }
                }
            },
            "required": ["title", "concepts"]
        },
        "chapter7": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "mistakes": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "mistake": {"type": "string"},
                            "wrong_code": {"type": "string"},
                            "right_code": {"type": "string"},
                            "why_it_matters": {"type": "string"},
                            "how_to_fix": {"type": "string"}
                        },
                        "required": ["mistake", "wrong_code", "right_code"]
                    },
                    "minItems": 3,
                    "maxItems": 5
                }
            },
            "required": ["title", "mistakes"]
        }
    },
    "required": [
        "chapter1", "chapter2", "chapter3", "chapter4",
        "chapter5", "chapter6", "chapter7"
    ]
}


def create_document_prompt(
    code: str,
    language: str,
    filename: str | None = None,
    additional_context: str | None = None,
    file_structure: dict[str, Any] | None = None
) -> tuple[str, str]:
    """
    Convenience function to create document generation prompt.

    Args:
        code: Source code to analyze
        language: Programming language
        filename: Optional filename for context
        additional_context: Optional extra context
        file_structure: Optional folder structure info

    Returns:
        Tuple of (system_instruction, prompt)
    """
    builder = PromptBuilder(
        code=code,
        language=language,
        filename=filename,
        additional_context=additional_context,
        file_structure=file_structure
    )
    return builder.get_system_instruction(), builder.build_document_prompt()


def create_practice_prompt(
    code: str,
    language: str,
    document_summary: str,
    concepts: list[dict[str, str]]
) -> tuple[str, str]:
    """
    Convenience function to create practice problem generation prompt.

    Args:
        code: Original source code
        language: Programming language
        document_summary: Chapter 1 summary from document
        concepts: List of concepts from Chapter 2

    Returns:
        Tuple of (system_instruction, prompt)
    """
    builder = PracticePromptBuilder(
        code=code,
        language=language,
        document_summary=document_summary,
        concepts=concepts
    )
    return builder.get_system_instruction(), builder.build_practice_prompt()


def create_qa_prompt(
    question: str,
    code_context: str | None = None,
    document_context: str | None = None,
    conversation_history: list[dict[str, str]] | None = None,
    language: str = "Unknown"
) -> tuple[str, str]:
    """
    Convenience function to create Q&A response prompt.

    Args:
        question: User's question
        code_context: Selected code snippet (if any)
        document_context: Relevant document sections
        conversation_history: Previous Q&A exchanges
        language: Programming language

    Returns:
        Tuple of (system_instruction, prompt)
    """
    builder = QAPromptBuilder(
        question=question,
        code_context=code_context,
        document_context=document_context,
        conversation_history=conversation_history,
        language=language
    )
    return builder.get_system_instruction(), builder.build_qa_prompt()
