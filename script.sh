curl -x "3.6.141.226:8080 https://api.openai.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer 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" \
  -d '{
     "model": "gpt-3.5-turbo",
     "messages": [{"role": "user", "content": "Say this is a test!"}],
     "temperature": 0.7
   }'

