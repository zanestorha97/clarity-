import os, subprocess, sys
script = os.path.join(os.path.dirname(__file__), "app.py")
subprocess.run([sys.executable, "-m", "streamlit", "run", script, "--server.port=8501"])
