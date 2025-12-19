import subprocess



result = subprocess.run(
    ["gcloud", 'auth', 'print-identity-token'],
    capture_output=True,
    text=True
)
print("🔑 Getting authentication token...", result)