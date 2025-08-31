@echo off
cd "C:\Users\dever\OneDrive\Área de Trabalho\ProTradingEngine"
call venv\Scripts\activate
python -m streamlit run dashboard/main_dashboard.py
pause