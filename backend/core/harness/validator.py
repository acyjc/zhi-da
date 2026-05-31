# SchemaValidator — JSON 提取与校验、能力评分钳位、匹配度钳位
import json
import re


class SchemaValidator:
    # 从 LLM 原始输出中提取 JSON
    @staticmethod
    def extract_json(text: str) -> str:
        match = re.search(r'\{[\s\S]*\}', text)
        return match.group(0) if match else text

    # 将四维能力分值钳位到 0-100
    @staticmethod
    def validate_ability_scores(data: dict) -> dict:
        cleaned = {}
        for dim in ["tech_skills", "project_exp", "soft_skills", "domain_knowledge"]:
            if dim in data and isinstance(data[dim], dict):
                cleaned[dim] = {}
                for skill, score in data[dim].items():
                    try:
                        val = float(score)
                        cleaned[dim][skill] = max(0, min(100, val))
                    except (ValueError, TypeError):
                        cleaned[dim][skill] = 50
        return cleaned

    # 将匹配度钳位到 0-1
    @staticmethod
    def validate_match_score(score: float) -> float:
        return max(0.0, min(1.0, float(score)))

    # 解析 LLM 输出为 JSON，失败时尝试正则提取
    @staticmethod
    def validate_json_output(text: str, schema: dict = None) -> tuple[dict | None, str | None]:
        try:
            data = json.loads(text)
            return data, None
        except json.JSONDecodeError:
            try:
                extracted = SchemaValidator.extract_json(text)
                data = json.loads(extracted)
                return data, None
            except json.JSONDecodeError as e:
                return None, str(e)
