import openai

openai.api_key = "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"

resp = openai.ChatCompletion.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Selam!"}]
)

print(resp.choices[0].message.content)
