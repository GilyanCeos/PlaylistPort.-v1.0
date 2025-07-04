# Base oficial com Python
FROM python:3.11-slim

# Diretório de trabalho no container
WORKDIR /app

# Copia os arquivos para o container
COPY . .

# Instala dependências
RUN pip install --no-cache-dir -r requirements.txt

# Porta usada pelo Flask
EXPOSE 5000

# Executa a aplicação
CMD ["python", "app.py"]
