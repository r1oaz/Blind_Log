import re
from datetime import datetime

version_file = "version.txt"

# Генерация новой версии
now = datetime.now()
new_version = f"1.0.{now.strftime('%Y%m%d%H%M%S')}"

# Чтение и обновление файла version.txt
with open(version_file, "r", encoding="utf-8") as file:
    content = file.read()

content = re.sub(
    r"filevers=\(.*?\)", f"filevers=({new_version.replace('.', ', ')}, 0)", content
)
content = re.sub(
    r"prodvers=\(.*?\)", f"prodvers=({new_version.replace('.', ', ')}, 0)", content
)
content = re.sub(
    r"StringStruct\('FileVersion', '.*?'\)",
    f"StringStruct('FileVersion', '{new_version}')",
    content,
)
content = re.sub(
    r"StringStruct\('ProductVersion', '.*?'\)",
    f"StringStruct('ProductVersion', '{new_version}')",
    content,
)

# Запись обновлённого файла
with open(version_file, "w", encoding="utf-8") as file:
    file.write(content)

print(f"Version updated to {new_version}")