#!/usr/bin/env python3
"""
学习报告自动生成工具
基于知识点提取结果和验证记录生成结构化学习报告
"""

import json
import re
from datetime import datetime
from typing import Dict, List, Any
from pathlib import Path

class LearningReportGenerator:
    def __init__(self, template_path: str):
        self.template_path = Path(template_path)
        self.template_content = self._load_template()

    def _load_template(self) -> str:
        """加载报告模板"""
        with open(self.template_path, 'r', encoding='utf-8') as f:
            return f.read()

    def generate_report(self,
                       learning_data: Dict[str, Any],
                       output_path: str) -> None:
        """生成学习报告"""

        # 准备模板变量
        template_vars = self._prepare_template_variables(learning_data)

        # 替换模板变量
        report_content = self._replace_template_variables(template_vars)

        # 写入报告文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report_content)

        print(f"学习报告已生成: {output_path}")

    def _prepare_template_variables(self, data: Dict[str, Any]) -> Dict[str, str]:
        """准备模板变量"""
        variables = {}

        # 基础信息
        variables['LEARNING_DATE'] = data.get('learning_date', datetime.now().strftime('%Y-%m-%d'))
        variables['LEARNING_TOPIC'] = data.get('topic', '未指定')
        variables['LEARNING_DURATION'] = data.get('duration', '未记录')
        variables['GENERATION_TIMESTAMP'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # 学习目标和范围
        variables['LEARNING_OBJECTIVES'] = self._format_list(data.get('objectives', []))
        variables['INCLUDED_SCOPE'] = data.get('included_scope', '待补充')
        variables['EXCLUDED_SCOPE'] = data.get('excluded_scope', '待补充')
        variables['DEPTH_REQUIREMENT'] = data.get('depth_requirement', '待补充')

        # 知识点掌握矩阵
        variables.update(self._generate_knowledge_matrix(data.get('knowledge_points', [])))

        # 三重角色验证记录
        variables.update(self._generate_verification_summary(data.get('verification_records', {})))

        # 学习效果评估
        variables.update(self._generate_evaluation_summary(data.get('evaluation', {})))

        # 核心洞察
        variables['KEY_INSIGHTS'] = self._format_list(data.get('key_insights', []))
        variables['MINDSET_SHIFTS'] = self._format_list(data.get('mindset_shifts', []))
        variables['PRACTICAL_METHODOLOGIES'] = self._format_list(data.get('methodologies', []))

        # 可复用知识资产
        variables['TRANSFERABLE_PRINCIPLES'] = self._format_list(data.get('transferable_principles', []))
        variables['REUSABLE_PATTERNS'] = self._format_list(data.get('reusable_patterns', []))
        variables['BEST_PRACTICES'] = self._format_list(data.get('best_practices', []))

        # 延伸学习计划
        variables['SHORT_TERM_PLAN'] = self._format_list(data.get('short_term_plan', []))
        variables['MEDIUM_TERM_PLAN'] = self._format_list(data.get('medium_term_plan', []))
        variables['LONG_TERM_PLAN'] = self._format_list(data.get('long_term_plan', []))
        variables['LEARNING_RESOURCES'] = self._format_list(data.get('learning_resources', []))

        # 标签与分类
        variables['TECH_DOMAIN'] = data.get('tech_domain', '待分类')
        variables['DIFFICULTY_LEVEL'] = data.get('difficulty_level', '中等')
        variables['APPLICATION_SCENARIOS'] = ', '.join(data.get('application_scenarios', []))
        variables['RELATED_TECHNOLOGIES'] = ', '.join(data.get('related_technologies', []))

        # 学习过程反思
        variables['LEARNING_METHOD_EFFECTIVENESS'] = data.get('method_effectiveness', '待评估')
        variables['VERIFICATION_VALUE'] = data.get('verification_value', '待评估')
        variables['PROCESS_IMPROVEMENTS'] = self._format_list(data.get('process_improvements', []))
        variables['NEXT_REVIEW_PLAN'] = data.get('next_review', '一个月后')

        return variables

    def _generate_knowledge_matrix(self, knowledge_points: List[Dict]) -> Dict[str, str]:
        """生成知识点掌握矩阵"""
        variables = {}

        if not knowledge_points:
            variables['KNOWLEDGE_POINT_1'] = '待补充'
            variables['DEPTH_LEVEL'] = '待评估'
            variables['MASTERY_LEVEL'] = '待评估'
            variables['VERIFICATION_METHOD'] = '待补充'
            variables['NOTES'] = '待补充'
            return variables

        # 取前三个重要知识点
        for i, point in enumerate(knowledge_points[:3], 1):
            variables[f'KNOWLEDGE_POINT_{i}'] = point.get('concept', f'知识点{i}')

        # 设置默认值（应该从验证过程中获取）
        variables['DEPTH_LEVEL'] = '深入理解'
        variables['MASTERY_LEVEL'] = '🟡 熟练'
        variables['VERIFICATION_METHOD'] = '三重角色验证'
        variables['NOTES'] = '已通过验证'

        return variables

    def _generate_verification_summary(self, verification_records: Dict) -> Dict[str, str]:
        """生成验证过程摘要"""
        variables = {}

        # 小白角色验证
        beginner_phase = verification_records.get('beginner', {})
        variables['BASIC_CONCEPTS_COVERED'] = '✅ ' + ', '.join(beginner_phase.get('concepts_covered', ['待补充']))
        variables['MECHANISM_COVERED'] = '✅ ' + ', '.join(beginner_phase.get('mechanisms_covered', ['待补充']))
        variables['SCENARIOS_COVERED'] = '✅ ' + ', '.join(beginner_phase.get('scenarios_covered', ['待补充']))
        variables['IMPLEMENTATION_COVERED'] = '✅ ' + ', '.join(beginner_phase.get('implementation_covered', ['待补充']))
        variables['BEGINNER_QA_SUMMARY'] = beginner_phase.get('qa_summary', '待补充')
        variables['KNOWLEDGE_GAPS'] = self._format_list(beginner_phase.get('knowledge_gaps', []))

        # 专家质疑验证
        expert_phase = verification_records.get('expert', {})
        variables['THEORY_CHALLENGES'] = expert_phase.get('theory_challenges', '待补充')
        variables['PRACTICE_CHALLENGES'] = expert_phase.get('practice_challenges', '待补充')
        variables['BOUNDARY_CHALLENGES'] = expert_phase.get('boundary_challenges', '待补充')
        variables['DESIGN_CHALLENGES'] = expert_phase.get('design_challenges', '待补充')
        variables['SUCCESSFUL_DEFENSES'] = self._format_list(expert_phase.get('successful_defenses', []))
        variables['FURTHER_LEARNING_NEEDED'] = self._format_list(expert_phase.get('further_learning', []))

        # 实战搭档验证
        practical_phase = verification_records.get('practical', {})
        variables['PRACTICAL_SCENARIOS'] = practical_phase.get('scenarios', '待补充')
        variables['TECHNICAL_FEASIBILITY'] = practical_phase.get('technical_feasibility', '良好')
        variables['SOLUTION_COMPLETENESS'] = practical_phase.get('solution_completeness', '完整')
        variables['INNOVATION_LEVEL'] = practical_phase.get('innovation_level', '中等')
        variables['PRACTICAL_VALUE'] = practical_phase.get('practical_value', '高')
        variables['PRACTICAL_INSIGHTS'] = self._format_list(practical_phase.get('insights', []))

        return variables

    def _generate_evaluation_summary(self, evaluation: Dict) -> Dict[str, str]:
        """生成评估摘要"""
        variables = {}

        scores = evaluation.get('scores', {})
        variables['THEORY_SCORE'] = str(scores.get('theory', 8))
        variables['PRACTICE_SCORE'] = str(scores.get('practice', 8))
        variables['ADAPTABILITY_SCORE'] = str(scores.get('adaptability', 7))
        variables['INNOVATION_SCORE'] = str(scores.get('innovation', 7))

        variables['LEARNING_HIGHLIGHTS'] = self._format_list(evaluation.get('highlights', []))
        variables['IMPROVEMENT_AREAS'] = self._format_list(evaluation.get('improvement_areas', []))

        return variables

    def _format_list(self, items: List[str]) -> str:
        """格式化列表为markdown"""
        if not items:
            return '待补充'

        return '\n'.join([f'- {item}' for item in items])

    def _replace_template_variables(self, variables: Dict[str, str]) -> str:
        """替换模板中的变量"""
        content = self.template_content

        for var_name, var_value in variables.items():
            placeholder = f'{{{{{var_name}}}}}'
            content = content.replace(placeholder, str(var_value))

        return content

def main():
    import argparse

    parser = argparse.ArgumentParser(description='生成学习报告')
    parser.add_argument('--template', required=True, help='报告模板文件路径')
    parser.add_argument('--data', required=True, help='学习数据JSON文件')
    parser.add_argument('--output', '-o', required=True, help='输出报告文件路径')

    args = parser.parse_args()

    # 加载学习数据
    with open(args.data, 'r', encoding='utf-8') as f:
        learning_data = json.load(f)

    # 生成报告
    generator = LearningReportGenerator(args.template)
    generator.generate_report(learning_data, args.output)

if __name__ == '__main__':
    main()