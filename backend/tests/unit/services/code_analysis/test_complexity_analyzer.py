"""
Unit tests for the code complexity analyzer service.

Tests the complexity analysis functionality including:
- Line count analysis (total, code, comment, blank lines)
- Nesting depth detection
- Function and class counting
- Multi-language support (Python, JavaScript, TypeScript, Java, C/C++)
- Complexity level determination (beginner, intermediate, advanced)
"""

import pytest

from src.services.code_analysis.complexity_analyzer import (
    CodeComplexity,
    ComplexityLevel,
    analyze_complexity,
    count_lines,
    calculate_nesting_depth,
    count_functions,
    count_classes,
    determine_complexity_level,
)


class TestCodeComplexity:
    """Tests for the CodeComplexity dataclass."""

    def test_code_complexity_creation(self):
        """Should create a CodeComplexity instance with all fields."""
        complexity = CodeComplexity(
            total_lines=100,
            code_lines=80,
            comment_lines=10,
            blank_lines=10,
            max_nesting_depth=3,
            average_nesting_depth=1.5,
            function_count=5,
            class_count=2,
            complexity_level=ComplexityLevel.INTERMEDIATE,
        )

        assert complexity.total_lines == 100
        assert complexity.code_lines == 80
        assert complexity.comment_lines == 10
        assert complexity.blank_lines == 10
        assert complexity.max_nesting_depth == 3
        assert complexity.average_nesting_depth == 1.5
        assert complexity.function_count == 5
        assert complexity.class_count == 2
        assert complexity.complexity_level == ComplexityLevel.INTERMEDIATE

    def test_code_complexity_is_immutable(self):
        """CodeComplexity should be frozen (immutable)."""
        complexity = CodeComplexity(
            total_lines=100,
            code_lines=80,
            comment_lines=10,
            blank_lines=10,
            max_nesting_depth=3,
            average_nesting_depth=1.5,
            function_count=5,
            class_count=2,
            complexity_level=ComplexityLevel.BEGINNER,
        )

        with pytest.raises(Exception):  # FrozenInstanceError
            complexity.total_lines = 200


class TestComplexityLevel:
    """Tests for the ComplexityLevel enum."""

    def test_complexity_level_values(self):
        """Should have three levels: beginner, intermediate, advanced."""
        assert ComplexityLevel.BEGINNER.value == "beginner"
        assert ComplexityLevel.INTERMEDIATE.value == "intermediate"
        assert ComplexityLevel.ADVANCED.value == "advanced"


class TestCountLines:
    """Tests for line counting functionality."""

    def test_empty_content(self):
        """Should handle empty content."""
        result = count_lines("")

        assert result["total"] == 0
        assert result["code"] == 0
        assert result["comment"] == 0
        assert result["blank"] == 0

    def test_python_code_lines(self):
        """Should count lines in Python code."""
        code = '''# This is a comment
def hello():
    """Docstring"""
    print("Hello")

# Another comment
if __name__ == "__main__":
    hello()
'''
        result = count_lines(code, language="python")

        assert result["total"] == 9
        assert result["code"] > 0
        assert result["blank"] >= 1  # At least one blank line

    def test_javascript_code_lines(self):
        """Should count lines in JavaScript code."""
        code = '''// Comment
function greet() {
    /* Multi-line
       comment */
    console.log("Hello");
}

greet();
'''
        result = count_lines(code, language="javascript")

        assert result["total"] == 9
        assert result["code"] > 0
        assert result["comment"] > 0

    def test_blank_lines_only(self):
        """Should correctly count blank lines."""
        # Note: "\n\n\n" splits into 4 lines (3 newlines = 4 segments)
        code = "\n\n\n"

        result = count_lines(code)

        assert result["blank"] == 4  # Each newline creates a blank line segment
        assert result["code"] == 0

    def test_mixed_content(self):
        """Should correctly categorize mixed content."""
        code = """# Comment line

x = 1  # Inline comment
"""
        result = count_lines(code, language="python")

        assert result["total"] == 4  # including trailing newline
        assert result["blank"] >= 1


