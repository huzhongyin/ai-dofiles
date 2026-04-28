#!/usr/bin/env python3
"""
学习知识点提取工具
从对话记录中自动提取和分类核心知识点
"""

import re
import json
from typing import List, Dict, Set
from dataclasses import dataclass, asdict
from collections import defaultdict

@dataclass
class KnowledgePoint:
    concept: str
    category: str
    description: str
    examples: List[str]
    confidence: float
    mentioned_count: int

class KnowledgeExtractor:
    def __init__(self):
        self.technical_patterns = [
            # 概念定义模式
            r'(\w+)是(.{10,100})',
            r'什么是(\w+)',
            r'(\w+)的定义',

            # 工作原理模式
            r'(\w+)如何工作',
            r'(\w+)的工作原理',
            r'(\w+)的机制',

            # 特征描述模式
            r'(\w+)具有(.{5,50})特点',
            r'(\w+)的优点是(.{10,100})',
            r'(\w+)的缺点是(.{10,100})',

            # 应用场景模式
            r'使用(\w+)来(.{5,50})',
            r'(\w+)适用于(.{5,50})',
            r'什么时候用(\w+)',
        ]

        self.category_keywords = {
            'architecture': ['架构', '设计', '模式', '结构', '组件'],
            'implementation': ['实现', '代码', '编程', '开发', '脚本'],
            'process': ['流程', '步骤', '方法', '过程', 'workflow'],
            'concept': ['概念', '原理', '理论', '定义', '本质'],
            'tool': ['工具', '框架', 'skill', 'agent', '技术'],
            'practice': ['实践', '应用', '场景', '案例', '经验']
        }

    def extract_knowledge_points(self, conversation_text: str,
                                learning_topic: str) -> List[KnowledgePoint]:
        """从对话文本中提取知识点"""
        knowledge_points = []
        mentioned_concepts = defaultdict(int)

        # 预处理：移除特殊字符，分句
        sentences = self._preprocess_text(conversation_text)

        for sentence in sentences:
            # 跳过太短的句子
            if len(sentence) < 10:
                continue

            # 提取概念
            concepts = self._extract_concepts_from_sentence(sentence, learning_topic)

            for concept, description, examples in concepts:
                mentioned_concepts[concept] += 1

                # 分类
                category = self._categorize_concept(sentence, concept)

                # 计算置信度
                confidence = self._calculate_confidence(sentence, concept, learning_topic)

                knowledge_points.append(KnowledgePoint(
                    concept=concept,
                    category=category,
                    description=description,
                    examples=examples,
                    confidence=confidence,
                    mentioned_count=mentioned_concepts[concept]
                ))

        # 去重和合并相似概念
        knowledge_points = self._deduplicate_and_merge(knowledge_points)

        # 按重要性排序
        knowledge_points.sort(key=lambda x: (x.confidence * x.mentioned_count), reverse=True)

        return knowledge_points

    def _preprocess_text(self, text: str) -> List[str]:
        """文本预处理"""
        # 移除特殊字符
        text = re.sub(r'[^\u4e00-\u9fff\w\s\.\?\!]', ' ', text)

        # 分句
        sentences = re.split(r'[。？！\.\?\!]', text)

        return [s.strip() for s in sentences if s.strip()]

    def _extract_concepts_from_sentence(self, sentence: str, topic: str) -> List[tuple]:
        """从单句中提取概念"""
        concepts = []

        for pattern in self.technical_patterns:
            matches = re.finditer(pattern, sentence, re.IGNORECASE)
            for match in matches:
                if len(match.groups()) >= 2:
                    concept = match.group(1).strip()
                    description = match.group(2).strip() if len(match.groups()) > 1 else ""

                    # 过滤噪音
                    if self._is_valid_concept(concept, topic):
                        examples = self._extract_examples_for_concept(sentence, concept)
                        concepts.append((concept, description, examples))

        return concepts

    def _is_valid_concept(self, concept: str, topic: str) -> bool:
        """验证概念的有效性"""
        # 长度检查
        if len(concept) < 2 or len(concept) > 30:
            return False

        # 是否与主题相关
        topic_keywords = topic.lower().split()
        if not any(keyword in concept.lower() for keyword in topic_keywords):
            # 检查是否是技术相关术语
            tech_indicators = ['技术', '方法', '模式', '架构', 'skill', 'agent', '工具']
            if not any(indicator in concept.lower() for indicator in tech_indicators):
                return False

        return True

    def _categorize_concept(self, sentence: str, concept: str) -> str:
        """概念分类"""
        sentence_lower = sentence.lower()

        for category, keywords in self.category_keywords.items():
            if any(keyword in sentence_lower for keyword in keywords):
                return category

        return 'general'

    def _calculate_confidence(self, sentence: str, concept: str, topic: str) -> float:
        """计算概念提取的置信度"""
        confidence = 0.5  # 基础置信度

        # 主题相关性
        if topic.lower() in concept.lower():
            confidence += 0.3

        # 句子质量
        if len(sentence) > 20:
            confidence += 0.1

        # 是否有明确定义
        if any(indicator in sentence for indicator in ['是', '定义为', '指的是']):
            confidence += 0.1

        return min(confidence, 1.0)

    def _extract_examples_for_concept(self, sentence: str, concept: str) -> List[str]:
        """为概念提取例子"""
        examples = []

        # 寻找例子模式
        example_patterns = [
            rf'{concept}.*?例如(.{{5,50}})',
            rf'{concept}.*?比如(.{{5,50}})',
            rf'例子.*{concept}.*?(.{{10,50}})'
        ]

        for pattern in example_patterns:
            matches = re.finditer(pattern, sentence, re.IGNORECASE)
            for match in matches:
                example = match.group(1).strip()
                if example:
                    examples.append(example)

        return examples

    def _deduplicate_and_merge(self, knowledge_points: List[KnowledgePoint]) -> List[KnowledgePoint]:
        """去重和合并相似概念"""
        unique_points = {}

        for point in knowledge_points:
            key = point.concept.lower()

            if key in unique_points:
                # 合并信息
                existing = unique_points[key]
                existing.mentioned_count += point.mentioned_count
                existing.confidence = max(existing.confidence, point.confidence)
                existing.examples.extend(point.examples)
                existing.examples = list(set(existing.examples))  # 去重

                # 取更详细的描述
                if len(point.description) > len(existing.description):
                    existing.description = point.description
            else:
                unique_points[key] = point

        return list(unique_points.values())

    def export_to_json(self, knowledge_points: List[KnowledgePoint],
                      filename: str) -> None:
        """导出为JSON格式"""
        data = {
            'knowledge_points': [asdict(point) for point in knowledge_points],
            'summary': {
                'total_concepts': len(knowledge_points),
                'categories': list(set(point.category for point in knowledge_points)),
                'high_confidence': len([p for p in knowledge_points if p.confidence > 0.8])
            }
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

def main():
    import argparse

    parser = argparse.ArgumentParser(description='从对话中提取知识点')
    parser.add_argument('conversation_file', help='对话记录文件')
    parser.add_argument('--topic', required=True, help='学习主题')
    parser.add_argument('--output', '-o', help='输出文件路径')
    parser.add_argument('--format', choices=['json', 'markdown'],
                       default='json', help='输出格式')

    args = parser.parse_args()

    # 读取对话文件
    with open(args.conversation_file, 'r', encoding='utf-8') as f:
        conversation_text = f.read()

    # 提取知识点
    extractor = KnowledgeExtractor()
    knowledge_points = extractor.extract_knowledge_points(conversation_text, args.topic)

    # 输出结果
    if args.format == 'json':
        output_file = args.output or f'{args.topic}_knowledge_points.json'
        extractor.export_to_json(knowledge_points, output_file)
        print(f"知识点已导出到: {output_file}")

    elif args.format == 'markdown':
        output_file = args.output or f'{args.topic}_knowledge_points.md'
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"# {args.topic} 学习知识点\n\n")

            for point in knowledge_points:
                f.write(f"## {point.concept}\n")
                f.write(f"**分类**: {point.category}\n")
                f.write(f"**描述**: {point.description}\n")
                f.write(f"**置信度**: {point.confidence:.1%}\n")
                f.write(f"**提及次数**: {point.mentioned_count}\n")

                if point.examples:
                    f.write("**例子**:\n")
                    for example in point.examples:
                        f.write(f"- {example}\n")
                f.write("\n")

        print(f"知识点已导出到: {output_file}")

    # 打印摘要
    print(f"\n提取摘要:")
    print(f"总概念数: {len(knowledge_points)}")
    print(f"高置信度概念: {len([p for p in knowledge_points if p.confidence > 0.8])}")
    print(f"涉及分类: {set(point.category for point in knowledge_points)}")

if __name__ == '__main__':
    main()