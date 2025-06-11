import json
import re
import streamlit as st
from deepdiff import DeepDiff
from demjson3 import decode as demjson_decode, JSONDecodeError as DemjsonDecodeError


# 将 DSL 风格的配置格式转换为 JSON 格式
def convert_dsl_to_json(text: str) -> str:
    # 处理 key value → "key": "value"
    text = re.sub(r'(\w+)\s+({)', r'"\1": {', text)  # USDCNY { → "USDCNY": {
    text = re.sub(r'(\w+)\s+(\w+)', r'"\1": "\2"', text)  # enabled true → "enabled": "true"
    text = re.sub(r'"(true|false|null|\d+[a-zA-Z]*)"', r'\1', text)  # 去掉布尔值或数字后缀的引号
    text = re.sub(r',\s*}', '}', text)  # 去掉 } 前的逗号
    text = re.sub(r',\s*]', ']', text)  # 去掉 ] 前的逗号
    text = '{' + text.strip() + '}'
    return text


# 尝试解析 JSON 或自动修复
def smart_parse_json(text: str):
    try:
        return json.loads(text), "✅ 使用标准 JSON 成功解析"
    except json.JSONDecodeError:
        try:
            # 尝试将 DSL 格式转成 JSON
            converted = convert_dsl_to_json(text)
            try:
                obj = json.loads(converted)
                return obj, "⚠️ 检测到非标准格式，已自动转换为 JSON"
            except json.JSONDecodeError:
                # 尝试用 demjson3 宽容解析
                obj = demjson_decode(text)
                return obj, "⚠️ 标准解析失败，但已用 demjson3 成功修复"
        except (DemjsonDecodeError, Exception) as e:
            return None, f"❌ 无法修复 JSON：{e}"


# 递归排序
def sort_json(obj):
    if isinstance(obj, dict):
        return {k: sort_json(obj[k]) for k in sorted(obj)}
    elif isinstance(obj, list):
        return [sort_json(item) for item in obj]
    else:
        return obj


# Streamlit 页面布局
st.set_page_config(page_title="JSON 对比工具（支持 DSL 修复）", layout="wide")
st.title("🧪 JSON 差异对比工具（支持非标准 DSL 格式修复）")

col1, col2 = st.columns(2)
with col1:
    input_json1 = st.text_area("输入 JSON / DSL 1", height=300, placeholder="支持非标准 DSL，如 USDCNY { ... }")
with col2:
    input_json2 = st.text_area("输入 JSON / DSL 2", height=300)

if st.button("🔍 开始比较"):
    with st.spinner("正在解析和比较..."):

        json1, msg1 = smart_parse_json(input_json1)
        json2, msg2 = smart_parse_json(input_json2)

        if msg1:
            st.info(f"JSON 1：{msg1}")
        if msg2:
            st.info(f"JSON 2：{msg2}")

        if json1 is None or json2 is None:
            st.error("❌ 无法完成解析，请检查输入格式。")
        else:
            sorted1 = sort_json(json1)
            sorted2 = sort_json(json2)

            st.subheader("📋 整理并排序后的 JSON 1")
            st.json(sorted1)

            st.subheader("📋 整理并排序后的 JSON 2")
            st.json(sorted2)

            st.subheader("📌 差异比对结果")
            diff = DeepDiff(sorted1, sorted2, ignore_order=True)

            if diff:
                st.code(json.dumps(diff, indent=2, ensure_ascii=False, default=str))
            else:
                st.success("🎉 两个 JSON 完全一致（字段顺序已忽略）")
