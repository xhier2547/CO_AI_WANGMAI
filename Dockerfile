# =========================================================
# 🧱 BASE IMAGE
# =========================================================
FROM apache/airflow:2.7.3

# =========================================================
# 👤 Switch to root (for installing system deps)
# =========================================================
USER root

# ---------------------------------------------------------
# 🧩 System dependencies (YOLO / Streamlit / plotting)
# ---------------------------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    ffmpeg \
    libsm6 \
    libxext6 \
    libgl1 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# =========================================================
# 👤 Switch to airflow user (เพื่อติดตั้ง Python packages)
# =========================================================
USER airflow

# ---------------------------------------------------------
# 🧠 Python Libraries (Forecasting + Data Science)
# ---------------------------------------------------------
RUN pip install --no-cache-dir \
    pandas \
    numpy \
    matplotlib \
    seaborn \
    statsmodels \
    scikit-learn \
    tqdm \
    plotly \
    joblib \
    pmdarima \
    prophet \
    streamlit \
    ultralytics \
    line-bot-sdk \
    flask \
    psycopg2-binary \
    groq 

# =========================================================
# 📦 Environment Variables
# =========================================================
ENV PYTHONUNBUFFERED=1
ENV TZ=Asia/Bangkok

# =========================================================
# 📁 Default working directory
# =========================================================
WORKDIR /app

# =========================================================
# ✅ Copy project files
# =========================================================
COPY . /app
