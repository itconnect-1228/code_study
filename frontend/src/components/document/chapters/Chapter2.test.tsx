import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { Chapter2Prerequisites } from "./Chapter2";
import type { DocumentChapters } from "@/services/document-service";

describe("Chapter2Prerequisites", () => {
  const sampleChapter: DocumentChapters["prerequisites"] = {
    title: "사전 지식",
    concepts: [
      {
        name: "함수",
        explanation:
          "재사용 가능한 코드 블록입니다. 특정 작업을 수행하고 결과를 반환할 수 있습니다.",
        analogy:
          "레시피와 같습니다. 한 번 정의하면 여러 번 사용할 수 있습니다.",
      },
      {
        name: "변수",
        explanation:
          "데이터를 저장하는 컨테이너입니다. 값을 할당하고 나중에 참조할 수 있습니다.",
        analogy:
          "라벨이 붙은 상자와 같습니다. 상자에 물건을 넣고 라벨로 찾을 수 있습니다.",
      },
      {
        name: "console.log",
        explanation: "콘솔에 메시지를 출력하는 함수입니다.",
        analogy: "프로그램의 말하기 기능과 같습니다.",
      },
      {
        name: "문자열",
        explanation: "텍스트 데이터를 나타내는 자료형입니다.",
        analogy: "따옴표로 감싸진 글자들의 목걸이와 같습니다.",
      },
      {
        name: "함수 호출",
        explanation: "정의된 함수를 실행하는 것입니다.",
        analogy: "레시피를 보고 실제로 요리를 만드는 것과 같습니다.",
      },
    ],
  };

  describe("렌더링", () => {
    it("챕터 타이틀이 렌더링되어야 함", () => {
      render(<Chapter2Prerequisites data={sampleChapter} />);

      expect(
        screen.getByRole("heading", { name: /사전 지식/i }),
      ).toBeInTheDocument();
    });

    it("5개의 개념 카드가 렌더링되어야 함", () => {
      render(<Chapter2Prerequisites data={sampleChapter} />);

      expect(screen.getByText("함수")).toBeInTheDocument();
      expect(screen.getByText("변수")).toBeInTheDocument();
      expect(screen.getByText("console.log")).toBeInTheDocument();
      expect(screen.getByText("문자열")).toBeInTheDocument();
      expect(screen.getByText("함수 호출")).toBeInTheDocument();
    });

    it("각 개념 카드에 설명이 포함되어야 함", () => {
      render(<Chapter2Prerequisites data={sampleChapter} />);

      expect(screen.getByText(/재사용 가능한 코드 블록/)).toBeInTheDocument();
      expect(
        screen.getByText(/데이터를 저장하는 컨테이너/),
      ).toBeInTheDocument();
    });

    it("각 개념 카드에 비유가 포함되어야 함", () => {
      render(<Chapter2Prerequisites data={sampleChapter} />);

      expect(screen.getByText(/레시피와 같습니다/)).toBeInTheDocument();
      expect(screen.getByText(/라벨이 붙은 상자/)).toBeInTheDocument();
    });
  });

  describe("개념 카드 구조", () => {
    it("각 카드가 개별 article 요소로 렌더링되어야 함", () => {
      render(<Chapter2Prerequisites data={sampleChapter} />);

      const cards = screen.getAllByRole("article");
      expect(cards).toHaveLength(5);
    });

    it("비유 섹션이 시각적으로 구분되어야 함", () => {
      render(<Chapter2Prerequisites data={sampleChapter} />);

      // "비유:" 또는 관련 레이블이 있어야 함
      expect(screen.getAllByText(/비유/i).length).toBeGreaterThan(0);
    });
  });

  describe("스타일링", () => {
    it("컨테이너에 기본 클래스가 적용되어야 함", () => {
      const { container } = render(
        <Chapter2Prerequisites data={sampleChapter} />,
      );

      const chapter = container.firstChild;
      expect(chapter).toHaveClass("chapter-prerequisites");
    });

    it("커스텀 className을 적용할 수 있어야 함", () => {
      const { container } = render(
        <Chapter2Prerequisites data={sampleChapter} className="custom-class" />,
      );

      const chapter = container.firstChild;
      expect(chapter).toHaveClass("custom-class");
    });
  });

  describe("빈 개념 처리", () => {
    it("개념이 없을 때 적절한 메시지를 표시해야 함", () => {
      const emptyChapter = { ...sampleChapter, concepts: [] };
      render(<Chapter2Prerequisites data={emptyChapter} />);

      expect(screen.getByText(/사전 지식이 없습니다/i)).toBeInTheDocument();
    });
  });

  describe("접근성", () => {
    it("각 개념 카드가 접근 가능한 제목을 가져야 함", () => {
      render(<Chapter2Prerequisites data={sampleChapter} />);

      const headings = screen.getAllByRole("heading", { level: 3 });
      expect(headings.length).toBeGreaterThanOrEqual(5);
    });
  });
});