class TestCalculateNestingDepth:
    """Tests for nesting depth calculation."""

    def test_no_nesting(self):
        """Code without nesting should have depth 0."""
        code = """x = 1
y = 2
z = x + y
"""
        result = calculate_nesting_depth(code, language="python")

        assert result["max_depth"] == 0
        assert result["average_depth"] == 0.0

    def test_simple_nesting_python(self):
        """Should detect simple nesting in Python."""
        code = """def foo():
    if True:
        x = 1
"""
        result = calculate_nesting_depth(code, language="python")

        assert result["max_depth"] >= 2  # function + if

    def test_deep_nesting_python(self):
        """Should detect deep nesting in Python."""
        code = """def outer():
    if True:
        for i in range(10):
            if i > 5:
                while True:
                    x = 1
                    break
"""
        result = calculate_nesting_depth(code, language="python")

        assert result["max_depth"] >= 4  # Multiple nested levels

    def test_javascript_nesting(self):
        """Should detect nesting in JavaScript."""
        code = """function outer() {
    if (true) {
        for (let i = 0; i < 10; i++) {
            console.log(i);
        }
    }
}
"""
        result = calculate_nesting_depth(code, language="javascript")

        assert result["max_depth"] >= 3

    def test_empty_content(self):
        """Should handle empty content."""
        result = calculate_nesting_depth("", language="python")

        assert result["max_depth"] == 0
        assert result["average_depth"] == 0.0


class TestCountFunctions:
    """Tests for function counting."""

    def test_no_functions(self):
        """Should return 0 when no functions."""
        code = """x = 1
y = 2
"""
        result = count_functions(code, language="python")

        assert result == 0

    def test_python_functions(self):
        """Should count Python functions."""
        code = """def foo():
    pass

def bar():
    pass

async def baz():
    pass
"""
        result = count_functions(code, language="python")

        assert result == 3

    def test_python_methods_in_class(self):
        """Should count methods in Python classes."""
        code = """class MyClass:
    def __init__(self):
        pass

    def method(self):
        pass

    @staticmethod
    def static_method():
        pass
"""
        result = count_functions(code, language="python")

        assert result == 3  # __init__, method, static_method

    def test_javascript_functions(self):
        """Should count JavaScript functions."""
        code = """function foo() {}

const bar = function() {};

const baz = () => {};

async function asyncFunc() {}
"""
        result = count_functions(code, language="javascript")

        assert result >= 3  # At least 3 functions

    def test_typescript_functions(self):
        """Should count TypeScript functions."""
        code = """function greet(name: string): void {
    console.log(name);
}

const add = (a: number, b: number): number => a + b;
"""
        result = count_functions(code, language="typescript")

        assert result >= 2


class TestCountClasses:
    """Tests for class counting."""

    def test_no_classes(self):
        """Should return 0 when no classes."""
        code = """def foo():
    pass
"""
        result = count_classes(code, language="python")

        assert result == 0

    def test_python_classes(self):
        """Should count Python classes."""
        code = """class Foo:
    pass

class Bar:
    pass
"""
        result = count_classes(code, language="python")

        assert result == 2

    def test_javascript_classes(self):
        """Should count JavaScript classes."""
        code = """class Animal {
    constructor(name) {
        this.name = name;
    }
}

class Dog extends Animal {
    bark() {
        console.log("Woof!");
    }
}
"""
        result = count_classes(code, language="javascript")

        assert result == 2

    def test_typescript_classes(self):
        """Should count TypeScript classes."""
        code = """class Person {
    name: string;

    constructor(name: string) {
        this.name = name;
    }
}

interface IPerson {
    name: string;
}
"""
        result = count_classes(code, language="typescript")

        # Should count classes, interfaces are not classes
        assert result >= 1


