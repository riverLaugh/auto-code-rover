import openai
from openai import BaseModel
import os
# openai.base_url = "https://cluster1-qwen.cxpcn.site/v1/"
# openai.api_key = "sk-VrP154liNPBQ80JvAfA579Bc16E34bD7Ae6774A19cC6352e"

# response = openai.chat.completions.create(
#     model="qwen2.5:32b-instruct-fp8",
#     messages=[
#         {"role": "user", "content": "Hello! Who are you?"},
#     ],
#     temperature=0.7,
#     response_format={"type":"json_object"},
# )
# content = response.choices[0].message.content


# print(response)


class Step(BaseModel):
    explanation: str
    output: str

class MathReasoning(BaseModel):
    steps: list[Step]
    final_answer: str

client = openai.OpenAI(api_key="sk-VrP154liNPBQ80JvAfA579Bc16E34bD7Ae6774A19cC6352e", base_url="https://cluster1-qwen.cxpcn.site/v1/")

completion = client.beta.chat.completions.parse(
    model="qwen2.5:32b-instruct-fp8",
    messages=[
        {"role": "system", "content": "You are a helpful math tutor. Guide the user through the solution step by step."},
        {"role": "user", "content": "how can I solve 8x + 7 = -23"}
    ],
    response_format=MathReasoning,
)

math_reasoning = completion.choices[0].message

print(math_reasoning.tool_calls)
# print(math_reasoning.)
# If the model refuses to respond, you will get a refusal message
if (math_reasoning.refusal):
    print(math_reasoning.refusal)
else:
    print(math_reasoning.parsed)

answer = math_reasoning.content
print(answer)