# Copy required files from main project
Copy-Item -Path "..\Nalanda_Chatbot\nandu_brain.py" -Destination ".\backend\" -Force
Copy-Item -Path "..\Nalanda_Chatbot\formatters.py" -Destination ".\backend\" -Force
Copy-Item -Path "..\Nalanda_Chatbot\catalogue.db" -Destination ".\backend\" -Force
Copy-Item -Path "..\Nalanda_Chatbot\general_queries.json" -Destination ".\backend\" -Force
Copy-Item -Path "..\Nalanda_Chatbot\general_queries_index.faiss" -Destination ".\backend\" -Force
Copy-Item -Path "..\Nalanda_Chatbot\general_queries_mapping.pkl" -Destination ".\backend\" -Force
Copy-Item -Path "..\Nalanda_Chatbot\catalogue_index.faiss" -Destination ".\backend\" -Force
Copy-Item -Path "..\Nalanda_Chatbot\catalogue_mapping.pkl" -Destination ".\backend\" -Force
Copy-Item -Path "..\Nalanda_Chatbot\models" -Destination ".\backend\" -Recurse -Force

Write-Host "Files copied successfully!" -ForegroundColor Green
