import os
from openpyxl import load_workbook

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # config/

BACKEND_ROOT = os.path.abspath(os.path.join(BASE_DIR, ".."))  # back-end/
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, "../../../../.."))  # repo root

INTERFACE_MANAGER_CONFIG = os.path.abspath(
    os.path.join(BASE_DIR, "../../../interface_manager/config.json")
)

print(INTERFACE_MANAGER_CONFIG)
profile_path = os.path.expanduser("~/test_profile")

print(f"Determined INTERFACE_MANAGER_CONFIG path: {INTERFACE_MANAGER_CONFIG}")
TEMPLATE_PATH = os.path.join(BACKEND_ROOT, "templates", "Reports.xlsx")
print(f"Determined TEMPLATE_PATH: {TEMPLATE_PATH}")

wb = load_workbook(TEMPLATE_PATH)