class TestDetermineComplexityLevel:
    """Tests for complexity level determination."""

    def test_beginner_level(self):
        """Simple code should be beginner level."""
        # Simple code: few lines, low nesting, few functions
        result = determine_complexity_level(
            total_lines=20,
            max_nesting_depth=1,
            function_count=2,
            class_count=0,
        )

        assert result == ComplexityLevel.BEGINNER

    def test_intermediate_level(self):
        """Moderately complex code should be intermediate level."""
        result = determine_complexity_level(
            total_lines=100,
            max_nesting_depth=3,
            function_count=8,
            class_count=2,
        )

        assert result == ComplexityLevel.INTERMEDIATE

    def test_advanced_level(self):
        """Complex code should be advanced level."""
        result = determine_complexity_level(
            total_lines=500,
            max_nesting_depth=6,
            function_count=30,
            class_count=10,
        )

        assert result == ComplexityLevel.ADVANCED

    def test_deep_nesting_triggers_advanced(self):
        """Deep nesting should increase complexity level."""
        result = determine_complexity_level(
            total_lines=50,
            max_nesting_depth=7,  # Very deep nesting
            function_count=3,
            class_count=0,
        )

        # Deep nesting should bump up complexity
        assert result in [ComplexityLevel.INTERMEDIATE, ComplexityLevel.ADVANCED]


class TestAnalyzeComplexity:
    """Tests for the main analyze_complexity function."""

    def test_simple_python_code(self):
        """Should analyze simple Python code."""
        code = '''def hello():
    print("Hello, World!")

hello()
'''
        result = analyze_complexity(code, language="python")

        assert isinstance(result, CodeComplexity)
        assert result.total_lines >= 4
        assert result.function_count == 1
        assert result.class_count == 0
        assert result.complexity_level == ComplexityLevel.BEGINNER

    def test_intermediate_python_code(self):
        """Should analyze intermediate complexity Python code."""
        code = '''class Calculator:
    """A simple calculator class."""

    def __init__(self):
        self.result = 0

    def add(self, x, y):
        return x + y

    def subtract(self, x, y):
        return x - y

    def calculate(self, operation, x, y):
        if operation == "add":
            return self.add(x, y)
        elif operation == "subtract":
            return self.subtract(x, y)
        else:
            raise ValueError("Unknown operation")

def main():
    calc = Calculator()
    print(calc.calculate("add", 5, 3))

if __name__ == "__main__":
    main()
'''
        result = analyze_complexity(code, language="python")

        assert result.function_count >= 4
        assert result.class_count == 1
        assert result.max_nesting_depth >= 1

    def test_javascript_code(self):
        """Should analyze JavaScript code."""
        code = '''function greet(name) {
    if (name) {
        console.log("Hello, " + name);
    } else {
        console.log("Hello, World!");
    }
}

class Person {
    constructor(name) {
        this.name = name;
    }

    greet() {
        greet(this.name);
    }
}
'''
        result = analyze_complexity(code, language="javascript")

        assert result.total_lines > 0
        assert result.function_count >= 1
        assert result.class_count >= 1

    def test_empty_code(self):
        """Should handle empty code."""
        result = analyze_complexity("", language="python")

        assert result.total_lines == 0
        assert result.code_lines == 0
        assert result.function_count == 0
        assert result.class_count == 0
        assert result.complexity_level == ComplexityLevel.BEGINNER

    def test_default_language(self):
        """Should work without explicit language."""
        code = """x = 1
y = 2
print(x + y)
"""
        result = analyze_complexity(code)

        assert result.total_lines >= 3
        assert result.complexity_level == ComplexityLevel.BEGINNER

    def test_java_code(self):
        """Should analyze Java code."""
        code = '''public class HelloWorld {
    public static void main(String[] args) {
        System.out.println("Hello, World!");
    }

    public int add(int a, int b) {
        return a + b;
    }
}
'''
        result = analyze_complexity(code, language="java")

        assert result.class_count >= 1
        assert result.function_count >= 1

    def test_complex_code_detection(self):
        """Should detect complex code patterns."""
        # Deeply nested, many functions
        code = '''def level1():
    def level2():
        def level3():
            if True:
                for i in range(10):
                    if i > 5:
                        while True:
                            break

def func1(): pass
def func2(): pass
def func3(): pass
def func4(): pass
def func5(): pass
def func6(): pass
def func7(): pass
def func8(): pass
def func9(): pass
def func10(): pass

class A: pass
class B: pass
class C: pass
'''
        result = analyze_complexity(code, language="python")

        assert result.function_count >= 10
        assert result.class_count >= 3
        # Deep nesting should push this to intermediate or advanced
        assert result.complexity_level in [
            ComplexityLevel.INTERMEDIATE,
            ComplexityLevel.ADVANCED,
        ]


class TestIntegration:
    """Integration tests for complexity analyzer."""

    def test_real_world_python_file(self):
        """Should analyze a realistic Python file."""
        code = '''#!/usr/bin/env python3
"""
A module for handling user authentication.
"""

import hashlib
import secrets
from typing import Optional

class AuthenticationError(Exception):
    """Raised when authentication fails."""
    pass

class User:
    """Represents a user in the system."""

    def __init__(self, username: str, email: str):
        self.username = username
        self.email = email
        self._password_hash: Optional[str] = None

    def set_password(self, password: str) -> None:
        """Hash and store the password."""
        salt = secrets.token_hex(16)
        hash_input = f"{salt}:{password}".encode()
        self._password_hash = f"{salt}:{hashlib.sha256(hash_input).hexdigest()}"

    def verify_password(self, password: str) -> bool:
        """Verify a password against the stored hash."""
        if not self._password_hash:
            return False

        try:
            salt, stored_hash = self._password_hash.split(":")
            hash_input = f"{salt}:{password}".encode()
            computed_hash = hashlib.sha256(hash_input).hexdigest()
            return secrets.compare_digest(computed_hash, stored_hash)
        except ValueError:
            return False

def authenticate(username: str, password: str, users: dict) -> User:
    """Authenticate a user by username and password."""
    if username not in users:
        raise AuthenticationError("User not found")

    user = users[username]
    if not user.verify_password(password):
        raise AuthenticationError("Invalid password")

    return user
'''
        result = analyze_complexity(code, language="python")

        assert result.total_lines > 40
        assert result.function_count >= 4  # set_password, verify_password, authenticate, __init__
        assert result.class_count >= 2  # AuthenticationError, User
        assert result.complexity_level in [
            ComplexityLevel.BEGINNER,
            ComplexityLevel.INTERMEDIATE,
        ]

    def test_typescript_react_component(self):
        """Should analyze a TypeScript React component."""
        code = '''import React, { useState, useEffect } from 'react';

interface Props {
    title: string;
    items: string[];
}

const ItemList: React.FC<Props> = ({ title, items }) => {
    const [filter, setFilter] = useState('');
    const [filteredItems, setFilteredItems] = useState(items);

    useEffect(() => {
        const filtered = items.filter(item =>
            item.toLowerCase().includes(filter.toLowerCase())
        );
        setFilteredItems(filtered);
    }, [items, filter]);

    const handleFilterChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setFilter(e.target.value);
    };

    return (
        <div className="item-list">
            <h2>{title}</h2>
            <input
                type="text"
                value={filter}
                onChange={handleFilterChange}
                placeholder="Filter items..."
            />
            <ul>
                {filteredItems.map((item, index) => (
                    <li key={index}>{item}</li>
                ))}
            </ul>
        </div>
    );
};

export default ItemList;
'''
        result = analyze_complexity(code, language="typescript")

        assert result.total_lines > 30
        # TSX/React components may have various function patterns
        assert result.function_count >= 1
